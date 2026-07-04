from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from decouple import config

DATABASE_URL = config('DATABASE_URL')

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)