from models import UserProfile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from enums import VisibilityChoice
from publisher import publish_user_events
import logging

logger = logging.getLogger(__name__)

class UserProfileService:
    def __init__(self, db, request_user):
        self.db = db
        self.request_user = request_user

    async def get_user_profile(self, user_id):
        if user_id is None:
            user_id = self.request_user
        user_profile_is_exist = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        db_user_profile = user_profile_is_exist.scalar_one_or_none()
        if db_user_profile is None:
            logger.warning(f'User profile for user {user_id} not found')
            raise UserProfileNotFound('User not found')
        else:
            if db_user_profile.visibility_choice == VisibilityChoice.PRIVATE and self.request_user != user_id:
                logger.warning(f'User profile for user {user_id} visibility choice is private and request user is not owner of this account')
                raise UserProfileNotFound('User not found')
            return db_user_profile

    async def update_user_profile(self, user_profile_update_request):
        user_profile_is_exist = await self.db.execute(select(UserProfile).where(UserProfile.user_id == self.request_user))
        db_user_profile = user_profile_is_exist.scalar_one_or_none()
        if db_user_profile is None:
            logger.warning(f'User profile for user {self.request_user} not found')
            raise UserProfileNotFound('User not found')
        user_profile_update_dump = user_profile_update_request.model_dump(exclude_unset=True)
        if user_profile_update_dump.get('username') is not None:
            username_is_already_exist = await self.db.execute(select(UserProfile).where(UserProfile.username == user_profile_update_dump.get('username')))
            db_username_is_already_exist = username_is_already_exist.scalar_one_or_none()
            if db_username_is_already_exist is not None:
                logger.warning(f'Username {user_profile_update_dump.get("username")} is already taken')
                raise UsernameConflict('Username is already exist')
        if user_profile_update_dump.get('email') is not None:
            email_is_already_exist = await self.db.execute(select(UserProfile).where(UserProfile.email == user_profile_update_dump.get('email')))
            db_email_is_already_exist = email_is_already_exist.scalar_one_or_none()
            if db_email_is_already_exist is not None:
                logger.warning(f'Email {user_profile_update_dump.get("email")} is already taken')
                raise EmailConflict('Email is already exist')
        user_profile_update_dump_items = user_profile_update_dump.items()
        for item, value in user_profile_update_dump_items:
            setattr(db_user_profile, item, value)
        try:
            await self.db.commit()
            logger.info(f'User profile for user {self.request_user} successfully updated')
            if 'username' in user_profile_update_dump or 'email' in user_profile_update_dump:
                await publish_user_events('updated', self.request_user, **{k: v for k, v in user_profile_update_dump_items if k in {'username', 'email'}})
            if 'budget_limit' in user_profile_update_dump:
                await publish_user_events('budget_limit_updated', self.request_user, budget_limit=user_profile_update_dump.get('budget_limit'))
            if 'monthly_budget_exceeded_notification' in user_profile_update_dump or 'weekly_summary_notification' in user_profile_update_dump:
                await publish_user_events('settings.updated', self.request_user, **{k: v for k, v in user_profile_update_dump_items if k in {'monthly_budget_exceeded_notification', 'weekly_summary_notification'}})
            return db_user_profile
        except IntegrityError as e:
            pg_code = e.orig.diag.message_detail
            await self.db.rollback()
            logger.error(f'IntegrityError during user updating: {pg_code}')
            raise UsernameAndEmailConflict('Username or email is already taken')

    async def delete_user_profile(self):
        user_profile_is_exist = await self.db.execute(select(UserProfile).where(UserProfile.user_id == self.request_user))
        db_user_profile = user_profile_is_exist.scalar_one_or_none()
        if db_user_profile is None:
            logger.warning(f'User profile for user {self.request_user} not found')
            raise UserProfileNotFound('User not found')
        await self.db.delete(db_user_profile)
        await self.db.commit()
        logger.info(f'User profile for user {self.request_user} successfully deleted')
        await publish_user_events('deleted', self.request_user)

class UserProfileNotFound(Exception):
    pass

class UsernameConflict(Exception):
    pass

class EmailConflict(Exception):
    pass

class UsernameAndEmailConflict(Exception):
    pass