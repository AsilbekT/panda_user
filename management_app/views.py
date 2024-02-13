from sqlalchemy import extract
from sqlalchemy import func, and_
import traceback
import httpx
from fastapi import HTTPException, Depends, Security, UploadFile
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from datetime import timedelta, datetime

from app.utils import decode_jwt_token
from app.models import UserProfile
from app.database import get_db
from .schemas import UserProfileCreate, StandardResponse, UserProfileList, UserProfileResponse
from sqlalchemy.future import select
from sqlalchemy import or_
from app.utils import SERVICES, delete_avatar_file, save_avatar_file


async def read_profile(user_id: int, db: AsyncSession = Depends(get_db)) -> StandardResponse:
    db_profile = (await db.execute(select(UserProfile).filter(UserProfile.id == user_id))).scalar_one_or_none()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    response_data = UserProfileResponse.from_orm(db_profile)
    return StandardResponse(status="success", message="Profile retrieved successfully", data=response_data)


async def update_profile(user_id: int, profile_update: UserProfileCreate, db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Retrieve the existing user profile from the database
    result = await db.execute(select(UserProfile).filter(UserProfile.id == user_id))
    db_profile = result.scalar_one_or_none()

    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update profile fields from the provided data
    for key, value in profile_update.dict(exclude_unset=True).items():
        # Check if the field exists on the model and is not None
        if hasattr(db_profile, key) and value is not None:
            setattr(db_profile, key, value)

    # Handle avatar upload
    if profile_update.avatar and isinstance(profile_update.avatar, UploadFile):
        if profile_update.avatar.size > 1_000_000:  # 1MB size limit
            raise HTTPException(
                status_code=400, detail="Avatar file size exceeds 1MB limit")

        avatar_path = await save_avatar_file(profile_update.avatar)
        db_profile.avatar = avatar_path

    # Commit the updates to the database
    await db.commit()
    await db.refresh(db_profile)

    # Prepare the response
    response_data = UserProfileCreate.from_orm(db_profile)
    return StandardResponse(status="success", message="Profile updated successfully", data=response_data)


async def delete_profile(user_id: int, db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Fetch the user profile
    result = await db.execute(select(UserProfile).filter(UserProfile.id == user_id))
    db_profile = result.scalar_one_or_none()
    
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Check if the profile has an avatar and delete the avatar file
    if db_profile.avatar:
        await delete_avatar_file(db_profile.avatar)

    # Delete the profile from the database
    await db.delete(db_profile)
    await db.commit()

    return StandardResponse(status="success", message="Profile deleted successfully")
