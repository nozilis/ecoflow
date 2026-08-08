import asyncio
import aio_pika
import json
from database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from services.transaction_consumer_core import TransactionConsumerService
from rabbitmq_client import get_rabbitmq_connection
from redis.asyncio import Redis
from redis_client import redis_pool
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 5

async def run_consumer(handlers: dict[str, callable]):
    connection = await get_rabbitmq_connection()

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)
        dl_exchange = await channel.declare_exchange("retry_ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue(
            "transaction_service.events", 
            durable=True, 
            arguments={
                'x-dead-letter-exchange': 'retry_ecoflow_events'
            }
        )
        dl_queue = await channel.declare_queue(
            "transaction_service.retry_queue", 
            durable=True,
            arguments={
                'x-message-ttl': 5000,
                'x-dead-letter-exchange': 'ecoflow_events'
            }
        )
        final_dl_queue = await channel.declare_queue(
            "transaction_service.dl_queue", durable=True
        )

        for routing_key in handlers.keys():
            await queue.bind(exchange, routing_key=routing_key)
            await dl_queue.bind(dl_exchange, routing_key=routing_key)

        redis_client = Redis(connection_pool=redis_pool, decode_responses=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    handler = handlers.get(message.routing_key)
                    if handler:
                        headers = message.headers or {}
                        death_info = headers.get('x-death')
                        retry_count = death_info[0].get('count') if death_info else 0
                        try:
                            async with async_session_maker() as session:
                                await handler(data, session, redis_client)
                        except Exception as exc:
                            if retry_count >= MAX_RETRIES:
                                logger.error(f'Message exceeded retry limit, sending to DLQ: {exc}')
                                await channel.default_exchange.publish(
                                    aio_pika.Message(body=message.body, headers=message.headers),
                                    routing_key='transaction_service.dl_queue'
                                )
                            else:
                                raise

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