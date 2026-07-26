import asyncio
from fastapi import FastAPI, Request, Response, status, HTTPException
import httpx
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

SERVICE_MAP = {
        'auth': 'http://auth_service:8000',
        'transactions': 'http://transaction_service:8000',
        'analytics': 'http://analytics_service:8000',
        'user_profile': 'http://user_service:8000',
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    client = httpx.AsyncClient(limits=limits)
    yield  
    await client.aclose()

app = FastAPI(lifespan=lifespan, title='Gateway Service API')

@app.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
async def gateway_proxy(request: Request, path: str):
    body = await request.body()
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    headers.pop("host", None)

    service_prefix = path.split('/')[0]

    base_url = SERVICE_MAP.get(f'{service_prefix}')

    if base_url is None:
        logger.warning(f'Service prefix {service_prefix} not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Service prefix not found')

    try:
        response = await asyncio.wait_for(
            client.request(
                method=request.method,
                url=f"{base_url}/{path}",
                content=body,
                headers=headers,
                params=params
            ),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.warning('Request response timeout')
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=('Request response timeout'))

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )