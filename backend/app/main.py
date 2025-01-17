import os
import uuid
from typing import Any, Dict, List, Optional, Union

import numpy as np
import rasterio
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from geojson_pydantic import Feature, Polygon
from pydantic import AnyHttpUrl
from pystac_client import Client
from starlette.middleware.sessions import SessionMiddleware

from app.leaf_on_generator.main4api import your_main_model_function
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
def read_root(request: Request):
    print(request)
    return {"Hello": "World"}


@app.post("/api/datasets")
def find_datasets_in_aoi(aoi: Feature[Polygon, Dict]) -> DatasetsResponse:
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
    payload = {
        "point_cloud": [
            {
                "id": item.id,
                "href": item.assets["ept.json"].href,
                "bbox": item.bbox,
                "epsg": item.properties.get("proj:epsg"),
            }
            for item in search_3dep.items()
        ],
        "raster": [
            {
                "id": item.id,
                "href": item.assets["image"].href,
                "bbox": item.bbox,
                "epsg": item.properties.get("proj:epsg"),
                "gsd": item.properties.get("gsd"),
            }
            for item in search_naip.items()
        ],
    }

    return payload


@app.post("/api/model")
def run_3dep_model(
    aoi: Feature[Polygon, Dict],
    lidar: LidarDatasetItem,
    model: str = "lidar",
    naip: Optional[NaipDatasetItem] = None,
) -> ModelResponse:
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
        naip_url = naip.url
        naip_epsg = naip.epsg
        naip_gsd = naip.gsd

    model_path = os.path.join("/app", "app", "leaf_on_generator", "test_oct2_.h5")

    # Run model here
    if model == "lidar":
        ndhm_path, chm_path = your_main_model_function(
            bounding_box, session_dir, ept_id, ept_url, ept_epsg, model_path
        )
    elif model == "both":
        pass
        # ndhm_path, chm_path, naip_path = your_main_model_function2(
        #     bounding_box,
        #     session_dir,
        #     ept_id,
        #     ept_url,
        #     ept_epsg,
        #     naip_id,
        #     naip_url,
        #     naip_epsg,
        #     naip_gsd,
        #     model_path,
        # )
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

    # Get rescale values for ndhm
    with rasterio.open(ndhm_path) as src:
        band1 = src.read(1)
        ndhm_min_value = band1.min()
        ndhm_max_value = band1.max()

    # Create response with URL for CHM and session ID
    response = JSONResponse(
        content={
            "chm": {
                "href": chm_path,
                "rescale": f"{chm_min_value},{chm_max_value}",
            },
            "ndhm": {
                "href": ndhm_path,
                "rescale": f"{ndhm_min_value},{ndhm_max_value}",
            },
            "session_id": session_id,
        }
    )
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    return response
