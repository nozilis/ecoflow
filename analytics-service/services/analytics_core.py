from models import MonthlyStats
from sqlalchemy import select, func
from datetime import datetime

class AnalyticsService:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    async def get_monthly_stats(self, month, year):
        now = datetime.now()
        if month is None:
           month = now.month
        if year is None:
            year = now.year
        monthly_stats = await self.db.execute(select(MonthlyStats).where(MonthlyStats.user_id == self.user_id, MonthlyStats.month == month, MonthlyStats.year == year))
        db_monthly_stats = monthly_stats.scalars().all()
        return db_monthly_stats

    async def get_yearly_stats(self, year):
        now = datetime.now()
        if year is None:
            year = now.year
        db_yearly_stats = await self.db.execute(select(MonthlyStats.year, MonthlyStats.category, func.sum(MonthlyStats.total_amount).label('total_year_amount')).where(MonthlyStats.year == year, MonthlyStats.user_id == self.user_id).group_by(MonthlyStats.year, MonthlyStats.category))
        return db_yearly_stats

    async def get_range_stats(self, start_year, start_month, end_year, end_month):
        now = datetime.now()
        if start_year is None:
            start_year = now.year
        if end_year is None:
            end_year = now.year
        if start_month is None:
            start_month = now.month
        if end_month is None:
            end_month = now.month
        db_range_stats = await self.db.execute(select(MonthlyStats.category, func.sum(MonthlyStats.total_amount).label('total_range_amount')).where(MonthlyStats.user_id == self.user_id, (MonthlyStats.year * 12 + MonthlyStats.month).between(start_year * 12 + start_month, end_year * 12 + end_month)).group_by(MonthlyStats.category))
        return db_range_stats