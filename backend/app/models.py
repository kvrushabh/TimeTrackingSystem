from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, Time, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class RoleEnum(enum.Enum):
    Admin = "Admin"
    Employee = "Employee"
    TL = "TL"
    Manager = "Manager"
    Management = "Management"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    EmpCode = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    department = Column(String(50), nullable=True)
    reporting_manager = Column(Integer, ForeignKey('users.id'), nullable=True)
    TL = Column(Integer, ForeignKey('users.id'), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True)

    reporting_manager_user = relationship("User", remote_side=[id], foreign_keys=[reporting_manager], post_update=True)
    tl_user = relationship("User", remote_side=[id], foreign_keys=[TL], post_update=True)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    description = Column(String)
    is_active = Column(Boolean, default=True)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String)
    details = Column(String)
    task_type = Column(String)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="To Be Approved")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
