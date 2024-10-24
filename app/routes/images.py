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
        project = await projects_collection.find_one({"Name": project_name})
        if not project:
            raise ProjectNotFoundError()

        project_id = project["_id"]

        validated_rectangle_annotations = [RectangleAnnotation(**annotation.dict()) for annotation in data.Rectangle_annotations] if data.Rectangle_annotations else []
        validated_polygon_annotations = [PolygonAnnotation(**annotation.dict()) for annotation in data.Polygon_annotations] if data.Polygon_annotations else []
        validated_segmentation_annotations = [SegmentationAnnotation(**annotation.dict()) for annotation in data.Segmentation_annotations] if data.Segmentation_annotations else []


        image_content = base64.b64decode(data.File_content)
        encoded_image_content = base64.b64encode(image_content).decode('utf-8')

        existing_image = await images_collection.find_one({
            "Content": encoded_image_content,
            "Project_id": ObjectId(project_id)
        })

        if existing_image:
            update_result = await images_collection.update_one(
                {"_id": existing_image["_id"]},
                {
                    "$set": {
                        "Rectangle_annotations": [annotation.dict() for annotation in validated_rectangle_annotations],
                        "Polygon_annotations": [annotation.dict() for annotation in validated_polygon_annotations],
                        "Segmentation_annotations": [annotation.dict() for annotation in validated_segmentation_annotations],
                        "Mime_type": data.Mime_type or "application/octet-stream",
                        "Width_multiplier": data.Image.Width_multiplier,
                        "Height_multiplier": data.Image.Height_multiplier
                    }
                }
            )
            if update_result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Image not found for update")
            return {"image_id": str(existing_image["_id"])}
        else:
            image_data = {
                "Project_id": ObjectId(project_id),
                "Filename": data.File_name,
                "Content": encoded_image_content,
                "Rectangle_annotations": [annotation.dict() for annotation in validated_rectangle_annotations],
                "Polygon_annotations": [annotation.dict() for annotation in validated_polygon_annotations],
                "Segmentation_annotations": [annotation.dict() for annotation in validated_segmentation_annotations],
                "Mime_type": data.Mime_type or "application/octet-stream",
                "Width": data.Image.Width,
                "Height": data.Image.Height,
                "Width_multiplier": data.Image.Width_multiplier,
                "Height_multiplier": data.Image.Height_multiplier
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
    images = await images_collection.find({"Project_id": ObjectId(project_id)}).to_list(length=None)

    response = []
    for image in images:
        file_content = base64.b64decode(image["Content"])
        response.append({
            "Image_id": str(image["_id"]),
            "Filename": image["Filename"],
            "Rectangle_annotations": image.get("Rectangle_annotations", []),
            "Polygon_annotations": image.get("Polygon_annotations", []),
            "Segmentation_annotations": image.get("Segmentation_annotations", []),
            "Src": base64.b64encode(file_content).decode('utf-8'),
            "Mime_type": image.get("Mime_type", "application/octet-stream"),
            "Width": image.get("Width", 0),
            "Height": image.get("Height", 0),
            "Width_multiplier": image.get("Width_multiplier", 1),
            "Height_multiplier": image.get("Height_multiplier", 1)
        })

    return response

@router.get("/images/{image_id}")
async def get_image(image_id: str):
    image = await images_collection.find_one({"_id": ObjectId(image_id)})
    if image:
        return {
            "Filename": image["Filename"],
            "Rectangle_annotations": image.get("Rectangle_annotations", []),
            "Polygon_annotations": image.get("Polygon_annotations", []),
            "Segmentation_annotations": image.get("Segmentation_annotations", []),
            "Image_url": f"/images/content/{image_id}",
            "Width": image.get("Width", 0),
            "Height": image.get("Height", 0),
            "Width_multiplier": image.get("Width_multiplier", 1),
            "Height_multiplier": image.get("Height_multiplier", 1)
        }
    raise ImageNotFoundError()

@router.get("/images/content/{image_id}")
async def get_image_content(image_id: str):
    try:
        image = await images_collection.find_one({"_id": ObjectId(image_id)})
        if image:
            #logger.debug(f"Image content type: {type(image['content'])}")
            image_content = base64.b64decode(image['Content'])
            return StreamingResponse(io.BytesIO(image_content), media_type=image["Mime_type"])
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
