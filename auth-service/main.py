import logging
from contextlib import asynccontextmanager

from database import engine
from fastapi import FastAPI
from rabbitmq_client import get_rabbitmq_connection
from routers import auth

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.rabbitmq_connection = await get_rabbitmq_connection()
    yield
    logger.info('App shuting down')
    await app.state.rabbitmq_connection.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan, title='Authorization Service API')
app.include_router(auth.router)
