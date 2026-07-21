from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine
from routers import user

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('App starting up')
    yield
    print('App shuting down')
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='User Service API')
app.include_router(user.router)