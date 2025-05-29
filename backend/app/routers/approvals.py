from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/approvals", tags=["Approvals"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/pending/")
def pending_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.status == "To Be Approved").all()

@router.post("/approve/{task_id}")
def approve_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "Approved"
    db.commit()
    return {"status": "Approved"}
