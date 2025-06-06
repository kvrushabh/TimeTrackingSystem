from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date, timezone

from app import schemas
from app.dependencies import get_async_db, get_current_user
from app.models import User, RoleEnum, TaskStatusEnum
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/create", response_model=schemas.TaskOut)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(get_async_db)):
    return await task_service.create_task(task, db)


@router.put("/{task_id}/complete", response_model=schemas.TaskOut)
async def complete_task(task_id: int, end_time: Optional[datetime] = None, db: AsyncSession = Depends(get_async_db)):
    return await task_service.complete_task(task_id, end_time, db)


@router.post("/", response_model=List[schemas.TaskOut])
async def list_tasks(
    filters: schemas.TaskFilterRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    search: Optional[str] = None,
):
    return await task_service.list_tasks(filters, db, current_user, page, page_size, search)


@router.put("/{task_id}/approve", response_model=schemas.TaskOut)
async def approve_task(task_id: int, db: AsyncSession = Depends(get_async_db)):
    return await task_service.approve_task(task_id, db)


@router.put("/{task_id}/edit", response_model=schemas.TaskOut)
async def edit_task(
    task_id: int,
    updated_data: schemas.TaskUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await task_service.edit_task(task_id, updated_data, db, current_user)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    return await task_service.delete_task(task_id, db, current_user)
