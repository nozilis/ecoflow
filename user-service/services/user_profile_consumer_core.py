from models import UserProfile
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class UserProfileConsumerService:
    def __init__(self, data, session):
        self.data = data
        self.session = session

    async def handle_user_created(self):
        user_id, username, email = self.data['id'], self.data['username'], self.data['email']
        user_profile_is_exist = await self.session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        db_user_profile = user_profile_is_exist.scalar_one_or_none()
        if db_user_profile is None:
            create_user_profile = UserProfile(user_id = user_id, username = username, email = email)
            self.session.add(create_user_profile)
            await self.session.commit()
            logger.info(f'User profile for user {username} successfully created')
        else:
            logger.warning(f"User profile for user {username} already exists in UserProfile, skipping")