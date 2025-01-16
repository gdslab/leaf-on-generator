from typing import List

from pydantic import AnyHttpUrl, BaseModel


class DatasetItem(BaseModel):
    id: str
    bbox: List[float]
    epsg: int
    href: AnyHttpUrl


class DatasetsResponse(BaseModel):
    point_cloud: List[DatasetItem]
    raster: List[DatasetItem]


class ResultDataset(BaseModel):
    href: AnyHttpUrl
    rescale: str


class ModelResponse(BaseModel):
    chm: ResultDataset
    ndhm: ResultDataset
    session_id: str
