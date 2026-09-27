import pytest
from unittest.mock import AsyncMock, patch
from services.analytics_consumer_core import AnalyticsConsumerService
from models import MonthlyStats, UserBudget, BudgetExceedNotification
from datetime import datetime

@pytest.fixture
def get_analytics_consumer_service_transaction(mock_db, mock_redis, mock_rabbitmq):
    return AnalyticsConsumerService({'user_id': 1, 'category': 'Products', 'transaction_type': 'Expense', 'amount': 50000, 'created_at': '2026-07-04T12:00:00', 'budget_limit': 250000}, mock_db, mock_redis, mock_rabbitmq)

@pytest.fixture
def get_analytics_consumer_service_transaction_updated_unchanged_logic_fields(mock_db, mock_redis, mock_rabbitmq):
    return AnalyticsConsumerService({'user_id': 1, 'category': 'Products', 'transaction_type': 'Expense', 'amount': 30000, 'created_at': '2026-08-04T12:00:00', 'recent_type': 'Expense', 'recent_amount': 40000, 'recent_category': 'Products'}, mock_db, mock_redis, mock_rabbitmq)

@pytest.fixture
def get_analytics_consumer_service_transaction_updated_type_difference(mock_db, mock_redis, mock_rabbitmq):
    return AnalyticsConsumerService({'user_id': 1, 'category': 'Products', 'transaction_type': 'Expense', 'amount': 30000, 'created_at': '2026-08-04T12:00:00', 'recent_type': 'Income', 'recent_amount': 40000, 'recent_category': 'Products'}, mock_db, mock_redis, mock_rabbitmq)

@pytest.fixture
def get_analytics_consumer_service_transaction_updated_category_difference(mock_db, mock_redis, mock_rabbitmq):
    return AnalyticsConsumerService({'user_id': 1, 'category': 'Products', 'transaction_type': 'Expense', 'amount': 30000, 'created_at': '2026-08-04T12:00:00', 'recent_type': 'Income', 'recent_amount': 40000, 'recent_category': 'Restaurant'}, mock_db, mock_redis, mock_rabbitmq)

@pytest.fixture
def fake_user_budget():
    return UserBudget(user_id=1, budget_limit=250000)

@pytest.fixture
def fake_budget_exceed_notification():
    return BudgetExceedNotification(id=1, user_id=1, year=2026, month=7)

@pytest.fixture
def fake_mothly_stats():
    return MonthlyStats(id=1, user_id=1, year=2026, month=7, category='Products', transaction_type='Expense', total_amount=300000)

@pytest.fixture
def fake_type_difference_mothly_stats():
    return MonthlyStats(id=1, user_id=1, year=2026, month=7, category='Products', transaction_type='Income', total_amount=25000)

@pytest.fixture
def fake_category_difference_mothly_stats():
    return MonthlyStats(id=1, user_id=1, year=2026, month=7, category='Restaurant', transaction_type='Expense', total_amount=25000)

@pytest.fixture
def fake_scalars_monthly_stats():
    return [
        MonthlyStats(id=3, user_id=1, year=2026, month=7, category='Products', transaction_type='Expense', total_amount=25000),
        MonthlyStats(id=2, user_id=1, year=2025, month=8, category='Salary', transaction_type='Income', total_amount=37000),
        MonthlyStats(id=1, user_id=1, year=2025, month=6, category='Restaurant', transaction_type='Expense', total_amount=15000)
    ]

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_created(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=(make_mock_result(None)))
    result = await get_analytics_consumer_service_transaction.handle_transaction_created()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_updated_no_change(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction_updated_unchanged_logic_fields, mock_db, make_mock_result, fake_mothly_stats):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_mothly_stats))
    result = await get_analytics_consumer_service_transaction_updated_unchanged_logic_fields.handle_transaction_updated()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_updated_type_changed(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction_updated_type_difference, mock_db, make_mock_result, fake_mothly_stats, fake_type_difference_mothly_stats):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(fake_mothly_stats),
        make_mock_result(fake_type_difference_mothly_stats)
        ])
    result = await get_analytics_consumer_service_transaction_updated_type_difference.handle_transaction_updated()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_updated_not_found(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction_updated_unchanged_logic_fields, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_analytics_consumer_service_transaction_updated_unchanged_logic_fields.handle_transaction_updated()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_budget_exceed_check.assert_not_called()
    mock_cache_delete_handle.assert_not_called()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_updated_category_difference(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction_updated_category_difference, mock_db, make_mock_result, fake_mothly_stats, fake_category_difference_mothly_stats):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(fake_mothly_stats),
        make_mock_result(fake_category_difference_mothly_stats)
    ])
    result = await get_analytics_consumer_service_transaction_updated_category_difference.handle_transaction_updated()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_updated_category_changed_not_found(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction_updated_category_difference, mock_db, make_mock_result, fake_mothly_stats):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(fake_mothly_stats),
        make_mock_result(None)
    ])
    result = await get_analytics_consumer_service_transaction_updated_category_difference.handle_transaction_updated()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_deleted(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction, mock_db, make_mock_result, fake_mothly_stats):
    mock_db.execute = AsyncMock(return_value=make_mock_result(fake_mothly_stats))
    result = await get_analytics_consumer_service_transaction.handle_transaction_deleted()
    mock_db.commit.assert_called_once()
    mock_budget_exceed_check.assert_called_once()
    mock_cache_delete_handle.assert_called_once()

