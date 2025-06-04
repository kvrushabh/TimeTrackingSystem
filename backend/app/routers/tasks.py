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
from app.models import TaskStatusEnum, RoleEnum
from app.dependencies import get_current_user
from app.models import User

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

    status = TaskStatusEnum.ToBeApproved if is_backdated else TaskStatusEnum.InProgress

    task_data = task.dict()
    task_data.pop("is_backdated", None)
    task_data.pop("is_approved", None)
    task_data["status"] = status
    task_data["is_backdated"] = is_backdated
    task_data["is_approved"] = False

    new_task = models.Task(**task_data)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.put("/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(task_id: int, end_time: Optional[datetime] = None, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatusEnum.InProgress:
        raise HTTPException(status_code=400, detail="Only 'In Progress' tasks can be completed")

    final_end_time = end_time or datetime.now(timezone.utc)

    if final_end_time < task.start_time:
        raise HTTPException(status_code=400, detail="End time cannot be before start time")

    total_time = (final_end_time - task.start_time).total_seconds() / 60
    task.end_time = final_end_time
    task.status = TaskStatusEnum.Done
    task.total_time_minutes = round(total_time, 2)

    db.commit()
    db.refresh(task)
    return task


@router.post("/", response_model=List[schemas.TaskOut])
def list_tasks(
    filters: schemas.TaskFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    search: Optional[str] = None,
):
    query = db.query(models.Task)

    if current_user.role == RoleEnum.Employee:
        query = query.filter(models.Task.user_id == current_user.id)
    elif current_user.role == RoleEnum.TL:
        tl_ids = [u.id for u in db.query(User).filter(User.TL == current_user.id)]
        query = query.filter(models.Task.user_id.in_([current_user.id] + tl_ids))
    elif current_user.role == RoleEnum.Manager:
        mgr_ids = [u.id for u in db.query(User).filter(User.reporting_manager == current_user.id)]
        query = query.filter(models.Task.user_id.in_([current_user.id] + mgr_ids))
    # Admin/Management see all

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

        if filters.filter_backdated_by_creator_type == "own":
            query = query.filter(models.Task.user_id == models.Task.created_by)
        elif filters.filter_backdated_by_creator_type == "manager":
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
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
):
    query = db.query(models.Task)

    if current_user.role == RoleEnum.Employee:
        query = query.filter(models.Task.user_id == current_user.id)
    elif current_user.role == RoleEnum.TL:
        tl_ids = [u.id for u in db.query(User).filter(User.TL == current_user.id)]
        query = query.filter(models.Task.user_id.in_([current_user.id] + tl_ids))
    elif current_user.role == RoleEnum.Manager:
        mgr_ids = [u.id for u in db.query(User).filter(User.reporting_manager == current_user.id)]
        query = query.filter(models.Task.user_id.in_([current_user.id] + mgr_ids))

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

        if filters.filter_backdated_by_creator_type == "own":
            query = query.filter(models.Task.user_id == models.Task.created_by)
        elif filters.filter_backdated_by_creator_type == "manager":
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
    data = [dict(
        User_ID=t.user_id,
        Created_By=t.created_by,
        Project_ID=t.project_id,
        Date=t.date,
        Title=t.task_title,
        Details=t.task_details,
        Start_Time=t.start_time,
        End_Time=t.end_time,
        Task_Type=t.task_type,
        Status=t.status,
        Backdated=t.is_backdated,
        Approved=t.is_approved,
        Total_Time_Minutes=t.total_time_minutes,
    ) for t in tasks]

    output_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"tasks_{datetime.now().timestamp()}.xlsx")

    import pandas as pd
    pd.DataFrame(data).to_excel(file_path, index=False)

    return FileResponse(
        path=file_path,
        filename="task_report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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


@router.put("/{task_id}/edit", response_model=schemas.TaskOut)
def edit_task(task_id: int, updated_data: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role in [RoleEnum.Employee, RoleEnum.TL]:
        raise HTTPException(status_code=403, detail="Permission denied")

    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role in [RoleEnum.Employee, RoleEnum.TL]:
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}

