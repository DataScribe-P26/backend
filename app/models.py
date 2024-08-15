# app/models.py
from pydantic import BaseModel, validator
from typing import List, Optional

class Point(BaseModel):
    x: float
    y: float

class PolygonAnnotation(BaseModel):
    class_name: str
    class_id:float
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
    class_id:float
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
    class_id:float
    x: float
    y: float
    height: float
    width: float
    type: str = 'rectangle'
    Color: str
    edit: bool
    rotation: float

class Image(BaseModel):
    width: float
    height: float
    width_multiplier: float
    height_multiplier: float

class UploadData(BaseModel):
    rectangle_annotations: Optional[List[RectangleAnnotation]] = None
    polygon_annotations: Optional[List[PolygonAnnotation]] = None
    segmentation_annotations: Optional[List[SegmentationAnnotation]] = None
    file_content: str
    file_name: str
    mime_type: Optional[str] = None
    image: Image
    

class Project(BaseModel):
    name: str
    description: Optional[str] = None