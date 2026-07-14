from pydantic import BaseModel, ConfigDict

class MonthlyStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    month: int
    category: str
    transaction_type: str
    total_amount: int