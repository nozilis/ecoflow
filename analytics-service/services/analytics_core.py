from models import MonthlyStats
from sqlalchemy import select, func
from datetime import datetime
from schemas import MonthlyStatsResponse, YearlyStatsResponse, RangeStatsResponse
import json

class AnalyticsService:
    def __init__(self, db, user_id, redis):
        self.db = db
        self.user_id = user_id
        self.redis = redis

    async def get_monthly_stats(self, month, year):
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        cache_key = f'monthly_stats:{self.user_id}:{month}:{year}'
        cached_data = await self.redis.get(cache_key)
        if cached_data is not None:
            data = json.loads(cached_data)
            return data
        monthly_stats = await self.db.execute(select(MonthlyStats).where(MonthlyStats.user_id == self.user_id, MonthlyStats.month == month, MonthlyStats.year == year))
        db_monthly_stats = monthly_stats.scalars().all()
        validated_data = [MonthlyStatsResponse.model_validate(item).model_dump() for item in db_monthly_stats]
        data_to_cache = json.dumps(validated_data)
        await self.redis.set(cache_key, data_to_cache, 300)
        return validated_data

    async def get_yearly_stats(self, year):
        now = datetime.now()
        year = year or now.year
        cache_key = f'yearly_stats:{self.user_id}:{year}'
        cached_data = await self.redis.get(cache_key)
        if cached_data is not None:
            data = json.loads(cached_data)
            return data
        yearly_stats = await self.db.execute(select(MonthlyStats.year, MonthlyStats.category, func.sum(MonthlyStats.total_amount).label('total_year_amount')).where(MonthlyStats.year == year, MonthlyStats.user_id == self.user_id).group_by(MonthlyStats.year, MonthlyStats.category))
        db_yearly_stats = yearly_stats.mappings().all()
        validated_data = [YearlyStatsResponse.model_validate(item).model_dump() for item in db_yearly_stats]
        data_to_cache = json.dumps(validated_data)
        await self.redis.set(cache_key, data_to_cache, 300)
        return validated_data

    async def get_range_stats(self, start_year, start_month, end_year, end_month):
        now = datetime.now()
        start_year = start_year or now.year
        end_year = end_year or now.year
        start_month = start_month or now.month
        end_month = end_month or now.month
        start = start_year * 12 + start_month
        end = end_year * 12 + end_month
        cache_key = f'range_stats:{self.user_id}:{start}:{end}'
        cached_data = await self.redis.get(cache_key)
        if cached_data is not None:
            data = json.loads(cached_data)
            return data
        range_stats = await self.db.execute(select(MonthlyStats.category, func.sum(MonthlyStats.total_amount).label('total_range_amount')).where(MonthlyStats.user_id == self.user_id, (start, end)).group_by(MonthlyStats.category))
        db_range_stats = range_stats.mappings().all()
        validated_data = [RangeStatsResponse.model_validate(item).model_dump() for item in db_range_stats]
        data_to_cache = json.dumps(validated_data)
        await self.redis.set(cache_key, data_to_cache, 300)
        return validated_data