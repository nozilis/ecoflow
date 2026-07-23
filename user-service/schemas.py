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
    username: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    social_links: Optional[dict] = None
    visibility_choice: Optional[VisibilityChoice] = None