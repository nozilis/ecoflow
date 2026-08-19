import pytest
from unittest.mock import AsyncMock, patch, call
from services.user_profile_core import UserProfileService, UserProfileNotFound, UsernameConflict, EmailConflict
from models import UserProfile
from enums import VisibilityChoice
from schemas import UserProfileUpdate
import json

@pytest.fixture
def get_user_profile_service(mock_db, mock_redis, mock_rabbitmq):
    return UserProfileService(db=mock_db, request_user=1, redis=mock_redis, rabbitmq=mock_rabbitmq)

@pytest.fixture
def fake_user_profile_id():
    return 2

@pytest.fixture
def fake_private_user_profile_id():
    return 3

@pytest.fixture
def fake_not_found_user_profile_id():
    return 999

@pytest.fixture
def fake_user_profile():
    return UserProfile(
        user_id = 2,
        username = 'test_1',
        email = 'test_1',
        avatar = 'avatar_1',
        budget_limit = 80000,
        social_links = {},
        visibility_choice = VisibilityChoice.PUBLIC,
        monthly_budget_exceeded_notification = True,
        weekly_summary_notification = True
    )

@pytest.fixture
def fake_private_user_profile():
    return UserProfile(
        user_id = 3,
        username = 'test_2',
        email = 'test_2',
        avatar = 'avatar_2',
        budget_limit = 50000,
        social_links = {},
        visibility_choice = VisibilityChoice.PRIVATE,
        monthly_budget_exceeded_notification = True,
        weekly_summary_notification = True
    )

@pytest.fixture
def fake_owner_user_profile():
    return UserProfile(
        user_id = 1,
        username = 'test_3',
        email = 'test_3',
        avatar = 'avatar_3',
        budget_limit = 130000,
        social_links = {},
        visibility_choice = VisibilityChoice.PUBLIC,
        monthly_budget_exceeded_notification = True,
        weekly_summary_notification = True
    )

@pytest.fixture
def fake_username_taken_user_profile():
    return UserProfile(
        user_id = 1,
        username = 'update_test_1',
        email = 'test_3',
        avatar = 'avatar_3',
        budget_limit = 130000,
        social_links = {},
        visibility_choice = VisibilityChoice.PUBLIC,
        monthly_budget_exceeded_notification = True,
        weekly_summary_notification = True
    )

@pytest.fixture
def fake_email_taken_user_profile():
    return UserProfile(
        user_id = 1,
        username = 'test_3',
        email = 'update_test_2',
        avatar = 'avatar_3',
        budget_limit = 130000,
        social_links = {},
        visibility_choice = VisibilityChoice.PUBLIC,
        monthly_budget_exceeded_notification = True,
        weekly_summary_notification = True
    )

@pytest.fixture
def fake_user_profile_update_request():
    return UserProfileUpdate(
        username='update_test_1',
        budget_limit=1500000,
        monthly_budget_exceeded_notification=False,
        weekly_summary_notification=False
    )

@pytest.fixture
def fake_email_user_profile_update_request():
    return UserProfileUpdate(username='update_test_2', email='update_test_2')

async def test_get_user_profile(get_user_profile_service, mock_db, mock_redis, make_mock_result, fake_user_profile, fake_user_profile_id):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_profile))
    result = await get_user_profile_service.get_user_profile(fake_user_profile_id)
    mock_redis.get.assert_called_once()
    mock_redis.set.assert_called_once_with(
        'user_profile:2',
        json.dumps({
        'username': 'test_1',
        'email': 'test_1',
        'avatar': 'avatar_1',
        'budget_limit': 80000,
        'social_links': {},
        'visibility_choice': VisibilityChoice.PUBLIC,
        'monthly_budget_exceeded_notification': True,
        'weekly_summary_notification': True
        }),
        300
    )
    assert result

async def test_get_private_user_profile(get_user_profile_service, mock_db, mock_redis, make_mock_result, fake_private_user_profile, fake_private_user_profile_id):
    with pytest.raises(UserProfileNotFound):
        mock_db.execute = AsyncMock(return_value=make_mock_result(fake_private_user_profile))
        result = await get_user_profile_service.get_user_profile(fake_private_user_profile_id)
    mock_redis.get.assert_called_once()
    mock_redis.set.assert_not_called()

async def test_user_profile_not_found(get_user_profile_service, mock_db, mock_redis, make_mock_result, fake_not_found_user_profile_id):
    with pytest.raises(UserProfileNotFound):
        mock_db.execute = AsyncMock(return_value=make_mock_result(None))
        result = await get_user_profile_service.get_user_profile(fake_not_found_user_profile_id)
    mock_redis.get.assert_called_once()
    mock_redis.set.assert_not_called()

@patch('services.user_profile_core.publish_user_events', new_callable=AsyncMock)
async def test_update_user_profile(mock_publish, get_user_profile_service, mock_db, mock_redis, mock_rabbitmq, make_mock_result, fake_owner_user_profile, fake_user_profile_update_request):
    mock_db.execute = AsyncMock(side_effect=[make_mock_result(fake_owner_user_profile), make_mock_result(None), make_mock_result(None)])
    result = await get_user_profile_service.update_user_profile(fake_user_profile_update_request)
    mock_redis.delete.assert_called_once_with('user_profile:1')
    mock_publish.assert_has_calls([
    call('updated', 1, mock_rabbitmq, username='update_test_1'),
    call('budget_limit_updated', 1, mock_rabbitmq, budget_limit=1500000),
    call('settings.updated', 1, mock_rabbitmq, monthly_budget_exceeded_notification=False, weekly_summary_notification=False),
    ])
    assert result

async def test_username_conflict_update_user_profile(get_user_profile_service, mock_db, mock_redis, make_mock_result, fake_owner_user_profile, fake_username_taken_user_profile, fake_user_profile_update_request):
    with pytest.raises(UsernameConflict):
        mock_db.execute = AsyncMock(side_effect=[make_mock_result(fake_owner_user_profile), make_mock_result(fake_username_taken_user_profile)])
        result = await get_user_profile_service.update_user_profile(fake_user_profile_update_request)
    mock_redis.delete.assert_not_called()

async def test_email_conflict_update_user_profile(get_user_profile_service, mock_db, mock_redis, make_mock_result, fake_owner_user_profile, fake_email_taken_user_profile, fake_email_user_profile_update_request):
    with pytest.raises(EmailConflict):
        mock_db.execute = AsyncMock(side_effect=[make_mock_result(fake_owner_user_profile), make_mock_result(None), make_mock_result(fake_email_taken_user_profile)])
        result = await get_user_profile_service.update_user_profile(fake_email_user_profile_update_request)
    mock_redis.delete.assert_not_called()

@patch('services.user_profile_core.publish_user_events', new_callable=AsyncMock)
async def test_delete_user(mock_publish, get_user_profile_service, mock_db, mock_redis, mock_rabbitmq, make_mock_result, fake_owner_user_profile):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_owner_user_profile))
    result = await get_user_profile_service.delete_user_profile()
    mock_redis.delete.assert_called_once_with('user_profile:1')
    mock_publish.assert_called_once_with(
        'deleted',
        1,
        mock_rabbitmq
    )