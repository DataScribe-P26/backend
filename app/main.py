# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import projects, images, text_annotation
from app.exceptions import (
    invalid_annotation_exception_handler, 
    image_not_found_exception_handler, 
    project_not_found_exception_handler,
    InvalidAnnotationError, 
    ImageNotFoundError, 
    ProjectNotFoundError
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(images.router)
app.include_router(text_annotation.router)

app.add_exception_handler(InvalidAnnotationError, invalid_annotation_exception_handler)
app.add_exception_handler(ImageNotFoundError, image_not_found_exception_handler)
app.add_exception_handler(ProjectNotFoundError, project_not_found_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)