import json
import os
from typing import List, Tuple

import geopandas as gpd
import pdal
from shapely.geometry import box

from app.ml.lidar.model import (
    load_trained_pix2pix_model,
    generate_and_save_pix2pix_images,
)
from app.ml.lidar.my_functions import (
    generate_ndhm,
    save_patches,
    merge_patches,
    update_coordinate_system,
)


# ====================
# 1. 데이터 준비 및 DTM/DSM 생성
# ====================
def process_dtm_dsm(
    boundary_coordinates: List[float],
    session_dir: str,
    ept_id: str,
    ept_url: str,
    ept_epsg: int,
) -> Tuple[str, str]:
    """
    DTM 및 DSM 생성

    Parameters:
        boundary_coordinates (list): AOI 경계 좌표
        session_dir (str): 결과 저장 경로
        ept_id (str): 데이터셋 ID
        ept_url (str): 데이터셋 URL
        ept_epsg (str): EPSG 코드
    """
    # ====================
    # 좌표 변환
    # ====================
    # bbox_geom = box(*[coord for pair in boundary_coordinates[0] for coord in pair])
    bbox_geom = box(
        boundary_coordinates[0],
        boundary_coordinates[1],
        boundary_coordinates[2],
        boundary_coordinates[3],
    )
    poly = gpd.GeoDataFrame(geometry=[bbox_geom], crs="EPSG:4326")
    poly = poly.to_crs(ept_epsg)
    bbox_coords = poly.total_bounds.tolist()
    print("Reprojected Bounding Box:", bbox_coords)

    # ====================
    # DTM 생성 (Jupyter Notebook 방식)
    # ====================
    out_dtm_laz = os.path.join(session_dir, "clip_dtm.laz")
    out_dtm_tif = os.path.join(session_dir, "clip_dtm.tif")

    dtm_pipeline = {
        "pipeline": [
            {
                "bounds": f"([{bbox_coords[0]}, {bbox_coords[2]}], [{bbox_coords[1]}, {bbox_coords[3]}])",
                "filename": ept_url,
                "type": "readers.ept",
                "tag": "readdata",
            },
            {
                "limits": "Classification![7:7]",
                "type": "filters.range",
                "tag": "nonoise",
            },
            {
                "assignment": "Classification[:]=0",
                "type": "filters.assign",
                "tag": "wipeclasses",
            },
            {
                "out_srs": f"EPSG:{ept_epsg}",
                "type": "filters.reprojection",
                "tag": "reprojectUTM",
            },
            {"type": "filters.smrf", "tag": "groundify"},
            {
                "limits": "Classification[2:2]",
                "type": "filters.range",
                "tag": "classify",
            },
            {
                "filename": out_dtm_laz,
                "inputs": ["classify"],
                "type": "writers.las",
                "tag": "writerslas",
            },
            {
                "filename": out_dtm_tif,
                "gdalopts": "tiled=yes,compress=deflate",
                "inputs": ["writerslas"],
                "nodata": -9999,
                "output_type": "idw",
                "resolution": 1,
                "type": "writers.gdal",
                "window_size": 30,
                "override_srs": f"EPSG:{ept_epsg}",
            },
        ]
    }

    print("Running DTM Pipeline...")
    os.makedirs(session_dir, exist_ok=True)
    pdal.Pipeline(json.dumps(dtm_pipeline)).execute()
    print(f"✅ DTM Generated: {out_dtm_tif}")

    # ====================
    # DSM 생성 (기존 방식 유지)
    # ====================
    out_dsm_laz = os.path.join(session_dir, "clip_dsm.laz")
    out_dsm_tif = os.path.join(session_dir, "clip_dsm.tif")

    dsm_pipeline = {
        "pipeline": [
            {
                "bounds": f"([{bbox_coords[0]}, {bbox_coords[2]}], [{bbox_coords[1]}, {bbox_coords[3]}])",
                "filename": ept_url,
                "type": "readers.ept",
                "tag": "readdata",
            },
            {
                "assignment": "Classification[:]=0",
                "type": "filters.assign",
                "tag": "wipeclasses",
            },
            {
                "out_srs": f"EPSG:{ept_epsg}",
                "type": "filters.reprojection",
                "tag": "reprojectUTM",
            },
            {
                "filename": out_dsm_laz,
                "inputs": ["reprojectUTM"],
                "type": "writers.las",
                "tag": "savelaz",
            },
            {
                "filename": out_dsm_tif,
                "gdalopts": "tiled=yes,compress=deflate",
                "inputs": ["savelaz"],
                "nodata": -9999,
                "output_type": "max",
                "resolution": 1,
                "type": "writers.gdal",
                "window_size": 6,
                "override_srs": f"EPSG:{ept_epsg}",
            },
        ]
    }

    print("Running DSM Pipeline...")
    pdal.Pipeline(json.dumps(dsm_pipeline)).execute()
    print(f"✅ DSM Generated: {out_dsm_tif}")

    return out_dtm_tif, out_dsm_tif


# ====================
# 2. NDHM generation and Pix2Pix model execution
# ====================
def process_ndhm_and_model(
    dtm: str, dsm: str, session_dir: str, model_path: str
) -> Tuple[str, str]:
    """
    NDHM generation and Pix2Pix model application
    """
    ndhm_output = os.path.join(session_dir, "output_ndhm.tif")
    patch_folder = os.path.join(session_dir, "patches")
    output_model = os.path.join(session_dir, "gen_patches")
    merged_output = os.path.join(session_dir, "merged_gen_chm.tif")
    updated_output = os.path.join(session_dir, "updated_gen_patches")

    # NDHM generate
    generate_ndhm(dsm, dtm, ndhm_output)
    save_patches(ndhm_output, patch_folder, patch_size=256)

    # Pix2Pix model application
    model = load_trained_pix2pix_model(model_path)
    generate_and_save_pix2pix_images(model, patch_folder, output_model)
    update_coordinate_system(patch_folder, output_model, updated_output)
    merge_patches(updated_output, merged_output)

    return ndhm_output, merged_output


# ====================
# 3. main execution
# ====================
def your_main_model_function(
    boundary_coordinates: List[float],
    session_dir: str,
    ept_id: str,
    ept_url: str,
    ept_epsg: int,
    model_path: str,
) -> Tuple[str, str]:
    dtm, dsm = process_dtm_dsm(
        boundary_coordinates, session_dir, ept_id, ept_url, ept_epsg
    )
    ndhm_output, final_output = process_ndhm_and_model(
        dtm, dsm, session_dir, model_path
    )

    print(f"✅ NDHM: {ndhm_output}")
    print(f"✅ Final Leaf-on CHM: {final_output}")

    return ndhm_output, final_output
