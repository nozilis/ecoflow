from fastapi import FastAPI
from routers import auth
from database import engine
from contextlib import asynccontextmanager
from rabbitmq_client import get_rabbitmq_connection
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.rabbitmq_connection = await get_rabbitmq_connection()
    yield
    logger.info('App shuting down')
    await app.state.rabbitmq_connection.aclose()
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Authorization Service API')
app.include_router(auth.router)