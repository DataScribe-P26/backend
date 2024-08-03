from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
import io
import json
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient("mongodb+srv://Mohit:Tz4O610okBOvSpIu@cluster0.a2yzwap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['annotated_images']
collection = db['images']

class Annotation(BaseModel):
    class_name: str
    x: float
    y: float
    height: float
    width: float

class ImageData(BaseModel):
    filename: str
    annotations: List[Annotation]

class InvalidAnnotationError(HTTPException):
    def _init_(self, detail: str):
        super()._init_(status_code=400, detail=detail)

class ImageNotFoundError(HTTPException):
    def _init_(self):
        super()._init_(status_code=404, detail="Image not found")

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

@app.post("/upload/")
async def upload_image(
    annotations: str = Form(...),
    src: str = Form(...)
):
    """
    """
    try:
        annotation_data = json.loads(annotations)
        
        if 'annotations' not in annotation_data or not isinstance(annotation_data['annotations'], list):
            raise InvalidAnnotationError("Invalid structure for annotations")
        
        for annotation in annotation_data['annotations']:
            Annotation(**annotation)
            
    except json.JSONDecodeError:
        raise InvalidAnnotationError("Invalid JSON format for annotations")
    
    image_data = {
        "filename": "image.png",
        "content": src,
        "annotations": annotation_data['annotations']
    }
    result = await collection.insert_one(image_data)
    return {"image_id": str(result.inserted_id)}

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    image = await collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return {
            "filename": image["filename"],
            "annotations": image.get("annotations", []),
            "image_url": f"/images/content/{image_id}"
        }
    raise ImageNotFoundError()

@app.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    image = await collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return StreamingResponse(io.BytesIO(image['content']), media_type="image/jpeg")
    raise ImageNotFoundError()

@app.delete("/images/{image_id}")
async def delete_image(image_id: str):
    result = await collection.delete_one({"_id": ObjectId(image_id)})
    if result.deleted_count == 1:
        return {"detail": "Image deleted successfully"}
    raise ImageNotFoundError()

if __name__ == "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=8000)