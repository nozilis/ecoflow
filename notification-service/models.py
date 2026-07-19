from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, ForeignKey

class Base(DeclarativeBase):
    pass

class UserContact(Base):
    __tablename__ = 'user_contact'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

class NotificationSettings(Base):
    __tablename__ = 'notifications_settings'

    user_id: Mapped[int] = mapped_column(ForeignKey('user_contact.user_id', ondelete='CASCADE'), primary_key=True)
    monthly_budget_exceeded_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_summary_notification: Mapped[bool] = mapped_column(Boolean, default=True)