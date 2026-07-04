from pydantic import BaseModel, model_validator, EmailStr

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