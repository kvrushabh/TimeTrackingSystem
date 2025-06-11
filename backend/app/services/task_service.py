from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional
from app import schemas
from app.models import Task, User, Project, RoleEnum, TaskStatusEnum
from fastapi import HTTPException
import io
from fastapi.responses import StreamingResponse
import pandas as pd
import pytz
from app.utils.mail_config import send_email_async
from jinja2 import Template
import os

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware and in UTC"""
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_local_str(dt: datetime, tz_str: str) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        tz = pytz.timezone(tz_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.UTC
    local_dt = dt.astimezone(tz)
    return local_dt.strftime("%m-%d-%Y %H:%M:%S")

def to_local_date_str(d: date) -> str:
    return d.strftime("%m-%d-%Y") if d else ""

def render_email_template(file_path: str, context: dict) -> str:
    with open(file_path, 'r') as f:
        template = Template(f.read())
    return template.render(**context)


async def create_task(task: schemas.TaskCreate, db: AsyncSession) -> Task:
    today = date.today()
    is_backdated = task.date != today

    # Get user
    user_result = await db.execute(select(User).where(User.id == task.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check reviewer != user
    if task.reviewer_id is not None and task.reviewer_id == task.user_id:
        raise HTTPException(status_code=400, detail="Reviewer cannot be the same as the user")

    # Check backdated limit
    if is_backdated and user.role in [RoleEnum.Employee, RoleEnum.TL]:
        first_day = today.replace(day=1)
        count_result = await db.execute(
            select(func.count()).select_from(Task).where(
                Task.created_by  == task.user_id,
                Task.date >= first_day,
                Task.date < today,
                Task.is_backdated == True
            )
        )
        count = count_result.scalar()
        if count >= 5:
            raise HTTPException(status_code=400, detail="Max 5 backdated tasks allowed per month.")

    # Convert times to UTC
    start_time = ensure_utc(task.start_time)
    end_time = ensure_utc(task.end_time)

    # Validate start and end time
    if start_time and end_time and end_time < start_time:
        raise HTTPException(status_code=400, detail="End time cannot be before start time")

    # Prepare task data
    task_data = task.dict()
    task_data["is_backdated"] = is_backdated
    task_data["is_approved"] = False
    task_data["start_time"] = start_time
    task_data["end_time"] = end_time

    if not task_data.get("status"):
        task_data["status"] = TaskStatusEnum.ToBeApproved if is_backdated else TaskStatusEnum.InProgress

    new_task = Task(**task_data)

    # Calculate total_time_minutes
    if start_time and end_time:
        total_minutes = (end_time - start_time).total_seconds() / 60
        new_task.total_time_minutes = round(total_minutes, 2)

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Send backdated email
    if is_backdated and user.role in [RoleEnum.Employee, RoleEnum.TL] and user.reporting_manager:
        manager_result = await db.execute(select(User).where(User.id == user.reporting_manager))
        manager = manager_result.scalar_one_or_none()
        if manager and manager.email:
            template_path = os.path.join("templates", "backdated_task_email.txt")
            body = render_email_template(template_path, {
                "manager_name": manager.name,
                "employee_name": user.name,
                "task_date": task.date.strftime("%Y-%m-%d"),
                "task_title": task.task_title,
                "task_details": task.task_details,
            })
            subject = f"[TimeTracking] Backdated Task Submitted by {user.name}"
            await send_email_async(subject, manager.email, body)

    return new_task


async def complete_task(task_id: int, end_time: Optional[datetime], db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatusEnum.InProgress:
        raise HTTPException(status_code=400, detail="Only 'In Progress' tasks can be completed")

    final_end_time = ensure_utc(end_time) or datetime.now(timezone.utc)
    # Ensure task.start_time is timezone-aware
    task_start_time = task.start_time
    if task_start_time.tzinfo is None:
        task_start_time = task_start_time.replace(tzinfo=timezone.utc)

    if final_end_time < task_start_time:
        raise HTTPException(status_code=400, detail="End time cannot be before start time")

    total_time = (final_end_time - task.start_time).total_seconds() / 60
    task.end_time = final_end_time
    task.status = TaskStatusEnum.Done
    task.total_time_minutes = round(total_time, 2)

    await db.commit()
    await db.refresh(task)
    return task


async def list_tasks(filters: schemas.TaskFilterRequest, db: AsyncSession, current_user: User, page: int, page_size: int, search: Optional[str]) -> List[Task]:
    stmt = select(Task)

    if current_user.role == RoleEnum.Employee:
        stmt = stmt.where(Task.user_id == current_user.id)
    elif current_user.role == RoleEnum.TL:
        tl_result = await db.execute(select(User.id).where(User.tl == current_user.id))
        ids = [r for r, in tl_result.all()]
        stmt = stmt.where(Task.user_id.in_([current_user.id] + ids))
    elif current_user.role == RoleEnum.Manager:
        mgr_result = await db.execute(select(User.id).where(User.reporting_manager == current_user.id))
        ids = [r for r, in mgr_result.all()]
        stmt = stmt.where(Task.user_id.in_([current_user.id] + ids))

    if filters.user_id:
        stmt = stmt.where(Task.user_id == filters.user_id)
    if filters.project_id:
        stmt = stmt.where(Task.project_id == filters.project_id)
    if filters.task_type:
        stmt = stmt.where(Task.task_type == filters.task_type)
    if filters.status:
        stmt = stmt.where(Task.status == filters.status)
    if filters.from_date and filters.to_date:
        stmt = stmt.where(Task.date.between(filters.from_date, filters.to_date))
    if search:
        stmt = stmt.where(or_(
            Task.task_title.ilike(f"%{search}%"),
            Task.task_details.ilike(f"%{search}%")
        ))

    if filters.only_backdated:
        stmt = stmt.where(Task.is_backdated == True)
        if filters.filter_backdated_by_creator_type == "own":
            stmt = stmt.where(Task.user_id == Task.created_by)
        elif filters.filter_backdated_by_creator_type == "manager":
            stmt = stmt.where(Task.user_id != Task.created_by)
    else:
        stmt = stmt.where(or_(
            Task.is_backdated == False,
            Task.is_approved == True
        ))

    stmt = stmt.order_by(Task.start_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


async def approve_task(task_id: int, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatusEnum.ToBeApproved:
        raise HTTPException(status_code=400, detail="Only tasks in 'To Be Approved' status can be approved")

    task.status = TaskStatusEnum.Approved
    task.is_approved = True

    await db.commit()
    await db.refresh(task)
    return task


async def edit_task(task_id: int, updated_data: schemas.TaskUpdate, db: AsyncSession, current_user: User) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role in [RoleEnum.Employee, RoleEnum.TL]:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = updated_data.dict(exclude_unset=True)

    # Do not allow start_time update for non-backdated
    if not task.is_backdated and "start_time" in updates:
        updates.pop("start_time")

    # Reviewer cannot be same as user
    if "reviewer_id" in updates and updates["reviewer_id"] == task.user_id:
        raise HTTPException(status_code=400, detail="Reviewer cannot be the same as the user")

    # Convert datetime fields to UTC
    if "start_time" in updates:
        updates["start_time"] = ensure_utc(updates["start_time"])
    if "end_time" in updates:
        updates["end_time"] = ensure_utc(updates["end_time"])

    # Validate end_time > start_time
    start_time = updates.get("start_time", task.start_time)
    end_time = updates.get("end_time", task.end_time)
    if start_time and end_time and end_time < start_time:
        raise HTTPException(status_code=400, detail="End time cannot be before start time")

    for key, value in updates.items():
        setattr(task, key, value)

    if task.start_time and task.end_time:
        task.total_time_minutes = round((task.end_time - task.start_time).total_seconds() / 60, 2)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(task_id: int, db: AsyncSession, current_user: User):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own task.")

    await db.delete(task)
    await db.commit()
    return {"detail": "Task deleted"}


async def download_task_report(filters: schemas.TaskFilterRequest, db: AsyncSession, current_user: User, search: Optional[str] = None):
    tasks = await list_tasks(filters, db, current_user, page=1, page_size=10000, search=search)

    # Collect user/project/reviewer IDs
    user_ids = {task.user_id for task in tasks}
    project_ids = {task.project_id for task in tasks}
    reviewer_ids = {task.reviewer_id for task in tasks if task.reviewer_id}
    all_user_ids = list(user_ids.union(reviewer_ids))

    # Fetch user names
    users_result = await db.execute(select(User.id, User.name).where(User.id.in_(all_user_ids)))
    user_map = {uid: name for uid, name in users_result.all()}

    # Fetch project names
    projects_result = await db.execute(select(Project.id, Project.project_name).where(Project.id.in_(project_ids)))
    project_map = {pid: name for pid, name in projects_result.all()}

    # Use frontend-sent timezone, default UTC
    user_timezone = filters.timezone or "UTC"

    # Prepare rows for DataFrame
    rows = []
    for task in tasks:
        rows.append({
            "Date": to_local_date_str(task.date),
            "User": user_map.get(task.user_id, "Unknown"),
            "Project": project_map.get(task.project_id, "Unknown"),
            "Task Title": task.task_title,
            "Task Details": task.task_details,
            "Start Time": to_local_str(task.start_time, user_timezone) if task.start_time else "",
            "End Time": to_local_str(task.end_time, user_timezone) if task.end_time else "",
            "Task Type": task.task_type.name if task.task_type else "",  # Strip enum prefix
            "Reviewer": user_map.get(task.reviewer_id, "") if task.reviewer_id else "",
            "Status": task.status.name if task.status else "",  # Strip enum prefix
            "Is Backdated": str(task.is_backdated).upper(),
            "Is Approved": str(task.is_approved).upper(),
            "Total Minutes": task.total_time_minutes,
        })

    # Generate Excel
    df = pd.DataFrame(rows)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Task Report")

    stream.seek(0)
    filename = f"task_report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

