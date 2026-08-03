import aio_pika
import asyncio
import json
from database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from services.notification_consumer_core import NotificationConsumerService
from rabbitmq_client import get_rabbitmq_connection

async def run_consumer(handlers: dict[str, callable]):
    connection = await get_rabbitmq_connection()

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

async def handle_user_created(
    data: dict, 
    session: AsyncSession
):
    notification_consumer_service = NotificationConsumerService(data, session)
    await notification_consumer_service.handle_user_created()

async def handle_user_updated(
    data: dict, 
    session: AsyncSession
):
    notification_consumer_service = NotificationConsumerService(data, session)
    await notification_consumer_service.handle_user_updated()

async def handle_user_deleted(
    data: dict, 
    session: AsyncSession
):
    notification_consumer_service = NotificationConsumerService(data, session)
    await notification_consumer_service.handle_user_deleted()

async def handle_budget_exceed(
    data: dict, 
    session: AsyncSession
):
    notification_consumer_service = NotificationConsumerService(data, session)
    await notification_consumer_service.handle_budget_exceed()

async def handle_settings_updated(
    data: dict, 
    session: AsyncSession
):
    notification_consumer_service = NotificationConsumerService(data, session)
    await notification_consumer_service.handle_settings_updated()

if __name__ == "__main__":
    handlers = {
        'user.created': handle_user_created,
        'user.updated': handle_user_updated,
        'user.deleted': handle_user_deleted,
        'budget.exceed': handle_budget_exceed,
        'user.settings.updated': handle_settings_updated,
    }
    asyncio.run(run_consumer(handlers))