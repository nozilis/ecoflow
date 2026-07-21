from pydantic import BaseModel, ConfigDict
from enums import VisibilityChoice
from typing import Optional

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: str
    avatar: str
    social_links: dict
    visibility_choice: VisibilityChoice

class UserProfileUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    avatar: Optional[str]
    social_links: Optional[dict] 
    visibility_choice: Optional[VisibilityChoice]