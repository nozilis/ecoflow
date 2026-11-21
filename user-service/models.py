from enums import VisibilityChoice
from sqlalchemy import JSON, Boolean, Enum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    avatar: Mapped[str] = mapped_column(String(300), nullable=True)
    biography: Mapped[str] = mapped_column(String(750), nullable=True)
    budget_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    social_links: Mapped[dict[str, str]] = mapped_column(JSON, nullable=True)
    visibility_choice: Mapped[VisibilityChoice] = mapped_column(
        Enum(VisibilityChoice), default=VisibilityChoice.PRIVATE
    )
    monthly_budget_exceeded_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_summary_notification: Mapped[bool] = mapped_column(Boolean, default=True)
