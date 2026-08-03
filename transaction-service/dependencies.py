from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends, Request
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from database import async_session_maker
from services import TransactionService
from redis.asyncio import Redis
from aio_pika import RobustConnection
import logging

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]: 
    async with async_session_maker() as session:
        yield session

async def get_redis(request: Request):
    async with Redis(connection_pool=request.app.state.redis_pool) as session:
        yield session

async def get_rabbitmq(request: Request):
    yield request.app.state.rabbitmq_connection

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

def get_transaction_service(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    rabbitmq: RobustConnection = Depends(get_rabbitmq)
) -> TransactionService:
    return TransactionService(db, user_id, redis, rabbitmq)