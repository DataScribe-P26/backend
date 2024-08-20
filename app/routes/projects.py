# app/routes/projects.py
from fastapi import APIRouter, HTTPException
from app.models import Project
from app.database import projects_collection
from app.exceptions import ProjectNotFoundError
from datetime import datetime


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
                "created_on": project.get("created_on", datetime.now()).strftime('%d-%B-%Y')  # Formatting date to '29-August-2024'
            } 
            for project in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))