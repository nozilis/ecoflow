import pytest
from services.transaction_core import TransactionService, TransactionNotFound, InvalidCategory
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from enums import ExpenseCategory, IncomeCategory, TransactionType
from types import SimpleNamespace
from schemas import TransactionUpdate

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
def mock_result(fake_transaction):
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_transaction
    return result

@pytest.fixture
def mock_transaction_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    return result

async def fake_scan_iter(match=None):
    yield 'transactions:1:1:20'

async def fake_refresh(obj):
    obj.id = 1
    obj.created_at = datetime(2026, 8, 4, 12, 0, 0)

@pytest.fixture
def fake_transaction():
    return SimpleNamespace(
        id=1,
        user_id=1,
        amount=500,
        transaction_type=TransactionType.EXPENSE,
        category=ExpenseCategory.RESTAURANT,
        description='Поход в ресторан',
        created_at=datetime(2026, 8, 4, 12, 0, 0)
    )

@pytest.fixture
def fake_transaction_update_request():
    return TransactionUpdate(amount=5000)

@pytest.fixture
def fake_invalid_transaction_update_request():
    return TransactionUpdate(amount=5000, category=IncomeCategory.TRANSFERS)

@pytest.fixture
def get_transaction_service(mock_db, mock_redis, mock_rabbitmq):
    return TransactionService(db=mock_db,user_id=1,redis=mock_redis,rabbitmq=mock_rabbitmq)

@patch('services.transaction_core.publish_transaction_events', new_callable=AsyncMock)
async def test_create_transaction(mock_publish, get_transaction_service, mock_db, mock_redis, mock_rabbitmq):
    result = await get_transaction_service.create_transaction(
        amount=50000, 
        transaction_type=TransactionType.EXPENSE,
        category=ExpenseCategory.TRAVEL,
        description='Поездка в Норвегию'
        )
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once_with(
        'created', 
        1, 
        mock_rabbitmq, 
        amount=50000, 
        transaction_type=TransactionType.EXPENSE, 
        category=ExpenseCategory.TRAVEL, 
        created_at=datetime(2026, 8, 4, 12, 0, 0)
    )
    mock_redis.delete.assert_called_once()
    assert result

@patch('services.transaction_core.publish_transaction_events', new_callable=AsyncMock)
async def test_delete_transaction(mock_publish, get_transaction_service, mock_db, mock_redis, mock_rabbitmq, mock_result):
    mock_db.execute = AsyncMock(return_value=mock_result)
    result = await get_transaction_service.delete_transaction(1)
    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once_with(
        'deleted',
        1,
        mock_rabbitmq,
        amount=500,
        transaction_type=TransactionType.EXPENSE,
        category=ExpenseCategory.RESTAURANT,
        created_at=datetime(2026, 8, 4, 12, 0, 0)
    )
    mock_redis.delete.assert_called_once()

@patch('services.transaction_core.publish_transaction_events', new_callable=AsyncMock)
async def test_valid_update_transaction(mock_publish, get_transaction_service, mock_db, mock_redis, mock_rabbitmq, mock_result, fake_transaction_update_request, fake_transaction):
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_recent_amount=fake_transaction.amount
    mock_recent_type=fake_transaction.transaction_type
    result = await get_transaction_service.update_transaction(
        1,
        fake_transaction_update_request
    )
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once_with(
        'updated',
        1,
        mock_rabbitmq,
        amount=5000,
        transaction_type=TransactionType.EXPENSE,
        category=ExpenseCategory.RESTAURANT,
        created_at=datetime(2026, 8, 4, 12, 0, 0),
        recent_amount=mock_recent_amount,
        recent_type=mock_recent_type
    )
    mock_redis.delete.assert_called_once()
    assert result

async def test_invalid_update_transaction(get_transaction_service, mock_db, mock_transaction_not_found, fake_transaction_update_request):
    with pytest.raises(TransactionNotFound):
        mock_db.execute = AsyncMock(return_value=mock_transaction_not_found)
        result = await get_transaction_service.update_transaction(
            10,
            fake_transaction_update_request
        )

async def test_invalid_category_transacton_update(get_transaction_service, mock_db, mock_result, fake_invalid_transaction_update_request, fake_transaction):
    with pytest.raises(InvalidCategory):
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await get_transaction_service.update_transaction(
            1,
            fake_invalid_transaction_update_request
        )