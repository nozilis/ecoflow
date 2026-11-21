from dependencies import get_analytics_service
from fastapi import APIRouter, Depends, status
from schemas import MonthlyStatsResponse, RangeStatsResponse, YearlyStatsResponse
from services.analytics_core import AnalyticsService

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.get('/monthly_stats', status_code=status.HTTP_200_OK)
async def get_monthly_stats(
    month: int | None = None,
    year: int | None = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[MonthlyStatsResponse]:
    monthly_stats = await analytics_service.get_monthly_stats(month=month, year=year)
    return monthly_stats


@router.get('/yearly_stats', status_code=status.HTTP_200_OK)
async def get_yearly_stats(
    year: int | None = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[YearlyStatsResponse]:
    yearly_stats = await analytics_service.get_yearly_stats(year=year)
    return yearly_stats


@router.get('/range_stats', status_code=status.HTTP_200_OK)
async def get_range_stats(
    start_year: int | None = None,
    start_month: int | None = None,
    end_year: int | None = None,
    end_month: int | None = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[RangeStatsResponse]:
    range_stats = await analytics_service.get_range_stats(
        start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month
    )
    return range_stats
