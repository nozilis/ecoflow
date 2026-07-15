from fastapi import APIRouter, status, Depends
from dependencies import get_db, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import MonthlyStats
from schemas import MonthlyStatsResponse
from datetime import datetime

router = APIRouter(
    prefix='/analytics',
    tags=['analytics']
)

@router.get('/monthly_stats', status_code=status.HTTP_200_OK)
async def get_monthly_stats(month: int = None, year: int = None, db: AsyncSession = Depends(get_db), user: int = Depends(get_current_user)):
    now = datetime.now()
    if month is None:
       month = now.month
    if year is None:
        year = now.year
    result = await db.execute(select(MonthlyStats).where(MonthlyStats.user_id == user, MonthlyStats.month == month, MonthlyStats.year == year))
    db_monthly_stats = result.scalars().all()
    return [MonthlyStatsResponse.model_validate(s) for s in db_monthly_stats]