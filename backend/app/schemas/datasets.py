from typing import List
from enum import Enum

from pydantic import AnyHttpUrl, BaseModel


class LidarDatasetItem(BaseModel):
    id: str
    bbox: List[float]
    epsg: int
    href: AnyHttpUrl


class NaipDatasetItem(BaseModel):
    id: str
    bbox: List[float]
    epsg: int
    gsd: float
    href: AnyHttpUrl


class DatasetsResponse(BaseModel):
    point_cloud: List[LidarDatasetItem]
    raster: List[NaipDatasetItem]


class ResultDataset(BaseModel):
    href: AnyHttpUrl
    rescale: str


class ModelResponse(BaseModel):
    chm: ResultDataset
    ndhm: ResultDataset
    session_id: str
