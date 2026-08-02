from fastapi import FastAPI
from routers import transaction
from database import engine
from contextlib import asynccontextmanager
from redis_client import redis_pool
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.redis_pool = redis_pool
    yield
    logger.info('App shuting down')
    await redis_pool.aclose()
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Transaction Service API')
app.include_router(transaction.router)