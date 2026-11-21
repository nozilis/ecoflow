
from enums import VisibilityChoice
from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: str
    avatar: str
    budget_limit: int
    social_links: dict
    visibility_choice: VisibilityChoice
    monthly_budget_exceeded_notification: bool
    weekly_summary_notification: bool


class UserProfileUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    avatar: str | None = None
    budget_limit: int | None = None
    social_links: dict | None = None
    visibility_choice: VisibilityChoice | None = None
    monthly_budget_exceeded_notification: bool | None = None
    weekly_summary_notification: bool | None = None
