import pytest
from unittest.mock import AsyncMock, MagicMock
from services.analytics_core import AnalyticsService
from models import MonthlyStats
import json

@pytest.fixture
def get_analytics_service(mock_db, mock_redis):
    return AnalyticsService(mock_db, 1, mock_redis)

@pytest.fixture
def fake_scalars_monthly_stats():
    return [
        MonthlyStats(id=3, user_id=1, year=2026, month=7, category='Products', transaction_type='Expense', total_amount=25000),
        MonthlyStats(id=2, user_id=1, year=2026, month=7, category='Salary', transaction_type='Income', total_amount=37000),
        MonthlyStats(id=1, user_id=1, year=2026, month=7, category='Restaurant', transaction_type='Expense', total_amount=15000)
    ]

@pytest.fixture
def fake_monthly_cache_response():
    data = [
    {
        "id": 3,
        "user_id": 1,
        "year": 2026,
        "month": 7,
        "category": "Products",
        "transaction_type": "Expense",
        "total_amount": 25000
    },
    {
        "id": 2,
        "user_id": 1,
        "year": 2026,
        "month": 7,
        "category": "Salary",
        "transaction_type": "Income",
        "total_amount": 37000
    },
    {
        "id": 1,
        "user_id": 1,
        "year": 2026,
        "month": 7,
        "category": "Restaurant",
        "transaction_type": "Expense",
        "total_amount": 15000
    }
    ]
    return json.dumps(data)

@pytest.fixture
def fake_yearly_stats():
    return [
        {'year': 2026, 'category': 'Products', 'total_year_amount': 150000},
        {'year': 2026, 'category': 'Salary', 'total_year_amount': 800000},
    ]

@pytest.fixture
def fake_yearly_cache_response():
    data = [
    {
        'year': 2026, 
        'category': 'Products', 
        'total_year_amount': 150000
    },
    {
        'year': 2026, 
        'category': 'Salary', 
        'total_year_amount': 800000
    }
    ]
    return json.dumps(data)

@pytest.fixture
def fake_range_stats():
    return [
        {'category': 'Products', 'total_range_amount': 290000},
        {'category': 'Salary', 'total_range_amount': 1600000}, 
    ]

@pytest.fixture
def fake_range_stats_cache_response():
    data = [
    {
        'category': 'Products', 
        'total_range_amount': 290000
    },
    {
        'category': 'Salary', 
        'total_range_amount': 1600000
    }, 
    ]
    return json.dumps(data)

@pytest.fixture
def make_mock_mappings():
    def _make(return_value):
        result = MagicMock()
        result.mappings.return_value.all.return_value = return_value
        return result
    return _make

async def test_get_monthly_stats(get_analytics_service, mock_db, mock_redis, make_mock_results, fake_scalars_monthly_stats):
    mock_db.execute = AsyncMock(return_value=make_mock_results(fake_scalars_monthly_stats))
    mock_redis.get.return_value = None
    result = await get_analytics_service.get_monthly_stats(7, 2026)
    data = mock_redis.set.call_args.args
    assert data[0] == 'monthly_stats:1:7:2026'
    assert data[2] == 300
    assert result

async def test_get_monthly_stats_cache_response(get_analytics_service, mock_db, mock_redis, fake_monthly_cache_response):
    mock_redis.get = AsyncMock(return_value=fake_monthly_cache_response)
    result = await get_analytics_service.get_monthly_stats(7, 2026)
    assert result
    mock_redis.set.assert_not_called()
    mock_db.execute.assert_not_called()

async def test_get_yearly_stats(get_analytics_service, mock_db, mock_redis, make_mock_mappings, fake_yearly_stats):
    mock_db.execute = AsyncMock(return_value=make_mock_mappings(fake_yearly_stats))
    mock_redis.get.return_value = None
    result = await get_analytics_service.get_yearly_stats(2026)
    data = mock_redis.set.call_args.args
    assert data[0] == 'yearly_stats:1:2026'
    assert data[2] == 300
    assert result

async def test_get_yearly_stats_cache_response(get_analytics_service, mock_db, mock_redis, fake_yearly_cache_response):
    mock_redis.get = AsyncMock(return_value=fake_yearly_cache_response)
    result = await get_analytics_service.get_yearly_stats(2026)
    assert result
    mock_redis.set.assert_not_called()
    mock_db.execute.assert_not_called()

async def test_get_range_stats(get_analytics_service, mock_db, mock_redis, make_mock_mappings, fake_range_stats):
    mock_db.execute = AsyncMock(return_value=make_mock_mappings(fake_range_stats))
    mock_redis.get.return_value = None
    result = await get_analytics_service.get_range_stats(2025, 9, 2026, 10)
    data = mock_redis.set.call_args.args
    assert data[0] == 'range_stats:1:24309:24322'
    assert data[2] == 300
    assert result

async def test_get_range_stats_cache_response(get_analytics_service, mock_db, mock_redis, fake_range_stats_cache_response):
    mock_redis.get = AsyncMock(return_value=fake_range_stats_cache_response)
    result = await get_analytics_service.get_range_stats(2025, 9, 2026, 10)
    assert result
    mock_redis.get.assert_called_once_with('range_stats:1:24309:24322')
    mock_redis.set.assert_not_called()
    mock_db.execute.assert_not_called()