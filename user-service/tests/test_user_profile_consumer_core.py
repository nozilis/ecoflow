import pytest
from unittest.mock import AsyncMock
from services.user_profile_consumer_core import UserProfileConsumerService
from models import UserProfile

@pytest.fixture
def get_user_profile_consumer_service(mock_db):
    return UserProfileConsumerService({'id': 1, 'username': 'test_1', 'email': 'test@example.com'}, mock_db)

@pytest.fixture
def fake_user_profile_is_exist():
    return UserProfile(user_id = 1, username = 'test_1', email = 'test@example.com')

async def test_create_user_profile(get_user_profile_consumer_service, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_user_profile_consumer_service.handle_user_created()
    mock_db.add.assert_called_once()
    created_profile = mock_db.add.call_args.args[0]
    assert created_profile.user_id == 1
    assert created_profile.username == 'test_1'
    assert created_profile.email == 'test@example.com'
    mock_db.commit.assert_called_once()

async def test_user_profile_is_exist(get_user_profile_consumer_service, mock_db, make_mock_result, fake_user_profile_is_exist):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_profile_is_exist))
    result = await get_user_profile_consumer_service.handle_user_created()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()