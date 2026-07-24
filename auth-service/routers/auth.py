from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from schemas import UserCreate, UserResponse, UserLogin
from dependencies import get_db, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt
from models import User
from sqlalchemy import select, or_
from jwt_token import create_access_token
from publisher import publish_user_events

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = bcrypt.hash(user.password)
    user_is_exist = await db.execute(select(User).where(or_(User.username == user.username, User.email == user.email)))
    db_user = user_is_exist.scalar_one_or_none()
    if db_user is None:
        create_user = User(username = user.username, hashed_password = hashed_password, email = user.email)
        try:
            db.add(create_user)
            await db.commit()
            await publish_user_events('created', create_user.id, username=user.username, email=user.email, created_at=create_user.created_at)
            return UserResponse.model_validate(create_user)
        except IntegrityError as e:
            pg_code = e.orig.diag.message_detail
            await db.rollback()
            print(f'{pg_code}')
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Username or email is already taken')
    elif db_user.username == user.username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Username is already taken')
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Email is already taken')

@router.post('/login', status_code=status.HTTP_200_OK)
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    user_is_exist = await db.execute(select(User).where(User.username == user.username))
    db_user = user_is_exist.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')
    elif bcrypt.verify(user.password, db_user.hashed_password):
        return create_access_token({'sub': str(db_user.id)})
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')
    
@router.get('/whoami', status_code=status.HTTP_200_OK)
async def check_user(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)