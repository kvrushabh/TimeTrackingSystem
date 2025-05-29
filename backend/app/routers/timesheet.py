from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from datetime import datetime
import pandas as pd
from typing import Optional
from sqlalchemy import or_
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/timesheets", tags=["Timesheets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/download/")
def download_timesheet(
    from_date: str,
    to_date: str,
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    search: Optional[str] = None
):
    query = db.query(models.Task).filter(
        models.Task.date.between(from_date, to_date)
    )

    if user_id:
        query = query.filter(models.Task.user_id == user_id)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    if search:
        query = query.filter(
            or_(
                models.Task.title.ilike(f"%{search}%"),
                models.Task.details.ilike(f"%{search}%")
            )
        )

    tasks = query.all()
    data = [{
        "User": t.user.name if t.user else "",
        "Project": t.project_id,
        "Title": t.title,
        "Start": t.start_time,
        "End": t.end_time,
        "Date": t.date,
        "Status": t.status
    } for t in tasks]

    df = pd.DataFrame(data)
    filename = f"/tmp/timesheet_{datetime.now().timestamp()}.xlsx"
    df.to_excel(filename, index=False)

    return FileResponse(path=filename, filename="timesheet.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
