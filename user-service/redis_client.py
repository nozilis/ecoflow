import redis.asyncio as redis

redis_pool = redis.ConnectionPool.from_url('redis://redis:6379', max_connections=20)