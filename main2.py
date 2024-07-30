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
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client['annotated_images']
collection = db['images']


class Annotation(BaseModel):
    class_name: str
    x: int
    y: int
    height: int
    width: int


class ImageData(BaseModel):
    filename: str
    annotations: List[Annotation]

@app.post("/upload/")
async def upload_images(
    files: List[UploadFile] = File(...),
    annotations: str = Form(...)
):
    try:
        
        annotations_list = json.loads(annotations)
        
        
        if len(files) != len(annotations_list):
            raise HTTPException(status_code=400, detail="Number of files and annotations must match")

        for annotation_data in annotations_list:
            for annotation in annotation_data['annotations']:
                Annotation(**annotation)  
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for annotations")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image_ids = []
    for file, annotation_data in zip(files, annotations_list):
        contents = await file.read()
        image_data = {
            "filename": file.filename,
            "content": contents,
            "annotations": annotation_data['annotations']
        }
        result = await collection.insert_one(image_data)
        image_ids.append(str(result.inserted_id))

    return {"image_ids": image_ids}

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

@app.get("/")
async def main():
    content = """
    <body>
    <form action="/upload/" enctype="multipart/form-data" method="post">
    <input name="files" type="file" multiple><br>
    <textarea name="annotations" placeholder='Enter annotations as JSON (format: [{"filename": "file1.jpg", "annotations": [...]}, ...]')></textarea><br>
    <input type="submit">
    </form>
    </body>
    """
    return HTMLResponse(content=content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
