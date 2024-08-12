# app/models.py
from pydantic import BaseModel, validator
from typing import List, Optional

class Point(BaseModel):
    x: float
    y: float

class PolygonAnnotation(BaseModel):
    class_name: str
    points: List[Point]
    Color: str
    type: str = 'polygon'
    edit: bool

    @validator('points')
    def validate_points(cls, v):
        if len(v) < 3:
            raise ValueError('Polygon must have at least 3 points')
        return v
    
class SegmentationAnnotation(BaseModel):
    class_name: str
    points: List[Point]
    Color: str
    type: str = 'segmentation'
    edit: bool

    @validator('points')
    def validate_points(cls, v):
        if len(v) < 3:  # Ensure there's at least one point
            raise ValueError('Segmentation must have at least 1 point')
        return v

class RectangleAnnotation(BaseModel):
    class_name: str
    x: float
    y: float
    height: float
    width: float
    type: str = 'rectangle'
    Color: str
    edit: bool

class UploadData(BaseModel):
    rectangle_annotations: Optional[List[RectangleAnnotation]] = None
    polygon_annotations: Optional[List[PolygonAnnotation]] = None
    segmentation_annotations: Optional[List[SegmentationAnnotation]] = None
    file_content: str
    file_name: str
    mime_type: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None