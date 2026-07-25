import asyncio
import aio_pika
from decouple import config
import json
from database import async_session_maker
import logging
from sqlalchemy import select
from models import User
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

async def handle_user_updated(data: dict, session: AsyncSession):
    user_id, username, email = data['user_id'], data.get('username'), data.get('email')
    user_is_exist = await session.execute(select(User).where(User.id == user_id))
    db_user = user_is_exist.scalar_one_or_none()
    if db_user is None:
        logger.warning(f'User {user_id} not found')
    else:
        if username:
            db_user.username = username
        if email:
            db_user.email = email
        await session.commit()
        logger.info('User successfully updated')

async def handle_user_deleted(data: dict, session: AsyncSession):
    user_id = data['user_id']
    user_is_exist = await session.execute(select(User).where(User.id == user_id))
    db_user = user_is_exist.scalar_one_or_none()
    if db_user is None:
        logger.warning(f'User {user_id} not found')
    else:
        await session.delete(db_user)
        await session.commit()
        logger.info('User successfully deleted')

if __name__ == '__main__':
    handlers = {
        'user.updated': handle_user_updated,
        'user.deleted': handle_user_deleted,
    }
    asyncio.run(run_consumer(handlers))