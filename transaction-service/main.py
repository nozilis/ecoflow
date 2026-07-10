from fastapi import FastAPI
from routers import transaction
from database import engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('App starting up')
    yield
    print('App shuting down')
    await engine.dispose()

app = FastAPI(lifespan=lifespan, title='Transaction Service API')
app.include_router(transaction.router)