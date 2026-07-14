from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from database import async_session_maker
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from decouple import config
from fastapi import HTTPException, status, Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ALGORITHM = "HS256"

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
    
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    user_id = int(payload.get("sub"))
    return user_id