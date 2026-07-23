from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db, get_current_user
from sqlalchemy import select
from models import UserProfile
from schemas import UserProfileResponse, UserProfileUpdate
from enums import VisibilityChoice
from publisher import publish_user_updated, publish_user_deleted
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/user_profile',
    tags=['user_profile']
)

@router.get('/', status_code=status.HTTP_200_OK)
async def get_user_profile(user_id: int = None, db: AsyncSession = Depends(get_db), request_user: int = Depends(get_current_user)):
    if user_id is None:
        user_id = request_user
    user_profile_is_exist = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    db_user_profile = user_profile_is_exist.scalar_one_or_none()
    if db_user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    else:
        if db_user_profile.visibility_choice == VisibilityChoice.PRIVATE and request_user != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
        return UserProfileResponse.model_validate(db_user_profile)

@router.patch('/', status_code=status.HTTP_200_OK)
async def update_user_profile(user_profile_update_request: UserProfileUpdate, db: AsyncSession = Depends(get_db), request_user: int = Depends(get_current_user)):
    user_profile_is_exist = await db.execute(select(UserProfile).where(UserProfile.user_id == request_user))
    db_user_profile = user_profile_is_exist.scalar_one_or_none()
    if db_user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    user_profile_update_dump = user_profile_update_request.model_dump(exclude_unset=True)
    if user_profile_update_dump.get('username') is not None:
        username_is_already_exist = await db.execute(select(UserProfile).where(UserProfile.username == user_profile_update_dump.get('username')))
        db_username_is_already_exist = username_is_already_exist.scalar_one_or_none()
        if db_username_is_already_exist is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username is already exist')
    if user_profile_update_dump.get('email') is not None:
        email_is_already_exist = await db.execute(select(UserProfile).where(UserProfile.email == user_profile_update_dump.get('email')))
        db_email_is_already_exist = email_is_already_exist.scalar_one_or_none()
        if db_email_is_already_exist is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email is already exist')
    user_profile_update_dump_items = user_profile_update_dump.items()
    for item, value in user_profile_update_dump_items:
        setattr(db_user_profile, item, value)
    try:
        await db.commit()
        await publish_user_updated(request_user, user_profile_update_request.username, user_profile_update_request.email)
        return UserProfileResponse.model_validate(db_user_profile)
    except IntegrityError as e:
        pg_code = e.orig.diag.message_detail
        await db.rollback()
        print(f'{pg_code}')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Username or email is already taken')

@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(db: AsyncSession = Depends(get_db), request_user: int = Depends(get_current_user)):
    user_profile_is_exist = await db.execute(select(UserProfile).where(UserProfile.user_id == request_user))
    db_user_profile = user_profile_is_exist.scalar_one_or_none()
    if db_user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    await db.delete(db_user_profile)
    await db.commit()
    await publish_user_deleted(request_user)