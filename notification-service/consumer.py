import aio_pika
import asyncio
import json
from database import async_session_maker
from decouple import config
from sqlalchemy import select
from models import UserContact, NotificationSettings, NotificationLog
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

async def handle_user_updated(data: dict, session: AsyncSession):
    user_id, username, email = data['user_id'], data.get('username'), data.get('email')
    user_contact_is_exist = await session.execute(select(UserContact).where(UserContact.user_id == user_id))
    db_user_contact = user_contact_is_exist.scalar_one_or_none()
    if db_user_contact is None:
        logger.info('User not found')
    else:
        if username:
            db_user_contact.username = username
        if email:
            db_user_contact.email = email
        await session.commit()
        logger.info('User successfully updated')

async def handle_user_deleted(data: dict, session: AsyncSession):
    user_id = data['user_id']
    user_contact_is_exist = await session.execute(select(UserContact).where(UserContact.user_id == user_id))
    db_user_contact = user_contact_is_exist.scalar_one_or_none()
    if db_user_contact is None:
            logger.info('User not found')
    else:
        await session.delete(db_user_contact)
        await session.commit()

async def handle_budget_exceed(data: dict, session: AsyncSession):
    user_id, monthly_stats_total, user_budget_limit = data['user_id'], data['monthly_stats_total'], data['user_budget_limit']
    difference = monthly_stats_total - user_budget_limit
    username = await session.execute(select(UserContact.username).where(UserContact.user_id == user_id))
    db_username = username.scalar_one_or_none()
    if db_username is None:
        logger.info('User not found')
    else:
        notification_topic = 'Budget exceed'
        notification_message = f'Hello, {db_username}, your spending has exceeded the expected limit by {difference}'
        print('*Sending email*')
        logger.info('Email was successfully sended')
        notification_log = NotificationLog(user_id = user_id, notification_topic = notification_topic, notification_message = notification_message)
        session.add(notification_log)
        await session.commit()
        logger.info('Notification log was successfully created')

async def handle_settings_updated(data: dict, session: AsyncSession):
    user_id, monthly_budget_exceeded_notification, weekly_summary_notification = data['user_id'], data.get('monthly_budget_exceeded_notification'), data.get('weekly_summary_notification')
    notification_settings_is_exist = await session.execute(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
    db_notification_settings = notification_settings_is_exist.scalar_one_or_none()
    if db_notification_settings is None:
        logger.info('Settings not found')
    else:
        if monthly_budget_exceeded_notification is not None:
            db_notification_settings.monthly_budget_exceeded_notification = monthly_budget_exceeded_notification
        if weekly_summary_notification is not None:
            db_notification_settings.weekly_summary_notification = weekly_summary_notification
        await session.commit()
        logger.info('Settings successfully updated')

if __name__ == "__main__":
    handlers = {
        'user.created': handle_user_created,
        'user.updated': handle_user_updated,
        'user.deleted': handle_user_deleted,
        'budget.exceed': handle_budget_exceed,
        'user.settings.updated': handle_settings_updated,
    }
    asyncio.run(run_consumer(handlers))