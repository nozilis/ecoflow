from pydantic import BaseModel, ConfigDict

class MonthlyStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    month: int
    category: str
    transaction_type: str
    total_amount: int

class YearlyStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    category: str
    total_year_amount: int