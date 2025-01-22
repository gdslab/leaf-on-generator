import os
import uuid
from typing import Any, Dict, List, Optional, Union

import numpy as np
import rasterio
from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from geojson_pydantic import Feature, Polygon
from pydantic import AnyHttpUrl
from pystac_client import Client
from starlette.middleware.sessions import SessionMiddleware

from app.ml.lidar.main4api import your_main_model_function as lidar_model
from app.ml.lidar_and_naip.main4api_unet import (
    your_main_model_function2 as lidar_and_naip_model,
)
from app.schemas.datasets import (
    DatasetsResponse,
    LidarDatasetItem,
    ModelResponse,
    NaipDatasetItem,
)
from app.utils import generate_secret_key

app = FastAPI(title="Leaf-on Generator")


app.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", generate_secret_key())
)

app.mount("/static", StaticFiles(directory="/static"), name="static")


@app.get("/")
def read_root(request: Request) -> Any:
    print(request)
    return {"Hello": "World"}


@app.post("/api/datasets", response_model=DatasetsResponse)
def find_datasets_in_aoi(aoi: Feature[Polygon, Dict]) -> Any:
    # Check for required geometry
    if not aoi.geometry or aoi.geometry.type.lower() != "polygon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AOI must include polygon geometry",
        )

    # Get bounding box from polygon coordinates
    boundary_arr = np.array(aoi.geometry.coordinates[0])
    bounding_box = [
        boundary_arr[:, 0].min(),
        boundary_arr[:, 1].min(),
        boundary_arr[:, 0].max(),
        boundary_arr[:, 1].max(),
    ]

    # Connect to STAC API
    client = Client.open("https://stac-api.d2s.org")

    print(f"bounding_box: {bounding_box}")

    # Search 3DEP collection
    search_3dep = client.search(max_items=10, collections=["3dep"], bbox=bounding_box)

    # Search NAIP collection
    search_naip = client.search(max_items=10, collections=["naip"], bbox=bounding_box)

    # Get href for search results
    base_url_3dep = "https://stac.d2s.org/collections/3dep/items"
    base_url_naip = "https://stac.d2s.org/collections/3dep/items"

    # Create payload with dataset IDs and URLs
    payload = DatasetsResponse(
        point_cloud=[
            {
                "id": item.id,
                "bbox": item.bbox,
                "epsg": item.properties.get("proj:epsg") or -1,
                "href": item.assets["ept.json"].href,
            }
            for item in search_3dep.items()
        ],
        raster=[
            {
                "id": item.id,
                "bbox": item.bbox,
                "epsg": item.properties.get("proj:epsg") or -1,
                "gsd": item.properties.get("gsd") or -1,
                "href": item.assets["image"].href,
            }
            for item in search_naip.items()
        ],
    )

    return payload


@app.post("/api/model", response_model=ModelResponse)
def run_3dep_model(
    aoi: Feature[Polygon, Dict],
    lidar: LidarDatasetItem,
    model: str = Body(default="lidar"),
    naip: Optional[NaipDatasetItem] = None,
) -> Any:
    # Create session ID
    session_id = str(uuid.uuid4())

    # Create folder in static directory for session
    session_dir = os.path.join("/static", session_id)
    if not os.path.isdir(session_dir):
        os.makedirs(session_dir)

    # Check for required geometry
    if not aoi.geometry or aoi.geometry.type.lower() != "polygon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AOI must include polygon geometry",
        )

    # Get bounding box from polygon coordinates
    boundary_arr = np.array(aoi.geometry.coordinates[0])
    bounding_box = [
        boundary_arr[:, 0].min(),
        boundary_arr[:, 1].min(),
        boundary_arr[:, 0].max(),
        boundary_arr[:, 1].max(),
    ]
    # Get EPT ID, URL, and EPSG
    ept_id = lidar.id
    ept_url = str(lidar.href)
    ept_epsg = lidar.epsg

    # Get NAIP properties if Lidar + Spectral selected
    if model == "both" and naip:
        naip_id = naip.id
        naip_url = str(naip.href)
        naip_epsg = naip.epsg
        naip_gsd = naip.gsd

    model_path = os.path.join("/app", "app", "ml", "test_oct2_.h5")

    # Run model here
    if model == "lidar":
        print("Running lidar_model...")
        ndhm_path, chm_path = lidar_model(
            bounding_box, session_dir, ept_id, ept_url, ept_epsg, model_path
        )
        naip_path = None
    elif model == "both":
        print("Running lidar_and_naip_model...")
        chm_path, ndhm_path, naip_path = lidar_and_naip_model(
            bounding_box,
            session_dir,
            ept_id,
            ept_url,
            ept_epsg,
            naip_id,
            naip_url,
            naip_epsg,
            # naip_gsd,
            model_path,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected model must be 'lidar' or 'both'",
        )

    # Get rescale values for chm
    with rasterio.open(chm_path) as src:
        band1 = src.read(1)
        chm_min_value = band1.min()
        chm_max_value = band1.max()

    print(f"model: {model}")
    print(f"naip_path: {naip_path}")

    # Prepare naip payload if available
    if model == "both" and naip_path:
        naip_payload = {
            "href": naip_path,
            "rescale": f"{chm_min_value},{chm_max_value}",
        }
    else:
        naip_payload = None

    # Create response with URL for CHM and session ID
    payload = ModelResponse(
        chm={
            "href": chm_path,
            "rescale": f"{chm_min_value},{chm_max_value}",
        },
        ndhm={
            "href": ndhm_path,
            "rescale": f"{chm_min_value},{chm_max_value}",
        },
        naip=naip_payload,
        session_id=session_id,
    )
    response = JSONResponse(content=payload.model_dump())
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    return response
