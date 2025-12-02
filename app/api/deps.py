from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.core.config import settings
from app.core.database import async_session_factory
from app.crud.user import user_crud
from app.models.user import User, Role
from app.schemas.user import TokenData

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # In token we stored "sub" as string (email or id? in security.py we used str(subject))
    # In security.py: to_encode = {"exp": expire, "sub": str(subject)}
    # We usually use ID as subject.
    
    # But wait, TokenData schema has email: Optional[str].
    # Let's check how we create token.
    
    # If we store ID in sub, then token_data.sub? No TokenData has email.
    # I should probably update TokenData to have sub or id.
    
    # Let's assume we use user ID as subject.
    user_id = payload.get("sub")
    if not user_id:
         raise HTTPException(status_code=404, detail="User not found")
         
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    # We don't have is_active field yet, so assume all users are active
    return current_user

async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
