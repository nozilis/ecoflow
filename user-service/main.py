from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine
from routers import user_profile
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

app = FastAPI(lifespan=lifespan, title='User Service API')
app.include_router(user_profile.router)