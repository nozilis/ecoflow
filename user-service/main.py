from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine
from routers import user_profile
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    yield
    logger.info('App shuting down')
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='User Service API')
app.include_router(user_profile.router)