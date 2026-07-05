from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from decouple import config
from fastapi.security import OAuth2PasswordBearer

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