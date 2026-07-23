import asyncio
import aio_pika
from decouple import config
import json
from database import async_session_maker
import logging
from sqlalchemy import select
from models import UserProfile
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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

async def handle_user_created(data: dict, session: AsyncSession):
    user_id, username, email = data['id'], data['username'], data['email']
    user_profile_is_exist = await session.execute(select(UserProfile).where(UserProfile.username == username))
    db_user_profile = user_profile_is_exist.scalar_one_or_none()
    if db_user_profile is None:
        create_user_profile = UserProfile(user_id = user_id, username = username, email = email)
        session.add(create_user_profile)
        await session.commit()
        logger.info(f'User profile for user {username} successfully created')
    else:
        logger.info(f"User profile for user {username} already exists in UserProfile, skipping")

if __name__ == "__main__":
    tasks = [
        run_consumer({'user.created': handle_user_created})
    ]

    asyncio.run(asyncio.gather(*tasks))