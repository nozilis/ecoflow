from fastapi import APIRouter, Depends, status, HTTPException
from dependencies import get_user_profile_service
from schemas import UserProfileResponse, UserProfileUpdate
from services.user_profile_core import UserProfileService, UserProfileNotFound, UsernameConflict, EmailConflict, UsernameAndEmailConflict

router = APIRouter(
    prefix='/user_profile',
    tags=['user_profile']
)

@router.get('/', status_code=status.HTTP_200_OK)
async def get_user_profile(
    user_id: int = None, 
    user_profile_service: UserProfileService = Depends(get_user_profile_service)
) -> UserProfileResponse:
    try:
        user_profile = await user_profile_service.get_user_profile(user_id=user_id)
        return user_profile
    except UserProfileNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{exc}')

@router.patch('/', status_code=status.HTTP_200_OK)
async def update_user_profile(
    user_profile_update_request: UserProfileUpdate, 
    user_profile_service: UserProfileService = Depends(get_user_profile_service)
) -> UserProfileResponse:
    try:
        user_profile = await user_profile_service.update_user_profile(user_profile_update_request=user_profile_update_request)
        return UserProfileResponse.model_validate(user_profile)
    except UserProfileNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{exc}')
    except UsernameConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')
    except EmailConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')
    except UsernameAndEmailConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')

@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
    user_profile_service: UserProfileService = Depends(get_user_profile_service)
):
    try:
        await user_profile_service.delete_user_profile()
    except UserProfileNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{exc}')