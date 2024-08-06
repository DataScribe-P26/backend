import logging
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, validator
from bson import ObjectId
import io
import json
import base64
from typing import List, Optional

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient("mongodb+srv://Mohit:Tz4O610okBOvSpIu@cluster0.a2yzwap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['annotated_images']
projects_collection = db['projects']
images_collection = db['images']

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
    file_content: str
    file_name: str
    mime_type: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None

class InvalidAnnotationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class ImageNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Image not found")

class ProjectNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Project not found")

@app.exception_handler(InvalidAnnotationError)
async def invalid_annotation_exception_handler(request: Request, exc: InvalidAnnotationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(ImageNotFoundError)
async def image_not_found_exception_handler(request: Request, exc: ImageNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(ProjectNotFoundError)
async def project_not_found_exception_handler(request: Request, exc: ProjectNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.post("/projects/")
async def create_project(project: Project):
    result = await projects_collection.insert_one(project.dict())
    return {"project_id": str(result.inserted_id)}

@app.post("/projects/{project_name}/upload/")
async def upload_image(project_name: str, data: UploadData):
    try:
        # Find the project by name
        project = await projects_collection.find_one({"name": project_name})
        if not project:
            raise ProjectNotFoundError()

        # Get the project ID
        project_id = project["_id"]

        # Validate annotations
        validated_rectangle_annotations = [RectangleAnnotation(**annotation.dict()) for annotation in data.rectangle_annotations] if data.rectangle_annotations else []
        validated_polygon_annotations = [PolygonAnnotation(**annotation.dict()) for annotation in data.polygon_annotations] if data.polygon_annotations else []

        # Decode base64 file content
        image_content = base64.b64decode(data.file_content)

        image_data = {
            "project_id": ObjectId(project_id),
            "filename": data.file_name,
            "content": base64.b64encode(image_content).decode('utf-8'),
            "rectangle_annotations": [annotation.dict() for annotation in validated_rectangle_annotations],
            "polygon_annotations": [annotation.dict() for annotation in validated_polygon_annotations],
            "mime_type": data.mime_type or "application/octet-stream"  # Default MIME type if not provided
        }
        result = await images_collection.insert_one(image_data)
        return {"image_id": str(result.inserted_id)}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for annotations")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_name}/images/")
async def get_project_images(project_name: str):
    # Find the project by name
    project = await projects_collection.find_one({"name": project_name})
    if not project:
        raise ProjectNotFoundError()

    # Get the project ID
    project_id = project["_id"]

    # Retrieve images associated with the project ID
    images = await images_collection.find({"project_id": ObjectId(project_id)}).to_list(length=None)

    # Prepare the response with image content
    response = []
    for image in images:
        file_content = base64.b64decode(image["content"])
        response.append({
            "image_id": str(image["_id"]),
            "filename": image["filename"],
            "rectangle_annotations": image.get("rectangle_annotations", []),
            "polygon_annotations": image.get("polygon_annotations", []),
            "src": base64.b64encode(file_content).decode('utf-8'),  # Encode content as base64
            "mime_type": image.get("mime_type", "application/octet-stream")  # Default MIME type if not provided
        })

    return response


@app.get("/projects/")
async def get_all_projects():
    try:
        projects = await projects_collection.find().to_list(length=None)
        return [{"project_id": str(project["_id"]), "name": project["name"], "description": project.get("description", "")} for project in projects]
    except Exception as e:
        logger.error(f"Error retrieving projects: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving projects")

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    image = await images_collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return {
            "filename": image["filename"],
            "rectangle_annotations": image.get("rectangle_annotations", []),
            "polygon_annotations": image.get("polygon_annotations", []),
            "image_url": f"/images/content/{image_id}"
        }
    raise ImageNotFoundError()

@app.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    try:
        image = await images_collection.find_one({"_id": ObjectId(image_id)})
        if image:
            logger.debug(f"Image content type: {type(image['content'])}")
            image_content = base64.b64decode(image['content'])
            return StreamingResponse(io.BytesIO(image_content), media_type=image["mime_type"])
        else:
            raise ImageNotFoundError()
    except Exception as e:
        logger.error(f"Error retrieving image content for {image_id}: {e}")
        raise ImageNotFoundError()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
