from pydantic import BaseModel
from typing import Optional,List

# Entity schema for manual input
class EntitySchema(BaseModel):
    Entity: str
    Label: Optional[str]="UNKNOWN"  # The type can be manually defined or left empty for automatic generation
    Color: str
    bColor:  Optional[str]= None
    TextColor: str

class TextAnnotationSchema(BaseModel):
    Text: str
    Entities: Optional[List[EntitySchema]] = None

# Pydantic schema for the NER response
class NERAnnotationResponse(BaseModel):
    Entity: str
    Label: str
    Start_pos: int
    End_pos: int
    Color: str
    bColor: str
    TextColor: str

class SentimentAnnotationResponse(BaseModel):
    Text: str
    Sentiment: str
    Score: float

class ClassificationAnnotationResponse(BaseModel):
    Text: str
    Label: str
    Confidence: float

# Similar schemas for other types of annotations
# Project schemas
class ProjectCreateSchema(BaseModel):
    Name: str
    Description: Optional[str]
    Annotation_type: str

class ProjectResponseSchema(BaseModel):
    id: str
    Name: str
    Description: Optional[str]
    Annotation_type: str
  # Annotations associated with this project
