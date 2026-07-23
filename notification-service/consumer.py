import aio_pika
import asyncio
import json
from database import async_session_maker
from decouple import config
from sqlalchemy import select
from models import UserContact, NotificationSettings
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

        queue = await channel.declare_queue('notification_service.events', durable=True)

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
    user_id, email, username = data['id'], data['username'], data['email']
    user_contact_is_exist = await session.execute(select(UserContact).where(UserContact.username == username))
    db_user_contact = user_contact_is_exist.scalar_one_or_none()
    if db_user_contact is None:
        create_user_contact = UserContact(user_id = user_id, email = email, username = username)
        create_notification_settings = NotificationSettings(user_id = user_id)
        session.add(create_user_contact)
        session.add(create_notification_settings)
        await session.commit()
        logger.info(f"User {username} successfully created")
    else:
        logger.info(f"User {username} already exists in UserContact, skipping")
    

if __name__ == "__main__":
    tasks = [
        run_consumer({'user.created': handle_user_created})
    ]
    
    asyncio.run(asyncio.gather(*tasks))