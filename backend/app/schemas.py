from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum
from app.models import TaskTypeEnum, TaskStatusEnum


# Login Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# Enums
class RoleEnum(str, Enum):
    Admin = "Admin"
    Employee = "Employee"
    TL = "TL"
    Manager = "Manager"
    Management = "Management"


class DepartmentEnum(str, Enum):
    HR = "HR"
    QA = "QA"
    IT = "IT - SOFTWARE"
    GRAPHICS = "GRAPHICS"


# User Schemas
class UserBase(BaseModel):
    name: str
    username: str
    email: EmailStr
    department: DepartmentEnum
    reporting_manager: Optional[int] = None
    tl: Optional[int] = None
    role: RoleEnum
    is_active: bool = True
    employee_code: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str]
    department: Optional[DepartmentEnum]
    reporting_manager: Optional[int]
    tl: Optional[int]
    role: Optional[RoleEnum]
    is_active: Optional[bool]
    password: Optional[str]


class UserOut(UserBase):
    id: int
    employee_code: int

    class Config:
        from_attributes = True


class SimpleUser(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None

    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    project_code: Optional[str] = None
    project_name: str
    project_description: Optional[str] = None
    is_active: bool = True


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectOut(ProjectBase):
    id: int

    class Config:
        from_attributes = True


# Task Schemas
class TaskBase(BaseModel):
    user_id: int
    date: date
    project_id: int
    task_title: str
    task_details: str
    start_time: datetime
    end_time: Optional[datetime] = None
    task_type: TaskTypeEnum
    reviewer_id: Optional[int] = None
    is_backdated: bool = False
    is_approved: bool = False
    created_by: int
    status: Optional[TaskStatusEnum] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    task_title: Optional[str] = None
    task_details: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    reviewer_id: Optional[int] = None
    task_type: Optional[TaskTypeEnum] = None
    project_id: Optional[int] = None
    user_id: Optional[int] = None

class TaskOut(TaskBase):
    id: int
    status: TaskStatusEnum
    total_time_minutes: Optional[float] = None

    # Extra fields for display in frontend
    project_name: Optional[str] = None
    reviewer_name: Optional[str] = None

    class Config:
        from_attributes = True

class TaskFilterRequest(BaseModel):
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    task_type: Optional[TaskTypeEnum] = None
    status: Optional[TaskStatusEnum] = None
    created_by: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    timezone: Optional[str] = "UTC"

    only_backdated: Optional[bool] = False
    filter_backdated_by_creator_type: Optional[Literal["own", "manager", "all"]] = "all"