@patch.object(AnalyticsConsumerService, 'cache_delete_handle', new_callable=AsyncMock)
@patch.object(AnalyticsConsumerService, 'budget_exceed_check', new_callable=AsyncMock)
async def test_handle_transaction_deleted_not_found(mock_budget_exceed_check, mock_cache_delete_handle, get_analytics_consumer_service_transaction, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=make_mock_result(None))
    result = await get_analytics_consumer_service_transaction.handle_transaction_deleted()
    mock_db.commit.assert_not_called()
    mock_budget_exceed_check.assert_not_called()
    mock_cache_delete_handle.assert_not_called()

async def test_handle_budget_limit_updated(get_analytics_consumer_service_transaction, mock_db, make_mock_result, fake_user_budget):
    mock_db.execute = AsyncMock(return_value=(make_mock_result(fake_user_budget)))
    result = await get_analytics_consumer_service_transaction.handle_budget_limit_updated()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()

async def test_handle_budget_limit_updated_not_found(get_analytics_consumer_service_transaction, mock_db, make_mock_result):
    mock_db.execute = AsyncMock(return_value=(make_mock_result(None)))
    result = await get_analytics_consumer_service_transaction.handle_budget_limit_updated()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

async def test_handle_user_deleted(get_analytics_consumer_service_transaction, mock_db, mock_redis, make_mock_result, make_mock_results, fake_scalars_monthly_stats, fake_user_budget):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_results(fake_scalars_monthly_stats),
        make_mock_result(fake_user_budget)
    ])
    result = await get_analytics_consumer_service_transaction.handle_user_deleted()
    assert mock_db.delete.call_count == 4
    mock_db.commit.assert_called_once()
    mock_redis.delete.assert_called()

async def test_handle_user_deleted_budget_limit_not_found(get_analytics_consumer_service_transaction, mock_db, mock_redis, make_mock_result, make_mock_results, fake_scalars_monthly_stats):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_results(fake_scalars_monthly_stats),
        make_mock_result(None)
    ])
    result = await get_analytics_consumer_service_transaction.handle_user_deleted()
    assert mock_db.delete.call_count == 3
    mock_db.commit.assert_called_once()
    mock_redis.delete.assert_called()

async def fake_scan_iter_with_keys(*keys):
    async def _iter(match=None):
        for key in keys:
            yield key
    return _iter

async def test_cache_delete_handle(get_analytics_consumer_service_transaction, mock_redis):
    mock_redis.scan_iter = await fake_scan_iter_with_keys(
        'range_stats:1:24305:24321',
        'range_stats:1:24311:24323',
        'range_stats:1:24302:24305'
    )
    result = await get_analytics_consumer_service_transaction.cache_delete_handle()
    assert mock_redis.delete.call_count == 4

@patch('services.analytics_consumer_core.publish_analytics_events', new_callable=AsyncMock)
@patch('services.analytics_consumer_core.datetime')
async def test_budget_exceed_check(mock_datetime, mock_publish, get_analytics_consumer_service_transaction, mock_db, mock_rabbitmq, make_mock_result, fake_mothly_stats, fake_user_budget):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(300000),
        make_mock_result(250000),
        make_mock_result(None)
    ])
    mock_datetime.now.return_value = datetime(2026, 7, 4)
    mock_datetime.fromisoformat = datetime.fromisoformat
    result = await get_analytics_consumer_service_transaction.budget_exceed_check()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once()
    publish_event = mock_publish.call_args.args
    assert publish_event[0] == 'exceed'
    assert publish_event[1] == 1
    assert publish_event[2] == mock_rabbitmq

@patch('services.analytics_consumer_core.datetime')
async def test_budget_exceed_check_budget_not_exceed(mock_datetime, get_analytics_consumer_service_transaction, mock_db, make_mock_result, fake_mothly_stats, fake_user_budget, fake_budget_exceed_notification):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(120000),
        make_mock_result(250000),
        make_mock_result(fake_budget_exceed_notification)
    ])
    mock_datetime.now.return_value = datetime(2026, 7, 4)
    mock_datetime.fromisoformat = datetime.fromisoformat
    result = await get_analytics_consumer_service_transaction.budget_exceed_check()
    mock_db.add.assert_not_called()
    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()

@patch('services.analytics_consumer_core.datetime')
async def test_budget_exceed_check_continue_exceed(mock_datetime, get_analytics_consumer_service_transaction, mock_db, make_mock_result, fake_mothly_stats, fake_user_budget, fake_budget_exceed_notification):
    mock_db.execute = AsyncMock(side_effect=[
        make_mock_result(300000),
        make_mock_result(250000),
        make_mock_result(fake_budget_exceed_notification)
    ])
    mock_datetime.now.return_value = datetime(2026, 7, 4)
    mock_datetime.fromisoformat = datetime.fromisoformat
    result = await get_analytics_consumer_service_transaction.budget_exceed_check()
    mock_db.add.assert_not_called()
    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()