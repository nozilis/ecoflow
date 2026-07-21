from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db, get_current_user
from sqlalchemy import select
from models import UserProfile
from schemas import UserProfileResponse, UserProfileUpdate
from enums import VisibilityChoice

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
    user_profile_update_dump = user_profile_update_request.model_dump(exclude_unset=True).items()
    for item, value in user_profile_update_dump:
        setattr(db_user_profile, item, value)
    await db.commit()
    return UserProfileResponse.model_validate(db_user_profile)