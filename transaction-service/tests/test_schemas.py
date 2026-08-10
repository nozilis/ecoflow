import pytest
from schemas import TransactionCreate
from enums import ExpenseCategory, IncomeCategory, TransactionType
from pydantic import ValidationError

def test_expense_with_valid_category():
    transaction = TransactionCreate(
        amount=1000, 
        transaction_type=TransactionType.EXPENSE,
        category=ExpenseCategory.RESTAURANT
        )
    assert transaction.category in ExpenseCategory
    assert transaction.transaction_type == TransactionType.EXPENSE

def test_expense_with_invalid_category():
    with pytest.raises(ValidationError):
        transaction = TransactionCreate(
            amount=1000, 
            transaction_type=TransactionType.EXPENSE,
            category=IncomeCategory.SALARY
        )

def test_income_with_valid_category():
    transaction = TransactionCreate(
        amount=1000, 
        transaction_type=TransactionType.INCOME,
        category=IncomeCategory.REFUND
        )
    assert transaction.category in IncomeCategory
    assert transaction.transaction_type == TransactionType.INCOME

def test_income_with_invalid_category():
    with pytest.raises(ValidationError):
        transaction = TransactionCreate(
            amount=1000, 
            transaction_type=TransactionType.INCOME,
            category=ExpenseCategory.PRODUCTS
        )

@pytest.mark.parametrize('amount,transaction_type', [
    (5000, 'Expense'),
    (46000, 'Income')
])
def test_other_category_for_both_types(amount, transaction_type):
    transaction = TransactionCreate(
        amount=amount,
        transaction_type=transaction_type
    )
    assert transaction.category == 'Other'