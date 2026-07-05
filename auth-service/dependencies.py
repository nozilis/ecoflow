from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_maker
from fastapi.security import OAuth2PasswordBearer 
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from decouple import config
from sqlalchemy import select
from models import User
from jwt_token import ALGORITHM

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, config('SECRET_KEY'), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_token(token)
    user_id = payload.get("sub")
    db_request = await db.execute(select(User).where(User.id == int(user_id)))
    db_user = db_request.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not found")
    return db_user