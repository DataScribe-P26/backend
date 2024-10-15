# app/models.py
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime


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
    created_on: str = datetime.now()


class ProjectModel(BaseModel):
    name: str
    description: Optional[str] = None
    annotation_type: str  # e.g., "NER", "Sentiment", "Classification"

    class Config:
        # Specify the collection name for your MongoDB, if needed.
        # This is more relevant when using an ODM like Beanie, so you can ignore if you're not using it.
        json_schema_extr = {
            "collection": "projects"
        }

class NERAnnotationModel(BaseModel):
    text: str
    entities: List[dict] = Field(default_factory=list)
    project: str

    class Config:
        json_schema_extr = {
            "collection": "ner_annotations"
        }

class SentimentAnnotationModel(BaseModel):
    text: str
    sentiment: str
    score: float

    class Config:
        json_schema_extr = {
            "collection": "sentiment_annotations"
        }

class ClassificationAnnotationModel(BaseModel):
    text: str
    label: str
    confidence: float

    class Config:
        json_schema_extr = {
            "collection": "classification_annotations"
        }
