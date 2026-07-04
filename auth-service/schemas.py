from pydantic import BaseModel, model_validator, EmailStr, ConfigDict
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    confirm_password: str
    email: EmailStr

    @model_validator(mode='before')
    @classmethod
    def check_password_match(cls, data: dict):
        if data['password'] != data['confirm_password']:
            raise ValueError('Поля регистрации заполнены неверно!')
        return data
    
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    registered_at: datetime

class UserLogin(BaseModel):
    username: str
    password: str