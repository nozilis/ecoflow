from datetime import datetime

from enums import GeneralCategories, TransactionType
from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    category: Mapped[str] = mapped_column(Enum(GeneralCategories()))
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
