from passlib.hash import bcrypt
from models import User
from sqlalchemy import select, or_
from publisher import publish_user_events
from sqlalchemy.exc import IntegrityError
from schemas import UserResponse
from jwt_token import create_access_token
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db):
        self.db = db

    async def register_user(self, user):
        hashed_password = bcrypt.hash(user.password)
        user_is_exist = await self.db.execute(select(User).where(or_(User.username == user.username, User.email == user.email)))
        db_user = user_is_exist.scalar_one_or_none()
        if db_user is None:
            create_user = User(
                username = user.username, 
                hashed_password = hashed_password, 
                email = user.email)
            try:
                self.db.add(create_user)
                await self.db.commit()
                await publish_user_events('created', create_user.id, username=user.username, email=user.email, created_at=create_user.created_at)
                logger.info('User successfully registered')
                return UserResponse.model_validate(create_user)
            except IntegrityError as e:
                pg_code = e.orig.diag.message_detail
                await self.db.rollback()
                logger.error(f'IntegrityError during registration: {pg_code}')
                raise UsernameAndEmailConflict('Username or email is already taken')
        elif db_user.username == user.username:
            logger.warning('Username is already taken')
            raise UsernameConflict('Username is already taken')
        else:
            logger.warning('Email is already taken')
            raise EmailConflict('Email is already taken')

    async def login_user(self, user):
        user_is_exist = await self.db.execute(select(User).where(User.username == user.username))
        db_user = user_is_exist.scalar_one_or_none()
        if db_user is None:
            logger.warning('User not found')
            raise InvalidUsernameOrPassword('Invalid username or password')
        elif bcrypt.verify(user.password, db_user.hashed_password):
            logger.info('User successfully login')
            return create_access_token({'sub': str(db_user.id)})
        else:
            logger.warning('User fails verification')
            raise InvalidUsernameOrPassword('Invalid username or password')

class UsernameAndEmailConflict(Exception):
    pass

class UsernameConflict(Exception):
    pass

class EmailConflict(Exception):
    pass

class InvalidUsernameOrPassword(Exception):
    pass