from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app import schemas
from app.dependencies import get_async_db
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=schemas.ProjectOut)
async def create(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_async_db)):
    return await project_service.create_project(project, db)

@router.get("/", response_model=List[schemas.ProjectOut])
async def get_all(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    return await project_service.get_all_projects(skip, limit, db)

@router.get("/{project_id}", response_model=schemas.ProjectOut)
async def get_by_id(project_id: int, db: AsyncSession = Depends(get_async_db)):
    return await project_service.get_project_by_id(project_id, db)

@router.put("/{project_id}", response_model=schemas.ProjectOut)
async def update(project_id: int, updates: schemas.ProjectUpdate, db: AsyncSession = Depends(get_async_db)):
    return await project_service.update_project(project_id, updates, db)

@router.delete("/{project_id}")
async def delete(project_id: int, db: AsyncSession = Depends(get_async_db)):
    return await project_service.delete_project(project_id, db)
