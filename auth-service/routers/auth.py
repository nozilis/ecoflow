from fastapi import APIRouter, HTTPException, status, Depends
from schemas import UserCreate, UserResponse, UserLogin
from dependencies import get_auth_service, get_current_user
from models import User
from services.auth_core import AuthService, UsernameAndEmailConflict, UsernameConflict, EmailConflict, InvalidUsernameOrPassword
from typing import NewType

AccessToken = NewType('AccessToken', str)

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate, 
    auth_service: AuthService = Depends(get_auth_service)
    ) -> UserResponse:
    try:
        created_user = await auth_service.register_user(user)
        return UserResponse.model_validate(created_user)
    except UsernameAndEmailConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')
    except UsernameConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')
    except EmailConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'{exc}')

@router.post('/login', status_code=status.HTTP_200_OK)
async def login_user(
    user: UserLogin, 
    auth_service: AuthService = Depends(get_auth_service)
) -> AccessToken:
    try:
        access_token = await auth_service.login_user(user)
        return access_token
    except InvalidUsernameOrPassword as exc:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'{exc}')
    
@router.get('/whoami', status_code=status.HTTP_200_OK)
async def check_user(
    user: User = Depends(get_current_user)
) -> UserResponse:
    return UserResponse.model_validate(user)