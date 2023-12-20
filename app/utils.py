# auth_app/utils.py

from typing import Dict, Union
import jwt
import os
from fastapi import UploadFile

from datetime import datetime
import shutil
# SECRET_KEY = os.environ.get("SECRET_KEY")
SECRET_KEY = "VpwI_yUDuQuhA1VEB0c0f9qki8JtLeFWh3lA5kKvyGnHxKrZ-M59cA"
ALGORITHM = "HS256"
SERVICES = {
    "userservice": "http://127.0.0.1:8001",
    "catalogservice": "https://catalogservice.inminternational.uz",
    "authservice": "https://authservice.inminternational.uz",
    "billingservice": "https://billingservice.inminternational.uz",
    "videoconversion": "http://127.0.0.1:8000"
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
AVATAR_DIR = os.path.join(MEDIA_ROOT, 'avatars')
MEDIA_URL = '/media/'

os.makedirs(AVATAR_DIR, exist_ok=True)


def decode_jwt_token(token: str) -> Dict[str, Union[str, int]]:
    """Decode and verify a JWT token."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# def construct_avatar_url(filename: str) -> str:
#     return f"https:/userservice.inminternational.uz/files/{filename}"


def construct_file_url(file_path: str) -> str:
    return f"{MEDIA_URL}{file_path}"


async def save_avatar_file(avatar: UploadFile) -> str:
    # Generate a unique file name, e.g., using the current timestamp
    file_extension = os.path.splitext(avatar.filename)[1]
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"

    file_location = os.path.join(AVATAR_DIR, unique_filename)
    with open(file_location, "wb") as file_object:
        # Use shutil to efficiently copy the file
        shutil.copyfileobj(avatar.file, file_object)

    # Return the relative path of the saved file
    print(os.path.join('avatars', unique_filename))
    return os.path.join('avatars', unique_filename)


async def delete_avatar_file(avatar_url: str):
    # Extract the filename from the URL
    filename = avatar_url.split("/")[-1]
    file_location = os.path.join(AVATAR_DIR, filename)

    # Check if the file exists and delete it
    if os.path.exists(file_location):
        os.remove(file_location)
