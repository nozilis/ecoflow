import asyncio
import aio_pika
from decouple import config
import json
from database import async_session_maker
from datetime import datetime
from sqlalchemy import select
from models import MonthlyStats, UserBudget
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def run_consumer(handlers: dict[str, callable]):
    connection = await aio_pika.connect_robust(
        f"amqp://{config('RABBITMQ_DEFAULT_USER')}:{config('RABBITMQ_DEFAULT_PASS')}@rabbitmq/"
    )

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue("analytics_service.events", durable=True)

        for routing_key in handlers.keys():
            await queue.bind(exchange, routing_key=routing_key)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    handler = handlers.get(message.routing_key)
                    if handler:
                        async with async_session_maker() as session: 
                            await handler(data, session)

async def handle_transaction_created(data: dict, session: AsyncSession):
    date = datetime.fromisoformat(data['created_at'])
    year, month = date.year, date.month
    monthly_stats_is_exist = await session.execute(select(MonthlyStats).where(MonthlyStats.user_id == data['user_id'], MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == data['category']))
    db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
    if db_monthly_stats is None:
        db_monthly_stats = MonthlyStats(user_id = data['user_id'], year = year, month = month, category = data['category'], transaction_type = data['transaction_type'], total_amount = data['amount'])
        session.add(db_monthly_stats)
        logger.info('MonthlyStats object successfully created')
    else:
        db_monthly_stats.total_amount += data['amount']
        logger.info('Total amount successfully increased')
    await session.commit()

async def handle_transaction_updated(data: dict, session: AsyncSession):
    date = datetime.fromisoformat(data['created_at'])
    year, month = date.year, date.month
    monthly_stats_is_exist = await session.execute(select(MonthlyStats).where(MonthlyStats.user_id == data['user_id'], MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == data['category']))
    db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
    if db_monthly_stats:
        if data['recent_type'] == 'Income':
            old_impact = data['recent_amount']
        else:
            old_impact = -data['recent_amount']
        if data['transaction_type'] == 'Income':
            new_impact = data['amount']
        else:
            new_impact = -data['amount']
        db_monthly_stats.total_amount = db_monthly_stats.total_amount - old_impact + new_impact
        await session.commit()
        logger.info('MonthlyStats successfully updated')
    else:
        logger.info('MonthlyStats object not found')

async def handle_transaction_deleted(data: dict, session: AsyncSession):
    date = datetime.fromisoformat(data['created_at'])
    year, month = date.year, date.month
    monthly_stats_is_exist = await session.execute(select(MonthlyStats).where(MonthlyStats.user_id == data['user_id'], MonthlyStats.year == year, MonthlyStats.month == month, MonthlyStats.category == data['category']))
    db_monthly_stats = monthly_stats_is_exist.scalar_one_or_none()
    if db_monthly_stats:
        if data['transaction_type'] == 'Income':
            db_monthly_stats.total_amount -= data['amount']
        else:
            db_monthly_stats.total_amount += data['amount']
        await session.commit()
        logger.info('MonthlyStats successfully updated')
    else:
        logger.info('MonthlyStats object not found')

async def handle_budget_limit_updated(data: dict, session: AsyncSession):
    user_id, budget_limit = data['user_id'], data['budget_limit']
    user_budget_is_exist = await session.execute(select(UserBudget).where(UserBudget.user_id == user_id))
    db_user_budget = user_budget_is_exist.scalar_one_or_none()
    if db_user_budget is None:
        db_user_budget = UserBudget(user_id=user_id, budget_limit=budget_limit)
        session.add(db_user_budget)
        logger.info('Budget limit successfully added')
    else:
        db_user_budget.budget_limit = budget_limit
        logger.info('Budget limit successfully updated')
    await session.commit()

if __name__ == "__main__":
    tasks = [
        run_consumer({'transaction.created': handle_transaction_created}),
        run_consumer({'budget.limit_updated': handle_transaction_created})
    ]

    asyncio.run(asyncio.gather(*tasks))