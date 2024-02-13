from pydantic import BaseModel
from typing import Optional, Any
from fastapi import UploadFile, File
from datetime import datetime


class UserProfileCreate(BaseModel):
    id: Optional[int] = None
    phone_number: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[str] = None
    history: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StandardResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None


class UserProfileList(BaseModel):
    id: int
    username: Optional[str]
    name: Optional[str]


class UserProfileAvatar(BaseModel):
    avatar: UploadFile = None


class UserProfileResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    username: str
    avatar: str | None
    preferences: str | None
    history: str | None
    created_at: datetime

    class Config:
        from_attributes = True