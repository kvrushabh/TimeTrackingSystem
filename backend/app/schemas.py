from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from enum import Enum

class RoleEnum(str, Enum):
    Admin = "Admin"
    Employee = "Employee"
    TL = "TL"
    Manager = "Manager"
    Management = "Management"

class UserBase(BaseModel):
    EmpCode: str
    name: str
    username: str
    department: Optional[str] = None
    reporting_manager: Optional[int] = None
    TL: Optional[int] = None
    role: RoleEnum
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    EmpCode: Optional[str]
    name: Optional[str]
    username: Optional[str]
    password: Optional[str]
    department: Optional[str]
    reporting_manager: Optional[int]
    TL: Optional[int]
    role: Optional[RoleEnum]
    is_active: Optional[bool]

class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = ""
    is_active: Optional[bool] = True

class TaskCreate(BaseModel):
    user_id: int
    project_id: int
    title: str
    details: str
    task_type: str
    date: Optional[date]
    start_time: time
    end_time: time
    reviewer_id: Optional[int]
