# app/models.py
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime


class Point(BaseModel):
    x: float
    y: float

class PolygonAnnotation(BaseModel):
    Class_name: str
    Class_id:float
    Points: List[Point]
    Color: str
    type: str = 'Polygon'
    Edit: bool

    # @validator('points')
    # def validate_points(cls, v):
    #     if len(v) < 3:
    #         raise ValueError('Polygon must have at least 3 points')
    #     return v

class SegmentationAnnotation(BaseModel):
    Class_name: str
    Class_id:float
    Points: List[Point]
    Color: str
    type: str = 'segmentation'
    Edit: bool

    # @validator('points')
    # def validate_points(cls, v):
    #     if len(v) < 3:  # Ensure there's at least one point
    #         raise ValueError('Segmentation must have at least 1 point')
    #     return v

class RectangleAnnotation(BaseModel):
    Class_name: str
    Class_id:float
    x: float
    y: float
    Height: float
    Width: float
    type: str = 'Rectangle'
    Color: str
    Edit: bool
    Rotation: float

class Image(BaseModel):
    Width: float
    Height: float
    Width_multiplier: float
    Height_multiplier: float

class UploadData(BaseModel):
    Rectangle_annotations: Optional[List[RectangleAnnotation]] = None
    Polygon_annotations: Optional[List[PolygonAnnotation]] = None
    Segmentation_annotations: Optional[List[SegmentationAnnotation]] = None
    File_content: str
    File_name: str
    Mime_type: Optional[str] = None
    Image: Image


class Project(BaseModel):
    Name: str
    Description: Optional[str] = None
    Created_on: str = datetime.now()


class ProjectModel(BaseModel):
    Name: str
    Description: Optional[str] = None
    Annotation_type: str  # e.g., "NER", "Sentiment", "Classification"

    class Config:
        # Specify the collection name for your MongoDB, if needed.
        # This is more relevant when using an ODM like Beanie, so you can ignore if you're not using it.
        json_schema_extr = {
            "collection": "projects"
        }

class NERAnnotationModel(BaseModel):
    Text: str
    Entities: List[dict] = Field(default_factory=list)
    Project: str

    class Config:
        json_schema_extr = {
            "collection": "ner_annotations"
        }

class SentimentAnnotationModel(BaseModel):
    Text: str
    Sentiment: str
    Score: float

    class Config:
        json_schema_extr = {
            "collection": "sentiment_annotations"
        }

class ClassificationAnnotationModel(BaseModel):
    Text: str
    Label: str
    Confidence: float

    class Config:
        json_schema_extr = {
            "collection": "classification_annotations"
        }
