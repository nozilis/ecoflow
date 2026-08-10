from pydantic import BaseModel, model_validator, ConfigDict
from typing import Optional, Self
from enums import TransactionType, ExpenseCategory, IncomeCategory
from datetime import datetime

class TransactionCreate(BaseModel):
    amount: int
    transaction_type: TransactionType
    category: Optional[ExpenseCategory | IncomeCategory] = None #Union enum classes for typification
    description: Optional[str] = None

    @model_validator(mode='after')
    def check_category_type(self) -> Self:
        if self.category:
            if self.transaction_type == TransactionType.EXPENSE:
                if not isinstance(self.category, ExpenseCategory):
                    raise ValueError('Invalid transaction category')
            else:
                if not isinstance(self.category, IncomeCategory):
                    raise ValueError('Invalid transaction category')
        else:
            if self.transaction_type == TransactionType.EXPENSE:
                self.category = ExpenseCategory.OTHER
            else:
                self.category = IncomeCategory.OTHER
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