from fastapi import APIRouter, status, Depends
from dependencies import get_analytics_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import MonthlyStats
from schemas import MonthlyStatsResponse, YearlyStatsResponse, RangeStatsResponse
from services.analytics_core import AnalyticsService
from datetime import datetime

router = APIRouter(
    prefix='/analytics',
    tags=['analytics']
)

@router.get('/monthly_stats', status_code=status.HTTP_200_OK)
async def get_monthly_stats(
    month: int = None, 
    year: int = None, 
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> list[MonthlyStatsResponse]:
    monthly_stats = await analytics_service.get_monthly_stats(
        month=month, 
        year=year
        )
    return [MonthlyStatsResponse.model_validate(s) for s in monthly_stats]

@router.get('/yearly_stats', status_code=status.HTTP_200_OK)
async def get_yearly_stats(
    year: int = None, 
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> list[YearlyStatsResponse]:
    yearly_stats = await analytics_service.get_yearly_stats(year=year)
    return [YearlyStatsResponse.model_validate(row) for row in yearly_stats.mappings().all()]

@router.get('/range_stats', status_code=status.HTTP_200_OK)
async def get_range_stats(
    start_year: int = None, 
    start_month: int = None, 
    end_year: int = None, 
    end_month: int = None, 
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> list[RangeStatsResponse]:
    range_stats = await analytics_service.get_range_stats(
        start_year=start_year,
        start_month=start_month,
        end_year=end_year,
        end_month=end_month
        )
    return [RangeStatsResponse.model_validate(row) for row in range_stats.mappings().all()]