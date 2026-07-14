from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Date, func, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date

class Base(DeclarativeBase):
    pass

class MonthlyStats(Base):
    __tablename__ = 'monthly_stats'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(25))
    transaction_type: Mapped[str] = mapped_column(String(25))
    total_amount: Mapped[int] = mapped_column(Integer)
    
    __table_args__ = (UniqueConstraint('user_id', 'year', 'month', 'category', name='month_category_agregation'))