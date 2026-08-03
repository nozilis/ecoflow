from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_maker
from typing import AsyncGenerator
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from decouple import config
from fastapi import HTTPException, status, Depends, Request
from services.user_profile_core import UserProfileService
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_redis(request: Request):
    async with Redis(connection_pool=request.app.state.redis_pool) as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ALGORITHM = "HS256"

def decode_token(token: str):
    try:
        payload = jwt.decode(token, config('SECRET_KEY'), algorithms=[ALGORITHM])
        return payload
    except JWTError:    
        logger.warning('Failed to decode the token')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    user_id = int(payload.get("sub"))
    return user_id

def get_user_profile_service(
    db: AsyncSession = Depends(get_db),
    request_user: int = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> UserProfileService:
    return UserProfileService(db, request_user, redis)