from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app import schemas, models
from app.dependencies import get_async_db, get_current_user
from app.services import user_service
from sqlalchemy import select

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    return await user_service.create_user(user, db)

@router.get("/", response_model=List[schemas.UserOut])
async def get_users(
    role: Optional[schemas.RoleEnum] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
):
    return await user_service.get_users(db, role, active)

@router.get("/get-users", response_model=List[schemas.SimpleUser])
async def get_filtered_users(
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_user)
):
    query = await db.execute(select(models.User).filter(models.User.is_active == True))
    users = query.scalars().all()

    if current_user.role == models.RoleEnum.Employee:
        return [{"id": current_user.id, "name": current_user.name}]

    elif current_user.role == models.RoleEnum.TL:
        return [{"id": current_user.id, "name": current_user.name}] + [
            {"id": u.id, "name": u.name} for u in users if u.tl == current_user.id
        ]

    elif current_user.role == models.RoleEnum.Manager:
        return [{"id": current_user.id, "name": current_user.name}] + [
            {"id": u.id, "name": u.name} for u in users if u.reporting_manager == current_user.id
        ]

    return [{"id": u.id, "name": u.name} for u in users]

@router.get("/{user_id}", response_model=schemas.UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    return await user_service.get_user_by_id(user_id, db)

@router.put("/{user_id}", response_model=schemas.UserOut)
async def update_user(user_id: int, updates: schemas.UserUpdate, db: AsyncSession = Depends(get_async_db)):
    return await user_service.update_user(user_id, updates, db)

@router.delete("/{user_id}", response_model=schemas.UserOut)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    return await user_service.delete_user(user_id, db)
