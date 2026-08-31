from models import UserContact, NotificationSettings, NotificationLog
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class NotificationConsumerService:
    def __init__(self, data, session):
        self.data = data
        self.session = session

    async def handle_user_created(self):
        user_id, email, username = self.data['user_id'], self.data['email'], self.data['username']
        user_contact_is_exist = await self.session.execute(select(UserContact).where(UserContact.user_id == user_id))
        db_user_contact = user_contact_is_exist.scalar_one_or_none()
        if db_user_contact is None:
            create_user_contact = UserContact(user_id = user_id, email = email, username = username)
            create_notification_settings = NotificationSettings(user_id = user_id)
            self.session.add(create_user_contact)
            self.session.add(create_notification_settings)
            await self.session.commit()
            logger.info(f"User {user_id} successfully created")
        else:
            logger.warning(f"User {user_id} already exists in UserContact, skipping")

    async def handle_user_updated(self):
        user_id, email, username = self.data['user_id'], self.data.get('email'), self.data.get('username')
        user_contact_is_exist = await self.session.execute(select(UserContact).where(UserContact.user_id == user_id))
        db_user_contact = user_contact_is_exist.scalar_one_or_none()
        if db_user_contact is None:
            logger.warning(f'User {user_id} not found')
        else:
            if username:
                db_user_contact.username = username
            if email:
                db_user_contact.email = email
            await self.session.commit()
            logger.info(f'User {user_id} successfully updated')

    async def handle_user_deleted(self):
        user_id = self.data['user_id']
        user_contact_is_exist = await self.session.execute(select(UserContact).where(UserContact.user_id == user_id))
        db_user_contact = user_contact_is_exist.scalar_one_or_none()
        if db_user_contact is None:
            logger.warning(f'User {user_id} not found')
        else:
            await self.session.delete(db_user_contact)
            await self.session.commit()
            logger.info(f'User {user_id} successfully deleted')

    async def handle_budget_exceed(self):
        user_id, monthly_stats_total, user_budget_limit = self.data['user_id'], self.data['monthly_stats_total'], self.data['user_budget_limit']
        difference = monthly_stats_total - user_budget_limit
        username = await self.session.execute(select(UserContact.username).where(UserContact.user_id == user_id))
        db_username = username.scalar_one_or_none()
        if db_username is None:
            logger.warning(f'User {user_id} not found')
        else:
            notification_topic = 'Budget exceed'
            notification_message = f'Hello, {db_username}, your spending has exceeded the expected limit by {difference}'
            logger.info('*Sending email*')
            logger.info(f'Email was successfully sended to user {user_id}')
            notification_log = NotificationLog(user_id = user_id, notification_topic = notification_topic, notification_message = notification_message)
            self.session.add(notification_log)
            await self.session.commit()
            logger.info('Notification log was successfully created')

    async def handle_settings_updated(self):
        user_id, monthly_budget_exceeded_notification, weekly_summary_notification = self.data['user_id'], self.data.get('monthly_budget_exceeded_notification'), self.data.get('weekly_summary_notification')
        notification_settings_is_exist = await self.session.execute(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        db_notification_settings = notification_settings_is_exist.scalar_one_or_none()
        if db_notification_settings is None:
            logger.warning(f'Settings user {user_id} not found')
        else:
            if monthly_budget_exceeded_notification is not None:
                db_notification_settings.monthly_budget_exceeded_notification = monthly_budget_exceeded_notification
            if weekly_summary_notification is not None:
                db_notification_settings.weekly_summary_notification = weekly_summary_notification
            await self.session.commit()
            logger.info(f'Settings for user {user_id} successfully updated')