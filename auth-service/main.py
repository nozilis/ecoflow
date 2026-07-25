from fastapi import FastAPI
from routers import auth
from database import engine
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('App starting up')
    yield
    logger.info('App shuting down')
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Authorization Service API')
app.include_router(auth.router)