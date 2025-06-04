from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import SessionLocal
from app.utils.auth import hash_password
from app.models import User, RoleEnum
from ..dependencies import get_current_user
from app.schemas import UserOut

router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(models.User).filter(models.User.EmpCode == user.EmpCode).first():
        raise HTTPException(status_code=400, detail="EmpCode already exists")

    # Hash the password
    user_data = user.dict()
    user_data["password"] = hash_password(user.password)

    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    role: Optional[schemas.RoleEnum] = None,
    active: Optional[bool] = None
):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    if active is not None:
        query = query.filter(models.User.is_active == active)
    return query.all()

@router.get("/get-users", response_model=List[schemas.SimpleUser])
def get_filtered_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(models.User.is_active == True)

    if current_user.role == RoleEnum.Employee:
        return [{"id": current_user.id, "name": current_user.name}]

    elif current_user.role == RoleEnum.TL:
        return [{"id": current_user.id, "name": current_user.name}] + [
            {"id": u.id, "name": u.name}
            for u in query.filter(models.User.TL == current_user.id).all()
        ]

    elif current_user.role == RoleEnum.Manager:
        return [{"id": current_user.id, "name": current_user.name}] + [
            {"id": u.id, "name": u.name}
            for u in query.filter(models.User.reporting_manager == current_user.id).all()
        ]

    # Admin / Management
    return [{"id": u.id, "name": u.name} for u in query.all()]


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, updated_data: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", response_model=schemas.UserOut)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user
