from models import MonthlyStats, UserBudget
from publisher import publish_analytics_events
from sqlalchemy import select, func
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AnalyticsConsumerService:
    def __init__(self, data, session, redis):
        self.data = data
        self.session = session
        self.redis = redis

    async def handle_transaction_created(self, rabbitmq):
        date = datetime.fromisoformat(self.data['created_at'])
        year, month = date.year, date.month
        user_id, category, transaction_type, amount = self.data['user_id'], self.data['category'], self.data['transaction_type'], self.data['amount']
        monthly_stats_is_exist = await self.session.execute(select(MonthlyStats).where(MonthlyStats.user_id == user_id, MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == category))
        db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
        if db_monthly_stats is None:
            db_monthly_stats = MonthlyStats(user_id = user_id, year = year, month = month, category = category, transaction_type = transaction_type, total_amount = amount)
            self.session.add(db_monthly_stats)
            logger.info(f'MonthlyStats for user {user_id} successfully created')
        else:
            db_monthly_stats.total_amount += amount
            logger.info(f'Total amount for user {user_id} successfully increased')
        monthly_stats_total = await self.session.execute(select(func.sum(MonthlyStats.total_amount).label('monthly_stats_total')).where(MonthlyStats.user_id == user_id, MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.transaction_type == 'Expense'))
        user_budget_limit = await self.session.execute(select(UserBudget).where(UserBudget.user_id == user_id))
        db_monthly_stats_total = monthly_stats_total.scalar_one_or_none()
        db_user_budget_limit = user_budget_limit.scalar_one_or_none()
        if db_monthly_stats_total is None:
            logger.warning(f'User {user_id} transactions not found')
        if db_user_budget_limit is None:
            logger.warning(f'User {user_id} budget limit not found')
        if db_monthly_stats_total and db_user_budget_limit:
            if db_monthly_stats_total > db_user_budget_limit:
                await publish_analytics_events('exceed', user_id, rabbitmq, monthly_stats_total=db_monthly_stats_total, user_budget_limit=db_user_budget_limit)
                logger.info(f'User {user_id} budget exceed the limit event successfully published')
        await self.session.commit()
        await self.cache_delete_handle()

    async def handle_transaction_updated(self):
        date = datetime.fromisoformat(self.data['created_at'])
        year, month = date.year, date.month
        user_id, category, transaction_type, amount, recent_type, recent_amount = self.data['user_id'], self.data['category'], self.data['transaction_type'], self.data['amount'], self.data['recent_type'], self.data['recent_amount']
        monthly_stats_is_exist = await self.session.execute(select(MonthlyStats).where(MonthlyStats.user_id == user_id, MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == category))
        db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
        if db_monthly_stats:
            if recent_type == 'Income':
                old_impact = recent_amount
            else:
                old_impact = -recent_amount
            if transaction_type == 'Income':
                new_impact = amount
            else:
                new_impact = -amount
            db_monthly_stats.total_amount = db_monthly_stats.total_amount - old_impact + new_impact
            await self.session.commit()
            logger.info(f'MonthlyStats for user {user_id} successfully updated')
            await self.cache_delete_handle()
        else:
            logger.warning(f'MonthlyStats for user {user_id} not found')

    async def handle_transaction_deleted(self):
        date = datetime.fromisoformat(self.data['created_at'])
        year, month = date.year, date.month
        user_id, category, transaction_type, amount = self.data['user_id'], self.data['category'], self.data['transaction_type'], self.data['amount']
        monthly_stats_is_exist = await self.session.execute(select(MonthlyStats).where(MonthlyStats.user_id == user_id, MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == category))
        db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
        if db_monthly_stats:
            if transaction_type == 'Income':
                db_monthly_stats.total_amount -= amount
            else:
                db_monthly_stats.total_amount += amount
            await self.session.commit()
            logger.info(f'MonthlyStats for user {user_id} successfully updated')
            await self.cache_delete_handle()
        else:
            logger.warning(f'MonthlyStats for user {user_id} not found')

    async def handle_budget_limit_updated(self):
        user_id, budget_limit = self.data['user_id'], self.data['budget_limit']
        user_budget_is_exist = await self.session.execute(select(UserBudget).where(UserBudget.user_id == user_id))
        db_user_budget = user_budget_is_exist.scalar_one_or_none()
        if db_user_budget is None:
            db_user_budget = UserBudget(user_id=user_id, budget_limit=budget_limit)
            self.session.add(db_user_budget)
            logger.info(f'Budget limit for user {user_id} successfully added')
        else:
            db_user_budget.budget_limit = budget_limit
            logger.info(f'Budget limit for user {user_id} successfully updated')
        await self.session.commit()

    async def handle_user_deleted(self):
        user_id = self.data['user_id']
        user_monthly_stats_is_exist = await self.session.execute(select(MonthlyStats).where(MonthlyStats.user_id == user_id))
        user_budget_is_exist = await self.session.execute(select(UserBudget).where(UserBudget.user_id == user_id))
        db_user_monthly_stats = user_monthly_stats_is_exist.scalars().all()
        db_user_budget = user_budget_is_exist.scalar_one_or_none()
        if db_user_monthly_stats:
            for monthly_stats in db_user_monthly_stats:
                await self.session.delete(monthly_stats)
            logger.info(f'MonthlyStats for user {user_id} successfully deleted')
        if db_user_budget is not None:
            await self.session.delete(db_user_budget)
            logger.info(f'UserBudget for user {user_id} successfully deleted')
        await self.session.commit()
        async for cache_key in self.redis.scan_iter(match=f'*_stats:{user_id}:*'):
            await self.redis.delete(cache_key)
        logger.info(f'Cache for user {user_id} successfully deleted')

    async def cache_delete_handle(self):
        date = datetime.fromisoformat(self.data['created_at'])
        year, month = date.year, date.month
        user_id = self.data['user_id']
        monthly_cache_key = f'monthly_stats:{user_id}:{month}:{year}'
        await self.redis.delete(monthly_cache_key)
        logger.info(f'Cache with key {monthly_cache_key} successfully deleted')
        yearly_cache_key = f'yearly_stats:{user_id}:{year}'
        await self.redis.delete(yearly_cache_key)
        logger.info(f'Cache with key {yearly_cache_key} successfully deleted')
        transaction_point = year * 12 + month
        async for range_cache_key in self.redis.scan_iter(match=f'range_stats:{user_id}:*'):
            _, _, start, end = range_cache_key.split(':')
            if int(start) <= transaction_point <= int(end):
                await self.redis.delete(range_cache_key)
                logger.info(f'Cache with key {range_cache_key} successfully deleted')