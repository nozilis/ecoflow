from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, ForeignKey, DateTime, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UserContact(Base):
    __tablename__ = 'user_contacts'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

class NotificationSettings(Base):
    __tablename__ = 'notifications_settings'

    user_id: Mapped[int] = mapped_column(ForeignKey('user_contact.user_id', ondelete='CASCADE'), primary_key=True)
    monthly_budget_exceeded_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_summary_notification: Mapped[bool] = mapped_column(Boolean, default=True)

class NotificationLog(Base):
    __tablename__ = 'notifications_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user_contact.user_id'))
    notification_topic: Mapped[str] = mapped_column(String(200))
    notification_message: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())