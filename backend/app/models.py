from app.utils.timestamp import TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, Time, Enum, Text, DateTime, Float
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime, timezone

class RoleEnum(enum.Enum):
    Admin = "Admin"
    Employee = "Employee"
    TL = "TL"
    Manager = "Manager"
    Management = "Management"

class DepartmentEnum(str, enum.Enum):
    HR = "HR"
    QA = "QA"
    IT = "IT - SOFTWARE"
    GRAPHICS = "GRAPHICS"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    EmpCode = Column(String(50), unique=True, nullable=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    department = Column(Enum(DepartmentEnum), nullable=False)
    reporting_manager = Column(Integer, ForeignKey('users.id'), nullable=True)
    TL = Column(Integer, ForeignKey('users.id'), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    reporting_manager_user = relationship("User", remote_side=[id], foreign_keys=[reporting_manager], post_update=True)
    tl_user = relationship("User", remote_side=[id], foreign_keys=[TL], post_update=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=True)
    project_name = Column(String(50), nullable=False)
    project_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class TaskTypeEnum(str, enum.Enum):
    Development = "Development"
    Testing = "Testing"
    Documentation = "Documentation"
    Review = "Review"
    Break = "Break"
    Customer_Interaction = "Customer Interaction"
    Internal_Discussion = "Internal Discussion"
    Deployment = "Deployment"

class TaskStatusEnum(str, enum.Enum):
    ToBeApproved = "To Be Approved"
    Approved = "Approved"
    InProgress = "In Progress"
    Done = "Done"

def today_utc():
    return datetime.now(timezone.utc).date()

class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, default=today_utc)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_title = Column(String(50), nullable=False)
    task_details = Column(String(256), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_time_minutes = Column(Float, nullable=True)
    task_type = Column(Enum(TaskTypeEnum), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(TaskStatusEnum), nullable=True)
    is_backdated = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    creator = relationship("User", foreign_keys=[created_by])
    project = relationship("Project", foreign_keys=[project_id])
