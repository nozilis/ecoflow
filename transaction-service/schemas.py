from datetime import datetime
from typing import Self

from enums import ExpenseCategory, IncomeCategory, TransactionType
from pydantic import BaseModel, ConfigDict, model_validator


class TransactionCreate(BaseModel):
    amount: int
    transaction_type: TransactionType
    category: ExpenseCategory | IncomeCategory | None = None  # Union enum classes for typification
    description: str | None = None

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
    description: str | None = None
    created_at: datetime


class TransactionUpdate(BaseModel):
    amount: int | None = None
    transaction_type: TransactionType | None = None
    category: ExpenseCategory | IncomeCategory | None = None
    description: str | None = None
