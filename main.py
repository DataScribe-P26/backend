import logging
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
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
    allow_origins=["http://localhost:5173"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient("mongodb+srv://Mohit:Tz4O610okBOvSpIu@cluster0.a2yzwap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['annotated_images']
projects_collection = db['projects']
images_collection = db['images']

class Annotation(BaseModel):
    class_name: str
    x: float
    y: float
    height: float
    width: float

class ImageData(BaseModel):
    filename: str
    annotations: List[Annotation]

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

@app.post("/projects/{project_id}/upload/")
async def upload_image(
    project_id: str,
    annotations: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload an image along with its annotations to a specific project.
    """
    try:
        project = await projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise ProjectNotFoundError()

        annotation_data = json.loads(annotations)
        
        if 'annotations' not in annotation_data or not isinstance(annotation_data['annotations'], list):
            raise InvalidAnnotationError("Invalid structure for annotations")
        
        for annotation in annotation_data['annotations']:
            Annotation(**annotation)  # Validate each annotation
            
    except json.JSONDecodeError:
        raise InvalidAnnotationError("Invalid JSON format for annotations")
    
    image_content = await file.read()
    image_data = {
        "project_id": ObjectId(project_id),
        "filename": file.filename,
        "content": base64.b64encode(image_content).decode('utf-8'),
        "annotations": annotation_data['annotations'],
        "mime_type": file.content_type  # Store the MIME type
    }
    result = await images_collection.insert_one(image_data)
    return {"image_id": str(result.inserted_id)}

@app.get("/projects/{project_id}/images/")
async def get_project_images(project_id: str):
    project = await projects_collection.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise ProjectNotFoundError()
    
    images = await images_collection.find({"project_id": ObjectId(project_id)}).to_list(length=None)
    return [{"image_id": str(image["_id"]), "filename": image["filename"]} for image in images]

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    image = await images_collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return {
            "filename": image["filename"],
            "annotations": image.get("annotations", []),
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
