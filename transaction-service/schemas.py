from pydantic import BaseModel, model_validator, ConfigDict
from typing import Optional, Self
from enums import TransactionType, ExpenseCategory, IncomeCategory
from datetime import datetime

class TransactionCreate(BaseModel):
    amount: int
    transaction_type: TransactionType
    category: Optional[ExpenseCategory | IncomeCategory] = 'Other'  #Union enum classes for typification
    description: Optional[str] = None

    @model_validator(mode='after')
    def check_category_type(self) -> Self:
        if self.transaction_type == TransactionType.EXPENSE:
            if self.category not in ExpenseCategory:
                raise ValueError('Категория транзакции заполнена неверно!')
        else:
            if self.category not in IncomeCategory:
                raise ValueError('Категория транзакции заполнена неверно!')
        return self
    
class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: int
    transaction_type: TransactionType
    category: ExpenseCategory | IncomeCategory
    description: Optional[str] = None
    created_at: datetime

class TransactionUpdate(BaseModel):
    amount: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[ExpenseCategory | IncomeCategory] = None
    description: Optional[str] = None