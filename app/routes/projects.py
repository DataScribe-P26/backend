# app/routes/projects.py
from fastapi import APIRouter, HTTPException
from app.models import Project
from app.database import projects_collection,text_projects_collection
from app.exceptions import ProjectNotFoundError
from datetime import datetime
from app.schemas import ProjectCreateSchema, ProjectResponseSchema
from typing import List

router = APIRouter()

@router.post("/projects/")
async def create_project(project: Project):
    try:
        result = await projects_collection.insert_one(project.dict())
        return {"project_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/")
async def get_all_projects():
    try:
        projects = await projects_collection.find().to_list(length=None)
        return [
            {
                "project_id": str(project["_id"]),
                "name": project["name"],
                "description": project.get("description", ""),
                "created_on": project.get("created_on", datetime.now()) # Formatting date to '29-August-2024'
            } 
            for project in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/textprojects", response_model=ProjectResponseSchema)
async def create_project(data: ProjectCreateSchema):
    try:
        result = await text_projects_collection.insert_one(data.dict())
                # Create a response object
        project_response = {
            "id": str(result.inserted_id),  # Convert ObjectId to string
            "name": data.name,
            "description": data.description,
            "annotation_type": data.annotation_type
        }
        return project_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/textprojects", response_model=List[ProjectResponseSchema])
async def get_all_projects():
    try:
        # Fetch all projects from the collection
        projects = await text_projects_collection.find().to_list(length=None)
        
        # Convert each project to the expected response format
        formatted_projects = [
            {
                "id": str(project["_id"]),  # Convert ObjectId to string
                "name": project["name"],
                "description": project["description"],
                "annotation_type": project["annotation_type"]
            }
            for project in projects
        ]
        
        return formatted_projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Get a project by name
@router.get("/projects/{project_name}", response_model=ProjectResponseSchema)
async def get_project(project_name: str):
    project = await text_projects_collection.find_one({"name": project_name})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponseSchema(id=str(project["_id"]), **project)