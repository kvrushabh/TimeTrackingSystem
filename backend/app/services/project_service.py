from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app import models, schemas

async def create_project(data: schemas.ProjectCreate, db: AsyncSession) -> models.Project:
    project = models.Project(**data.dict())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

async def get_all_projects(skip: int, limit: int, db: AsyncSession):
    result = await db.execute(select(models.Project).offset(skip).limit(limit))
    return result.scalars().all()

async def get_project_by_id(project_id: int, db: AsyncSession) -> models.Project:
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

async def update_project(project_id: int, updates: schemas.ProjectUpdate, db: AsyncSession) -> models.Project:
    project = await get_project_by_id(project_id, db)
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project

async def delete_project(project_id: int, db: AsyncSession):
    project = await get_project_by_id(project_id, db)
    await db.delete(project)
    await db.commit()
    return {"detail": "Project deleted successfully"}
