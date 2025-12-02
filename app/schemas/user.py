from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models.user import Role

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[Role] = Role.EMPLOYEE

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class UserResponse(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None
    model_config = ConfigDict(extra='allow')
