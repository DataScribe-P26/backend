# app/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class AnnotationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class InvalidAnnotationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class ImageNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Image not found")

class ProjectNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Project not found")

async def invalid_annotation_exception_handler(request: Request, exc: InvalidAnnotationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def image_not_found_exception_handler(request: Request, exc: ImageNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def project_not_found_exception_handler(request: Request, exc: ProjectNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )