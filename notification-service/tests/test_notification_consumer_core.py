import pytest
from services.notification_consumer_core import NotificationConsumerService
from unittest.mock import AsyncMock
from models import UserContact, NotificationSettings

@pytest.fixture
def get_notification_consumer_service(mock_db):
    return NotificationConsumerService({'user_id': 1, 'email': 'test@example', 'username': 'test', 'monthly_stats_total': 150000, 'user_budget_limit': 125000, 'monthly_budget_exceeded_notification': True, 'weekly_summary_notification': True}, mock_db)

@pytest.fixture
def fake_user_contact():
    return UserContact(user_id = 1, email = 'test@example', username = 'test')

@pytest.fixture
def fake_notification_settings():
    return NotificationSettings(user_id = 1, monthly_budget_exceeded_notification = False, weekly_summary_notification = False)

async def test_user_created(get_notification_consumer_service, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_notification_consumer_service.handle_user_created()
    mock_db.add.call_count == 2
    created_user_contact = mock_db.add.call_args_list[0].args[0]
    assert created_user_contact.user_id == 1
    assert created_user_contact.email == 'test@example'
    assert created_user_contact.username == 'test'
    created_notification_settings = mock_db.add.call_args_list[1].args[0]
    assert created_notification_settings.user_id == 1
    mock_db.commit.assert_called_once()

async def test_user_contact_created_user_contact_is_exist(get_notification_consumer_service, mock_db, make_mock_result, fake_user_contact):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_contact))
    result = await get_notification_consumer_service.handle_user_created()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()

async def test_user_updated(get_notification_consumer_service, mock_db, make_mock_result, fake_user_contact):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_contact))
    result = await get_notification_consumer_service.handle_user_updated()
    mock_db.commit.assert_called_once()

async def test_user_updated_user_not_found(get_notification_consumer_service, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_notification_consumer_service.handle_user_updated()
    mock_db.commit.assert_not_called()

async def test_user_deleted(get_notification_consumer_service, mock_db, make_mock_result, fake_user_contact):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_contact))
    result = await get_notification_consumer_service.handle_user_deleted()
    mock_db.delete.assert_called_once_with(fake_user_contact)
    mock_db.commit.assert_called_once()

async def test_user_deleted_user_not_found(get_notification_consumer_service, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_notification_consumer_service.handle_user_deleted()
    mock_db.commit.assert_not_called()

async def test_budget_exceed(get_notification_consumer_service, mock_db, make_mock_result, fake_user_contact):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user_contact.username))
    result = await get_notification_consumer_service.handle_budget_exceed()
    notification_log_created = mock_db.add.call_args.args[0]
    assert notification_log_created.user_id == 1
    assert notification_log_created.notification_topic == 'Budget exceed'
    assert notification_log_created.notification_message == f'Hello, test, your spending has exceeded the expected limit by {25000}'
    mock_db.commit.assert_called_once()

async def test_settings_updated(get_notification_consumer_service, mock_db, make_mock_result, fake_notification_settings):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_notification_settings))
    result = await get_notification_consumer_service.handle_settings_updated()
    mock_db.commit.assert_called_once()