from pydantic import BaseModel, ConfigDict
from enums import VisibilityChoice

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: str
    avatar: str
    social_links: dict
    visibility_choice: VisibilityChoice