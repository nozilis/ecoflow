from fastapi import FastAPI
from routers import analytics
from database import engine
from contextlib import asynccontextmanager
import logging
from redis_client import redis_pool

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    app.state.redis_pool = redis_pool
    yield
    logger.info('App shuting down')
    await redis_pool.aclose()
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Analytics Service API')
app.include_router(analytics.router)