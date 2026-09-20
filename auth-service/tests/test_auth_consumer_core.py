import pytest
from unittest.mock import AsyncMock
from services.auth_consumer_core import AuthConsumerService

@pytest.fixture
def get_auth_consumer_service(mock_db):
    return AuthConsumerService({'user_id': 2, 'username': 'test_update', 'email': 'test_update@example.com'}, mock_db)

async def test_user_updated(get_auth_consumer_service, mock_db, make_mock_result, fake_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user))
    result = await get_auth_consumer_service.handle_user_updated()
    assert fake_user.username == 'test_update'
    assert fake_user.email == 'test_update@example.com'
    mock_db.commit.assert_called_once()

async def test_user_deleted(get_auth_consumer_service, mock_db, make_mock_result, fake_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user))
    result = await get_auth_consumer_service.handle_user_deleted()
    delete_user = mock_db.delete.call_args.args[0]
    assert delete_user.username == 'test'
    assert delete_user.email == 'test_999@example.com'
    mock_db.commit.assert_called_once()