import logging
from fastapi import FastAPI, Form, Request, HTTPException,UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, validator
from bson import ObjectId
import io
import json
import base64
from typing import List, Optional,Union

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
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
    polygon: List[Point]
    box_type: str = 'polygon'

    @validator('polygon')
    def validate_polygon(cls, v):
        if len(v) < 3:
            raise ValueError('Polygon must have at least 3 points')
        return v


class RectangleAnnotation(BaseModel):
    class_name: str
    x: float
    y: float
    height: float
    width: float
    box_type: str = 'rectangle'

class ImageData(BaseModel):
    filename: str
    rectangle_annotations: Optional[List[RectangleAnnotation]] = None
    polygon_annotations: Optional[List[PolygonAnnotation]] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None

class InvalidAnnotationError(HTTPException):
    def _init_(self, detail: str):
        super()._init_(status_code=400, detail=detail)

class ImageNotFoundError(HTTPException):
    def _init_(self):
        super()._init_(status_code=404, detail="Image not found")

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
    rectangle_annotations: Optional[str] = Form(None),
    polygon_annotations: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    try:
        project = await projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise ProjectNotFoundError()

        rectangle_annotations_data = json.loads(rectangle_annotations) if rectangle_annotations else []
        polygon_annotations_data = json.loads(polygon_annotations) if polygon_annotations else []

        # Validate rectangle annotations
        for annotation in rectangle_annotations_data:
            RectangleAnnotation(**annotation)

        # Validate polygon annotations
        for annotation in polygon_annotations_data:
            PolygonAnnotation(**annotation)

    except json.JSONDecodeError:
        raise InvalidAnnotationError("Invalid JSON format for annotations")

    image_content = await file.read()
    image_data = {
        "project_id": ObjectId(project_id),
        "filename": file.filename,
        "content": base64.b64encode(image_content).decode('utf-8'),
        "rectangle_annotations": rectangle_annotations_data,
        "polygon_annotations": polygon_annotations_data,
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

@app.get("/images/{image_obj_id}")
async def get_image(image_obj_id: str):
    image = await images_collection.find_one({"_id": ObjectId(image_obj_id)})
    if image:
        return {
            "filename": image["filename"],
            "rectangle_annotations": image.get("rectangle_annotations", []),
            "polygon_annotations": image.get("polygon_annotations", []),
            "image_url": f"/images/content/{image_obj_id}"
        }
    raise ImageNotFoundError()

@app.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    try:
        image = await images_collection.find_one({"_id": ObjectId(image_id)})
        if image:
            logger.debug(f"Image content type: {type(image['content'])}")
            image_content = base64.b64decode(image['content'])
            return StreamingResponse(io.BytesIO(image['content']), media_type=image["mime_type"])
        else:
            raise ImageNotFoundError()
    except Exception as e:
        logger.error(f"Error retrieving image content for {image_id}: {e}")
        raise ImageNotFoundError()

@app.delete("/images/{image_id}")
async def delete_image(image_id: str):
    result = await images_collection.delete_one({"_id": ObjectId(image_id)})
    if result.deleted_count == 1:
        return {"detail": "Image deleted successfully"}
    raise ImageNotFoundError()

@app.put("/images/{image_id}/annotations/{box_type}/{class_name}")
async def update_annotation(
    image_id: str,
    box_type: str,  # Either 'rectangle' or 'polygon'
    class_name: str, 
    annotation: Union[RectangleAnnotation, PolygonAnnotation]
):
    try:
        # Fetch the image from the database
        image = await images_collection.find_one({"_id": ObjectId(image_id)})
        if not image:
            raise ImageNotFoundError()

        # Determine the correct list of annotations to update based on box_type
        if box_type == 'rectangle':
            annotations = image.get("rectangle_annotations", [])
        elif box_type == 'polygon':
            annotations = image.get("polygon_annotations", [])
        else:
            raise HTTPException(status_code=400, detail="Invalid box type")
        
        # Print current annotations for debugging
        logger.debug(f"Current annotations: {annotations}")

        updated = False

        for i, ann in enumerate(annotations):
            if ann.get("class_name") == class_name:
                # Update the annotation details
                 # Preserve the class_id
                updated_annotation = annotation.dict()
                updated_annotation["class_name"] = class_name
                annotations[i] = updated_annotation
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="Annotation not found")  
          
        # Update the annotations in the database
        update_field = f"{box_type}_annotations"
        # Update the annotations in the database
        result = await images_collection.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {update_field: annotations}}
        )

        if result.modified_count == 1:
            return {"message": "Annotation updated successfully"}
        else:
            return {"message": "No changes made to the annotation"}

    except Exception as e:
        logger.error(f"Error updating annotation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)