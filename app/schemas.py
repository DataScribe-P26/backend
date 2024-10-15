from pydantic import BaseModel
from typing import Optional,List

# Entity schema for manual input
class EntitySchema(BaseModel):
    entity: str
    label: Optional[str]="UNKNOWN"  # The type can be manually defined or left empty for automatic generation
    color: str
    bColor:  Optional[str]= None 
    textColor: str

class TextAnnotationSchema(BaseModel):
    text: str
    entities: Optional[List[EntitySchema]] = None

# Pydantic schema for the NER response
class NERAnnotationResponse(BaseModel):
    entity: str
    label: str
    start_pos: int
    end_pos: int
    color: str
    bColor: str
    textColor: str

class SentimentAnnotationResponse(BaseModel):
    text: str
    sentiment: str
    score: float

class ClassificationAnnotationResponse(BaseModel):
    text: str
    label: str
    confidence: float

# Similar schemas for other types of annotations
# Project schemas
class ProjectCreateSchema(BaseModel):
    name: str
    description: Optional[str]
    annotation_type: str

class ProjectResponseSchema(BaseModel):
    id: str
    name: str
    description: Optional[str]
    annotation_type: str
  # Annotations associated with this project