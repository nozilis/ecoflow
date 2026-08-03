import asyncio
import aio_pika
import json
from database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from services.analytics_consumer_core import AnalyticsConsumerService
from redis.asyncio import Redis
from redis_client import redis_pool
from rabbitmq_client import get_rabbitmq_connection
from aio_pika import RobustConnection

async def run_consumer(handlers: dict[str, callable]):
    connection = await get_rabbitmq_connection()

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue("analytics_service.events", durable=True)

        for routing_key in handlers.keys():
            await queue.bind(exchange, routing_key=routing_key)

        redis_client = Redis(connection_pool=redis_pool, decode_responses=True)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    handler = handlers.get(message.routing_key)
                    if handler:
                        async with async_session_maker() as session: 
                            await handler(data, session, redis_client, connection)

async def handle_transaction_created(
    data: dict,
    session: AsyncSession,
    redis: Redis,
    rabbitmq: RobustConnection
):
    analytics_consumer_service = AnalyticsConsumerService(data, session, redis)
    await analytics_consumer_service.handle_transaction_created(rabbitmq)

async def handle_transaction_updated(
    data: dict, 
    session: AsyncSession,
    redis: Redis
):
    analytics_consumer_service = AnalyticsConsumerService(data, session, redis)
    await analytics_consumer_service.handle_transaction_updated()

async def handle_transaction_deleted(
    data: dict, 
    session: AsyncSession,
    redis: Redis
):
    analytics_consumer_service = AnalyticsConsumerService(data, session, redis)
    await analytics_consumer_service.handle_transaction_deleted()

async def handle_budget_limit_updated(
    data: dict, 
    session: AsyncSession,
    redis: Redis
):
    analytics_consumer_service = AnalyticsConsumerService(data, session, redis)
    await analytics_consumer_service.handle_budget_limit_updated()

async def handle_user_deleted(
    data: dict, 
    session: AsyncSession,
    redis: Redis
):
    analytics_consumer_service = AnalyticsConsumerService(data, session, redis)
    await analytics_consumer_service.handle_user_deleted()

if __name__ == "__main__":
    handlers = {
        'transaction.created': handle_transaction_created,
        'transaction.updated': handle_transaction_updated,
        'transaction.deleted': handle_transaction_deleted,
        'budget.limit_updated': handle_budget_limit_updated,
        'user.deleted': handle_user_deleted,
    }
    asyncio.run(run_consumer(handlers))