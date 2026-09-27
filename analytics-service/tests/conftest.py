import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db():
    result = AsyncMock()
    result.add = MagicMock()
    return result

@pytest.fixture
def mock_redis():
    result = AsyncMock()
    result.scan_iter = fake_scan_iter
    return result

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
    yield '*_stats:1:*'