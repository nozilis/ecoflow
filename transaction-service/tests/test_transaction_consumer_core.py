import pytest
from unittest.mock import AsyncMock, MagicMock
from services.transaction_consumer_core import TransactionConsumerService
from models import Transaction
from enums import TransactionType, IncomeCategory, ExpenseCategory
from datetime import datetime

@pytest.fixture
def get_transaction_consumer_service(mock_db, mock_redis):
    return TransactionConsumerService({'user_id': 1}, mock_db, mock_redis)

@pytest.fixture
def fake_user_transactions():
    return [
        Transaction(
        id=1, 
        user_id=1, 
        amount=50000, 
        transaction_type=TransactionType.EXPENSE, 
        category=ExpenseCategory.TRAVEL, 
        created_at=datetime(2026, 8, 4, 12, 0, 0)
        ),
        Transaction(
        id=2, 
        user_id=2, 
        amount=15000, 
        transaction_type=TransactionType.EXPENSE, 
        category=ExpenseCategory.RESTAURANT, 
        created_at=datetime(2026, 8, 4, 12, 0, 0)
        ),
        Transaction(
        id=3, 
        user_id=3, 
        amount=150000, 
        transaction_type=TransactionType.INCOME, 
        category=IncomeCategory.SALARY, 
        created_at=datetime(2026, 8, 4, 12, 0, 0)
        )
    ]

async def test_handle_user_deleted(get_transaction_consumer_service, mock_db, mock_redis, make_mock_results, fake_user_transactions):
    mock_db.execute = AsyncMock(return_value=make_mock_results(fake_user_transactions))
    result = await get_transaction_consumer_service.handle_user_deleted()
    assert mock_db.delete.call_count == 3
    mock_db.commit.assert_called_once()
    mock_redis.delete.assert_called_once()

async def test_transactions_not_found(get_transaction_consumer_service, mock_db, mock_redis, make_mock_results):
    mock_db.execute = AsyncMock(return_value=make_mock_results([]))
    result = await get_transaction_consumer_service.handle_user_deleted()
    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_redis.delete.assert_not_called()