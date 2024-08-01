from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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

@app.post("/upload/")
async def upload_image(
    annotations: str = Form(...),
    src: str = Form(...)
):
    try:
        annotation_data = json.loads(annotations)
        
        # Ensure the expected structure is a dictionary containing an 'annotations' key
        if 'annotations' not in annotation_data or not isinstance(annotation_data['annotations'], list):
            raise ValueError("Invalid structure for annotations")
        
        # Validate each annotation in the list
        for annotation in annotation_data['annotations']:
            Annotation(**annotation)
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for annotations")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    image_data = {
        "filename": "image.png",  # You can set this as per your requirements
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
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    image = await collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return StreamingResponse(io.BytesIO(image['content']), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
