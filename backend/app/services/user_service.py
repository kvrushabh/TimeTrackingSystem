from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app import models, schemas
from app.utils.auth import hash_password
from sqlalchemy import func


async def create_user(data: schemas.UserCreate, db: AsyncSession):
    existing_user = await db.execute(
        select(models.User).filter(models.User.username == data.username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    if data.email:
        existing_email = await db.execute(
            select(models.User).filter(models.User.email == data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

    max_code_result = await db.execute(select(func.max(models.User.employee_code)))
    max_code = max_code_result.scalar() or 1000  # Start from 1001
    new_code = max_code + 1

    hashed_pw = hash_password(data.password)
    new_user = models.User(
        **data.dict(exclude={"password", "employee_code"}),
        password=hashed_pw,
        employee_code=new_code
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_users(db: AsyncSession, role: Optional[schemas.RoleEnum] = None, active: Optional[bool] = None):
    query = select(models.User)
    if role:
        query = query.filter(models.User.role == role)
    if active is not None:
        query = query.filter(models.User.is_active == active)
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_by_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def update_user(user_id: int, updates: schemas.UserUpdate, db: AsyncSession):
    user = await get_user_by_id(user_id, db)
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(user_id: int, db: AsyncSession):
    user = await get_user_by_id(user_id, db)
    await db.delete(user)
    await db.commit()
    return user
