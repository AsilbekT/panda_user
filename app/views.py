from fastapi_pagination import Page
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
from .models import UserProfile
from .database import get_db
from .schemas import UserProfileCreate, StandardResponse, UserProfileList
from sqlalchemy.future import select
from sqlalchemy import or_
from .utils import SERVICES, delete_avatar_file, save_avatar_file
from fastapi_pagination.ext.sqlalchemy import paginate


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_all_users(db: AsyncSession = Depends(get_db)) -> Page[UserProfileList]:
    query = select(UserProfile)
    return await paginate(db, query)


def get_token_from_header(authorization: str = Depends(api_key_header)) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=401, detail="You must be logged in to access this resource")

    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Invalid authorization type")
        return token
    except ValueError:
        raise HTTPException(
            status_code=401, detail="Invalid authorization header")


def verify_token_and_session_with_auth_service(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client() as client:
        try:
            response = client.get(
                SERVICES['authservice'] + "/auth/verify-token", headers=headers)
            response.raise_for_status()
            data = response.json()
            if not data.get("status", 'success'):
                raise HTTPException(status_code=401, detail="Inactive session")
            # You can add more checks based on the response structure
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code,
                                detail="Auth service token verification failed")
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIyLCJ1c2VybmFtZSI6ImFzaWxiZWszIiwic2Vzc2lvbl9pZCI6MTIsImV4cCI6MTcwMzc5MDU2NH0.NqnGhM2WGDLX-Z0fy4njTMAOfvSJsH9psxA6sAZRdYY


async def create_profile(profile: UserProfileCreate, db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Check for existing user with the same username or phone number
    existing_user = (
        await db.execute(
            select(UserProfile).filter(
                or_(
                    UserProfile.username == profile.username,
                    UserProfile.phone_number == profile.phone_number
                )
            )
        )
    ).scalar_one_or_none()

    if existing_user:
        # Determine which field is causing the conflict
        conflict_field = "username" if existing_user.username == profile.username else "phone number"
        raise HTTPException(
            status_code=400, detail=f"{conflict_field.capitalize()} already exists")

    db_profile = UserProfile(
        phone_number=profile.phone_number,
        name=profile.name,
        username=profile.username,
        avatar=profile.avatar,
        preferences=profile.preferences,
        history=profile.history
    )
    if db_profile.avatar:
        if db_profile.avatar.size > 1_000_000:  # 1MB size limit
            raise HTTPException(
                status_code=400, detail="Avatar file size exceeds 1MB limit")
        avatar_path = await save_avatar_file(profile.avatar)
        db_profile.avatar = avatar_path

    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return StandardResponse(status="success", message="User created successfully")


async def get_profile(token: str = Depends(get_token_from_header), db: AsyncSession = Depends(get_db)) -> StandardResponse:
    verify_token_and_session_with_auth_service(token)

    try:
        print(token)
        token_data = decode_jwt_token(token)
    except Exception as e:
        print(f"An error occurred while decoding the token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    username = token_data['username']

    db_profile = (await db.execute(select(UserProfile).filter(UserProfile.username == username))).scalar_one_or_none()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    response_data = UserProfileCreate.from_orm(db_profile)

    return StandardResponse(status="success", message="Profile retrieved successfully", data=response_data)


async def update_profile(profile_update: UserProfileCreate, token: str = Depends(get_token_from_header), db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Decode the JWT token to get the username
    token_data = decode_jwt_token(token)
    username = token_data['username']

    # Retrieve the existing user profile from the database
    result = await db.execute(select(UserProfile).filter(UserProfile.username == username))
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


async def delete_profile(token: str = Depends(get_token_from_header), db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Decode token to get username
    token_data = decode_jwt_token(token)
    username = token_data['username']
    
    # Fetch the user profile
    result = await db.execute(select(UserProfile).filter(UserProfile.username == username))
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


async def get_statistics(db: AsyncSession = Depends(get_db)) -> StandardResponse:
    # Total number of user profiles
    total_user_count = await db.scalar(select(func.count()).select_from(UserProfile))

    # Number of users with a phone number
    users_with_phone_count = await db.scalar(select(func.count()).where(UserProfile.phone_number.isnot(None)))

    # Users updated their profiles in the last 30 days
    recently_updated_user_count = await db.scalar(
        select(func.count()).where(UserProfile.updated_at >
                                   func.now() - timedelta(days=30))
    )

    # Users with all profile fields completed
    complete_profiles_count = await db.scalar(
        select(func.count()).where(
            and_(
                UserProfile.phone_number.isnot(None),
                UserProfile.name.isnot(None),
                UserProfile.avatar.isnot(None),
                UserProfile.preferences.isnot(None),
                UserProfile.history.isnot(None)
            )
        )
    )

    # Users with avatars
    users_with_avatars_count = await db.scalar(select(func.count()).where(UserProfile.avatar.isnot(None)))

    # Users with preferences set
    users_with_preferences_count = await db.scalar(select(func.count()).where(UserProfile.preferences.isnot(None)))

    # Users created in the last 30 days
    new_users_in_last_30_days_count = await db.scalar(
        select(func.count()).where(UserProfile.created_at >
                                   func.now() - timedelta(days=30))
    )

    # Users who joined today
    today_new_users_count = await db.scalar(
        select(func.count()).where(
            extract('day', UserProfile.created_at) == datetime.utcnow().day,
            extract('month', UserProfile.created_at) == datetime.utcnow().month,
            extract('year', UserProfile.created_at) == datetime.utcnow().year
        )
    )

    # Users who joined this week
    current_week_new_users_count = await db.scalar(
        select(func.count()).where(
            UserProfile.created_at >= datetime.utcnow(
            ) - timedelta(days=datetime.utcnow().weekday())
        )
    )

    # Users who joined this month
    current_month_new_users_count = await db.scalar(
        select(func.count()).where(
            extract('month', UserProfile.created_at) == datetime.utcnow().month,
            extract('year', UserProfile.created_at) == datetime.utcnow().year
        )
    )

    # Hourly user creation distribution
    hourly_user_creation_distribution = await db.execute(
        select(extract('hour', UserProfile.created_at), func.count()
               ).group_by(extract('hour', UserProfile.created_at))
    )
    hourly_creation_data = {hour: count for hour,
                            count in hourly_user_creation_distribution}

    response_data = {
        "total_user_count": total_user_count,
        "users_with_phone_count": users_with_phone_count,
        "recently_updated_user_count": recently_updated_user_count,
        "complete_profiles_count": complete_profiles_count,
        "users_with_avatars_count": users_with_avatars_count,
        "users_with_preferences_count": users_with_preferences_count,
        "new_users_in_last_30_days_count": new_users_in_last_30_days_count,
        "today_new_users_count": today_new_users_count,
        "current_week_new_users_count": current_week_new_users_count,
        "current_month_new_users_count": current_month_new_users_count,
        "hourly_creation_data": hourly_creation_data,
    }

    return StandardResponse(status="success", message="Detailed user statistics retrieved successfully", data=response_data)
