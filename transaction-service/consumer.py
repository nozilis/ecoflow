import asyncio
import aio_pika
import json
from database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from services.transaction_consumer_core import TransactionConsumerService
from rabbitmq_client import get_rabbitmq_connection
from redis.asyncio import Redis
from redis_client import redis_pool

async def run_consumer(handlers: dict[str, callable]):
    connection = await get_rabbitmq_connection()

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue("transaction_service.events", durable=True)

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
                            await handler(data, session, redis_client)

async def handle_user_deleted(
    data: dict,
    session: AsyncSession,
    redis: Redis
):
    transaction_consumer_service = TransactionConsumerService(data, session, redis)
    await transaction_consumer_service.handle_user_deleted()

if __name__ == "__main__":
    handlers = {
        'user.deleted': handle_user_deleted,
    }
    asyncio.run(run_consumer(handlers))