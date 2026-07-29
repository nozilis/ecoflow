import asyncio
import aio_pika
from decouple import config
import json
from database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_profile_consumer_core import UserProfileConsumerService

async def run_consumer(handlers: dict[str, callable]):
    connection = await aio_pika.connect_robust(
        f"amqp://{config('RABBITMQ_DEFAULT_USER')}:{config('RABBITMQ_DEFAULT_PASS')}@rabbitmq/"
    )

    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue('user_service.events', durable=True)

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

async def handle_user_created(
    data: dict, 
    session: AsyncSession
):
    user_profile_consumer_service = UserProfileConsumerService(data, session)
    await user_profile_consumer_service.handle_user_created()

if __name__ == "__main__":
    handlers = {
        'user.created': handle_user_created,
    }
    asyncio.run(run_consumer(handlers))