import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from models import User

@pytest.fixture
def mock_db():
    result = AsyncMock()
    result.add = MagicMock()
    result.refresh = AsyncMock(side_effect=fake_refresh)
    return result

@pytest.fixture
def mock_rabbitmq():
    return AsyncMock()

@pytest.fixture
def fake_user():
    return User(id=2, username='test', hashed_password='a8dh8H@O*GR@#*(Ffbsa)', email='test_999@example.com', registered_at=datetime(2026, 6, 4, 12, 0, 0))

@pytest.fixture
def make_mock_result():
    def _make(return_value):
        result = MagicMock()
        result.scalar_one_or_none.return_value = return_value
        return result
    return _make

async def fake_refresh(obj):
    obj.id = 1
    obj.registered_at = datetime(2026, 8, 4, 12, 0, 0)