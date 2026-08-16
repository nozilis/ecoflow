import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock(side_effect=fake_refresh)
    return db

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.scan_iter = fake_scan_iter
    return redis

@pytest.fixture
def mock_rabbitmq():  
    return AsyncMock()

@pytest.fixture
def make_mock_result():
    def _make(return_value):
        result = MagicMock()
        result.scalar_one_or_none.return_value = return_value
        return result
    return _make

@pytest.fixture
def make_mock_results():
    def _make(return_value):
        result = MagicMock()
        result.scalars.return_value.all.return_value = return_value
        return result
    return _make

async def fake_scan_iter(match=None):
    yield 'transactions:1:1:20'

async def fake_refresh(obj):
    obj.id = 1
    obj.created_at = datetime(2026, 8, 4, 12, 0, 0)