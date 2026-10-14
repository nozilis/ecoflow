from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine
from routers import user_profile
from redis_client import redis_pool
from rabbitmq_client import get_rabbitmq_connection
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.redis_pool = redis_pool
    app.state.rabbitmq_connection = await get_rabbitmq_connection()
    yield
    logger.info('App shuting down')
    await redis_pool.aclose()
    await app.state.rabbitmq_connection.close()
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='User Service API')
app.include_router(user_profile.router)