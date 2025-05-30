from ..database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timezone
from sqlalchemy import or_
import pandas as pd
from fastapi.responses import FileResponse
import os

from app import models, schemas
from app.models import TaskStatusEnum

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    today = date.today()
    is_backdated = task.date != today

    # Enforce backdated count logic if applicable
    if is_backdated:
        first_day = today.replace(day=1)
        count = db.query(models.Task).filter(
            models.Task.user_id == task.user_id,
            models.Task.date >= first_day,
            models.Task.date < today,
            models.Task.is_backdated == True
        ).count()
        if count >= 5:
            raise HTTPException(status_code=400, detail="Max 5 backdated tasks allowed this month.")

    # Decide status
    status = TaskStatusEnum.ToBeApproved if is_backdated else TaskStatusEnum.InProgress

    # Clean the incoming data
    task_data = task.dict()
    task_data.pop("is_backdated", None)  # avoid conflict
    task_data.pop("is_approved", None)   # we'll control this
    task_data["status"] = status
    task_data["is_backdated"] = is_backdated
    task_data["is_approved"] = False

    new_task = models.Task(**task_data)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(
    task_id: int,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatusEnum.InProgress:
        raise HTTPException(status_code=400, detail="Only 'In Progress' tasks can be completed")

    final_end_time = end_time or datetime.now(timezone.utc)

    task.end_time = final_end_time
    task.status = TaskStatusEnum.Done
    db.commit()
    db.refresh(task)
    return task

@router.post("/", response_model=List[schemas.TaskOut])
def list_tasks(
    filters: schemas.TaskFilterRequest,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    search: Optional[str] = None,
):
    query = db.query(models.Task)

    # Filter logic
    if filters.user_id:
        query = query.filter(models.Task.user_id == filters.user_id)
    if filters.project_id:
        query = query.filter(models.Task.project_id == filters.project_id)
    if filters.task_type:
        query = query.filter(models.Task.task_type == filters.task_type)
    if filters.status:
        query = query.filter(models.Task.status == filters.status)
    if filters.from_date and filters.to_date:
        query = query.filter(models.Task.date.between(filters.from_date, filters.to_date))
    if search:
        query = query.filter(
            or_(
                models.Task.task_title.ilike(f"%{search}%"),
                models.Task.task_details.ilike(f"%{search}%")
            )
        )

    if filters.only_backdated:
        query = query.filter(models.Task.is_backdated == True)

        if not filters.show_all_backdated:
            query = query.filter(models.Task.is_approved == False)

        if filters.filter_backdated_by_creator_type == "own" and filters.user_id:
            query = query.filter(models.Task.user_id == models.Task.created_by)
        elif filters.filter_backdated_by_creator_type == "manager" and filters.user_id:
            query = query.filter(models.Task.user_id != models.Task.created_by)

    else:
        query = query.filter(
            or_(
                models.Task.is_backdated == False,
                models.Task.is_approved == True
            )
        )

    query = query.order_by(models.Task.start_time.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.post("/download")
def download_tasks(
    filters: schemas.TaskFilterRequest,
    db: Session = Depends(get_db),
    search: Optional[str] = None,
):
    query = db.query(models.Task)

    if filters.user_id:
        query = query.filter(models.Task.user_id == filters.user_id)
    if filters.project_id:
        query = query.filter(models.Task.project_id == filters.project_id)
    if filters.task_type:
        query = query.filter(models.Task.task_type == filters.task_type)
    if filters.status:
        query = query.filter(models.Task.status == filters.status)
    if filters.from_date and filters.to_date:
        query = query.filter(models.Task.date.between(filters.from_date, filters.to_date))
    if search:
        query = query.filter(
            or_(
                models.Task.task_title.ilike(f"%{search}%"),
                models.Task.task_details.ilike(f"%{search}%")
            )
        )

    if filters.only_backdated:
        query = query.filter(models.Task.is_backdated == True)

        if not filters.show_all_backdated:
            query = query.filter(models.Task.is_approved == False)

        if filters.filter_backdated_by_creator_type == "own" and filters.user_id:
            query = query.filter(models.Task.user_id == models.Task.created_by)
        elif filters.filter_backdated_by_creator_type == "manager" and filters.user_id:
            query = query.filter(models.Task.user_id != models.Task.created_by)

    else:
        query = query.filter(
            or_(
                models.Task.is_backdated == False,
                models.Task.is_approved == True
            )
        )

    query = query.order_by(models.Task.start_time.desc())

    tasks = query.all()
    data = [{
        "User ID": t.user_id,
        "Created By": t.created_by,
        "Project ID": t.project_id,
        "Date": t.date,
        "Title": t.task_title,
        "Details": t.task_details,
        "Start Time": t.start_time,
        "End Time": t.end_time,
        "Task Type": t.task_type,
        "Status": t.status,
        "Backdated": t.is_backdated,
        "Approved": t.is_approved,
    } for t in tasks]

    filename = f"/tmp/tasks_{datetime.now().timestamp()}.xlsx"
    pd.DataFrame(data).to_excel(filename, index=False)

    return FileResponse(path=filename, filename="tasks.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

0
@router.put("/{task_id}/approve", response_model=schemas.TaskOut)
def approve_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatusEnum.ToBeApproved:
        raise HTTPException(status_code=400, detail="Only tasks in 'To Be Approved' status can be approved")

    task.status = TaskStatusEnum.Approved
    task.is_approved = True
    db.commit()
    db.refresh(task)
    return task
