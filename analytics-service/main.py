from fastapi import FastAPI
from routers import analytics
from database import engine
from contextlib import asynccontextmanager
import logging
from redis_client import redis_pool
from rabbitmq_client import get_rabbitmq_connection

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.redis_pool = redis_pool
    app.state.rabbitmq_connection = await get_rabbitmq_connection()
    yield
    logger.info('App shuting down')
    await redis_pool.aclose()
    await app.state.rabbitmq_connection.aclose()
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Analytics Service API')
app.include_router(analytics.router)