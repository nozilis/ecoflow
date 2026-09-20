import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.auth_core import AuthService, UsernameConflict, InvalidUsernameOrPassword, UsernameAndEmailConflict
from schemas import UserCreate, UserLogin
from datetime import datetime
from sqlalchemy.exc import IntegrityError

@pytest.fixture
def get_auth_service(mock_db, mock_rabbitmq):
    return AuthService(mock_db, mock_rabbitmq)

@pytest.fixture
def fake_register_user():
    return UserCreate(username = 'test', password = 'test', confirm_password = 'test', email = 'test@example.com')

@pytest.fixture
def fake_login_user():
    return UserLogin(username='test', password='test')

@pytest.fixture
def mock_bcrypt():
    result = MagicMock()
    result.verify.return_value = True
    return result

@patch('services.auth_core.publish_user_events', new_callable=AsyncMock)
async def test_register_user(mock_publish, get_auth_service, mock_db, mock_rabbitmq, make_mock_result, fake_register_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_auth_service.register_user(fake_register_user)
    mock_db.add.assert_called_once()
    mock_db.refresh.assert_called_once()
    create_user = mock_db.add.call_args.args[0]
    assert create_user.username == 'test'
    assert create_user.email == 'test@example.com'
    assert create_user.hashed_password != 'test'
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once_with(
        'created',
        1,
        mock_rabbitmq,
        username='test',
        email='test@example.com',
        registered_at=datetime(2026, 8, 4, 12, 0, 0)
    )

async def test_register_user_username_is_already_taken(get_auth_service, mock_db, make_mock_result, fake_register_user, fake_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user))
    with pytest.raises(UsernameConflict):
        result = await get_auth_service.register_user(fake_register_user)
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()

@patch('services.auth_core.bcrypt.verify')
async def test_login_user(mock_verify, get_auth_service, mock_db, make_mock_result, fake_login_user, fake_user):
    mock_verify.return_value = True
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user))
    result = await get_auth_service.login_user(fake_login_user)
    mock_verify.assert_called_once()

async def test_login_user_not_found(get_auth_service, mock_db, make_mock_result, fake_login_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    with pytest.raises(InvalidUsernameOrPassword):
        result = await get_auth_service.login_user(fake_login_user)

@patch('services.auth_core.bcrypt.verify')
async def test_login_user_wrong_password(mock_verify, get_auth_service, mock_db, make_mock_result, fake_login_user, fake_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_user))
    mock_verify.return_value = False
    with pytest.raises(InvalidUsernameOrPassword):
        result = await get_auth_service.login_user(fake_login_user)

async def test_register_user_integrity_error(get_auth_service, mock_db, make_mock_result, fake_register_user):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    fake_error = IntegrityError('...', None, None)
    fake_error.orig = MagicMock()
    fake_error.orig.diag.message_detail = 'Username or email is already exist'
    mock_db.commit = AsyncMock(side_effect=fake_error)
    with pytest.raises(UsernameAndEmailConflict):
        await get_auth_service.register_user(fake_register_user)
    mock_db.rollback.assert_called_once()