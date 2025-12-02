from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from fastapi import Request

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud.user import user_crud
from app.schemas.user import Token, UserResponse, UserCreate
from app.models.user import Role

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await user_crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/debug-token")
async def debug_token(
    request: Request,
    token: str = Depends(deps.reusable_oauth2),
):
    return {"auth_header": request.headers.get("authorization"), "token": token}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.post("/dev-login", response_model=Token)
async def dev_login(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Development only: Login as admin without password
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Not allowed in production")
        
    # Get or create admin
    email = "admin@crm.com"
    user = await user_crud.get_by_email(db, email=email)
    if not user:
        user_in = UserCreate(
            email=email,
            password="admin123456",
            name="Admin User",
            role=Role.ADMIN
        )
        user = await user_crud.create(db, obj_in=user_in)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
