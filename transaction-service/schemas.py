from pydantic import BaseModel, model_validator
from typing import Optional, Self
from enums import TransactionType, ExpenseCategory, IncomeCategory

class TransactionCreate(BaseModel):
    amount: int
    transaction_type: TransactionType
    category: ExpenseCategory | IncomeCategory  #Union enum classes for typification
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