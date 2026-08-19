import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
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