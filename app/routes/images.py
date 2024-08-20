# app/routes/images.py
from fastapi import APIRouter, HTTPException
from app.models import UploadData, RectangleAnnotation, PolygonAnnotation,SegmentationAnnotation
from app.database import images_collection, projects_collection
from app.exceptions import ImageNotFoundError, ProjectNotFoundError
from bson import ObjectId
import base64
import io
import json
from fastapi.responses import StreamingResponse,JSONResponse

router = APIRouter()

@router.post("/projects/{project_name}/upload/")
async def upload_image(project_name: str, data: UploadData):
    try:
        project = await projects_collection.find_one({"name": project_name})
        if not project:
            raise ProjectNotFoundError()

        project_id = project["_id"]

        validated_rectangle_annotations = [RectangleAnnotation(**annotation.dict()) for annotation in data.rectangle_annotations] if data.rectangle_annotations else []
        validated_polygon_annotations = [PolygonAnnotation(**annotation.dict()) for annotation in data.polygon_annotations] if data.polygon_annotations else []
        validated_segmentation_annotations = [SegmentationAnnotation(**annotation.dict()) for annotation in data.segmentation_annotations] if data.segmentation_annotations else []


        image_content = base64.b64decode(data.file_content)
        encoded_image_content = base64.b64encode(image_content).decode('utf-8')

        existing_image = await images_collection.find_one({
            "content": encoded_image_content,
            "project_id": ObjectId(project_id)
        })

        if existing_image:
            update_result = await images_collection.update_one(
                {"_id": existing_image["_id"]},
                {
                    "$set": {
                        "rectangle_annotations": [annotation.dict() for annotation in validated_rectangle_annotations],
                        "polygon_annotations": [annotation.dict() for annotation in validated_polygon_annotations],
                        "segmentation_annotations": [annotation.dict() for annotation in validated_segmentation_annotations],
                        "mime_type": data.mime_type or "application/octet-stream",
                        "width_multiplier": data.image.width_multiplier,
                        "height_multiplier": data.image.height_multiplier
                    }
                }
            )
            if update_result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Image not found for update")
            return {"image_id": str(existing_image["_id"])}
        else:
            image_data = {
                "project_id": ObjectId(project_id),
                "filename": data.file_name,
                "content": encoded_image_content,
                "rectangle_annotations": [annotation.dict() for annotation in validated_rectangle_annotations],
                "polygon_annotations": [annotation.dict() for annotation in validated_polygon_annotations],
                "segmentation_annotations": [annotation.dict() for annotation in validated_segmentation_annotations],
                "mime_type": data.mime_type or "application/octet-stream",
                "width": data.image.width,
                "height": data.image.height,
                "width_multiplier": data.image.width_multiplier,
                "height_multiplier": data.image.height_multiplier
            }
            result = await images_collection.insert_one(image_data)
            return {"image_id": str(result.inserted_id)}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for annotations")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_name}/images/")
async def get_project_images(project_name: str):
    project = await projects_collection.find_one({"name": project_name})
    if not project:
        raise ProjectNotFoundError()

    project_id = project["_id"]
    images = await images_collection.find({"project_id": ObjectId(project_id)}).to_list(length=None)

    response = []
    for image in images:
        file_content = base64.b64decode(image["content"])
        response.append({
            "image_id": str(image["_id"]),
            "filename": image["filename"],
            "rectangle_annotations": image.get("rectangle_annotations", []),
            "polygon_annotations": image.get("polygon_annotations", []),
            "segmentation_annotations": image.get("segmentation_annotations", []),
            "src": base64.b64encode(file_content).decode('utf-8'),
            "mime_type": image.get("mime_type", "application/octet-stream"),
            "width": image.get("width", 0),
            "height": image.get("height", 0),
            "width_multiplier": image.get("width_multiplier", 1),
            "height_multiplier": image.get("height_multiplier", 1)
        })

    return response

@router.get("/images/{image_id}")
async def get_image(image_id: str):
    image = await images_collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return {
            "filename": image["filename"],
            "rectangle_annotations": image.get("rectangle_annotations", []),
            "polygon_annotations": image.get("polygon_annotations", []),
            "segmentation_annotations": image.get("segmentation_annotations", []),
            "image_url": f"/images/content/{image_id}",
            "width": image.get("width", 0),
            "height": image.get("height", 0),
            "width_multiplier": image.get("width_multiplier", 1), 
            "height_multiplier": image.get("height_multiplier", 1)
        }
    raise ImageNotFoundError()

@router.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    try:
        image = await images_collection.find_one({"_id": ObjectId(image_id)})
        if image:
            #logger.debug(f"Image content type: {type(image['content'])}")
            image_content = base64.b64decode(image['content'])
            return StreamingResponse(io.BytesIO(image_content), media_type=image["mime_type"])
        else:
            raise ImageNotFoundError()
    except Exception as e:
        #logger.error(f"Error retrieving image content for {image_id}: {e}")
        raise ImageNotFoundError()
    
@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    delete_result = await images_collection.delete_one({"_id": ObjectId(image_id)})

    if delete_result.deleted_count == 1:
        return {"message": f"Image with id {image_id} and all its annotations have been deleted."}
    else:
        raise ImageNotFoundError()
