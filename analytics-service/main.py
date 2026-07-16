from fastapi import FastAPI
from routers import analytics
from database import engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('App starting up')
    yield
    print('App shuting down')
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Analytics Service API')
app.include_router(analytics.router)