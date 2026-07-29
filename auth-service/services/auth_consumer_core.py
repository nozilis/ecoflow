from models import User
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class AuthConsumerService:
    def __init__(self, data, session):
        self.data = data
        self.session = session

    async def handle_user_updated(self):
        user_id, username, email = self.data['user_id'], self.data.get('username'), self.data.get('email')
        user_is_exist = await self.session.execute(select(User).where(User.id == user_id))
        db_user = user_is_exist.scalar_one_or_none()
        if db_user is None:
            logger.warning(f'User {user_id} not found')
        else:
            if username:
                db_user.username = username
            if email:
                db_user.email = email
            await self.session.commit()
            logger.info(f'User {user_id} successfully updated')

    async def handle_user_deleted(self):
        user_id = self.data['user_id']
        user_is_exist = await self.session.execute(select(User).where(User.id == user_id))
        db_user = user_is_exist.scalar_one_or_none()
        if db_user is None:
            logger.warning(f'User {user_id} not found')
        else:
            await self.session.delete(db_user)
            await self.session.commit()
            logger.info(f'User {user_id} successfully deleted')