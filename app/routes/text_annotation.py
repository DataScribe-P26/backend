from fastapi import APIRouter, HTTPException
from app.models import (
    ProjectModel,
    NERAnnotationModel,
    SentimentAnnotationModel,
    ClassificationAnnotationModel
)
from app.exceptions import ProjectNotFoundError
from app.schemas import ProjectCreateSchema, ProjectResponseSchema
from app.database import text_projects_collection,ner_annotations_collection
from ..schemas import EntitySchema,TextAnnotationSchema, NERAnnotationResponse, ClassificationAnnotationResponse
from ..services.ner_annotation import NERAnnotation
from ..services.sentiment_annotation import SentimentAnnotation
from ..services.classification_annotation import ClassificationAnnotation
from typing import List
from bson import ObjectId

router = APIRouter()

@router.post("/annotate/{project_name}/ner", response_model=List[NERAnnotationResponse])
async def annotate_ner(project_name: str, data: TextAnnotationSchema):
    ner = NERAnnotation()

    try:
        # Get the project ID if it exists
        project = await text_projects_collection.find_one({"Name": project_name})
        if not project:
            raise ProjectNotFoundError()

        project_id = str(project["_id"])

        # Add \n to each line in the text if not already present
        text_with_newlines = data.text.replace("\\n", "\n")

        # Perform NER based on the provided entities
        final_annotations = ner.annotate(data.text, data.entities)

        # Check for existing annotations
        existing_annotation = await ner_annotations_collection.find_one({"Project": project_id})

        # Avoid adding redundant annotations
        if existing_annotation:
            # Update only if entities are different to avoid duplicate entries
            update_data = {
                "Text": data.text,
                "Entities": final_annotations,
                "Project": project_id,
            }

            # Compare existing entities with the new ones
            existing_entities = existing_annotation.get("entities", [])
            if existing_entities != final_annotations:
                await ner_annotations_collection.update_one(
                    {"_id": existing_annotation["_id"]},
                    {"$set": update_data}
                )
            return final_annotations

        else:
            # Save the final annotations in the `ner_annotations` collection
            annotation_data = {
                "Text": data.text,
                "Entities": final_annotations,
                "Project": project_id,
            }
            result = await ner_annotations_collection.insert_one(annotation_data)

            # Check if the insert was successful
            if result.inserted_id:
                return final_annotations
            else:
                raise HTTPException(status_code=500, detail="Failed to save annotation")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_name}/ner/labels", response_model=List)
async def get_ner_labels(project_name: str):
    try:
        # Fetch the project to ensure it exists
        project = await text_projects_collection.find_one({"Name": project_name})
        if not project:
            raise ProjectNotFoundError()

        # Fetch only the labels (entities and types) for the project
        annotations = await ner_annotations_collection.find({"Project": str(project["_id"])}, {"Entities": 1, "_id": 0}).to_list()

        # Use a set to collect unique labels
        unique_labels = set()
        for annotation in annotations:
            for entity in annotation["Entities"]:
                unique_labels.add((entity["Entity"], entity.get("Label", "UNKNOWN"), entity["Color"], entity.get("bColor", "#ffffff"), entity["TextColor"]))

        # Convert the set back to a list of dictionaries
        labels = [{"Entity": entity, "Label": label, "Color": color, "bColor": bColor, "TextColor": textColor} for entity, label, color, bColor, textColor in unique_labels]


        return labels

    except Exception as e:
        print(f"Error occurred while fetching labels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_name}/ner/full-text", response_model=List[NERAnnotationModel])
async def get_ner_full_text(project_name: str):
    try:
        # Fetch the project to ensure it exists
        project = await text_projects_collection.find_one({"Name": project_name})
        if not project:
            raise ProjectNotFoundError()

        # Fetch the full text along with label mappings
        annotations = await ner_annotations_collection.find({"Project": str(project["_id"])}).to_list(length=None)

        if not annotations:
            raise HTTPException(status_code=404, detail="No annotations found for this project")

        results = []
        for annotation in annotations:
            labels = []
            for entity in annotation["Entities"]:
                labels.append({
                    "Entity": entity["Entity"],
                    "Label": entity.get("Label", "UNKNOWN"),
                    "Start_pos": entity["Start_pos"],
                    "End_pos": entity["End_pos"],
                    "Color": entity["Color"],
                    "bColor": entity.get("bColor", "#ffffff"),
                    "TextColor": entity["TextColor"]
                })

            results.append({
                "Id": str(annotation["_id"]),
                "Text": annotation["Text"],
                "Entities": labels,
                "Project": annotation["Project"]
            })

        return results

    except Exception as e:
        print(f"Error occurred while fetching full-text with label mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
