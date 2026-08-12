from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfileType(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    PATIENT = "PATIENT"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    profile_type: UserProfileType = UserProfileType.PATIENT

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str

    class Config:
        from_attributes = True
