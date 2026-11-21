import logging
from collections.abc import AsyncGenerator

from aio_pika import RobustConnection
from database import async_session_maker
from decouple import config
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jwt_token import ALGORITHM
from models import User
from services.auth_core import AuthService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_rabbitmq(request: Request):
    yield request.app.state.rabbitmq_connection


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')


def decode_token(token: str):
    try:
        payload = jwt.decode(token, config('SECRET_KEY'), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        logger.warning('Failed to decode the token')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_token(token)
    user_id = payload.get('sub')
    db_request = await db.execute(select(User).where(User.id == int(user_id)))
    db_user = db_request.scalar_one_or_none()
    if db_user is None:
        logger.warning(f'User {user_id} not found')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return db_user


def get_auth_service(
    db: AsyncSession = Depends(get_db), rabbitmq: RobustConnection = Depends(get_rabbitmq)
) -> AuthService:
    return AuthService(db, rabbitmq)
