from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database import SessionLocal
from .. import models, schemas
from ..utils.email_service import send_email
from typing import Optional
from sqlalchemy import or_


router = APIRouter(prefix="/tasks", tags=["Tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    today = date.today()
    task_date = task.date or today

    # Check backdated entries (if not today)
    if task_date != today:
        user_task_count = db.query(models.Task).filter(
            models.Task.user_id == task.user_id,
            models.Task.date != today
        ).count()
        if user_task_count >= 5:
            raise HTTPException(status_code=400, detail="Max 5 backdated entries allowed")

    db_task = models.Task(**task.dict(), date=task_date)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Email manager for backdated
    if task_date != today:
        user = db.query(models.User).filter(models.User.id == task.user_id).first()
        mgr = db.query(models.User).filter(models.User.name == user.reporting_manager).first()
        if mgr and mgr.email:
            send_email(
                subject="Backdated Task Approval Needed",
                body=f"User {user.name} added a backdated task for {task_date}. Please review.",
                to=mgr.email
            )

    return db_task

@router.get("/")
def list_tasks(user_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Task)
    if user_id:
        query = query.filter(models.Task.user_id == user_id)
    return query.all()

@router.get("/")
def list_tasks(
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, gt=0),
    page_size: int = Query(10, gt=0)
):
    query = db.query(models.Task)

    # Filters
    if user_id:
        query = query.filter(models.Task.user_id == user_id)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    if from_date and to_date:
        query = query.filter(models.Task.date.between(from_date, to_date))
    if search:
        query = query.filter(
            or_(
                models.Task.title.ilike(f"%{search}%"),
                models.Task.details.ilike(f"%{search}%")
            )
        )

    total = query.count()
    tasks = query.order_by(models.Task.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "tasks": tasks
    }
