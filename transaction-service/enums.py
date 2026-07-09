from enum import StrEnum

class ExpenseCategory(StrEnum):
    RESTAURANT = 'Restaurant'
    PRODUCTS = 'Products'
    TRANSPORT = 'Transport'
    TRAVEL = 'Travel'
    TAXES = 'Taxes'
    HEALTHCARE = 'Healthcare'
    HOUSEHOLD = 'Household'
    ENTERTAINMENT = 'Entertainment'
    PERSONAL_CARE = 'Personal care'
    HOBBY = 'Hobby'
    SPORT = 'Sport'
    CLOTHES = 'Clothes'
    PETS = 'Pets'
    TRANSFERS = 'Transfers'
    INSURANCE = 'Insurance'
    CREDIT = 'Credit'
    DEBTS = 'Debts'
    INVESTMENTS = 'Investments'
    SUBSCRIPTIONS = 'Subscriptions'
    GIFTS = 'Gifts'
    OTHER = 'Other'

class IncomeCategory(StrEnum):
    SALARY = 'Salary'
    TRANSFERS = 'Transfers'
    REFUND = 'Refund'
    OTHER = 'Other'

class TransactionType(StrEnum):
    EXPENSE = 'Expense'
    INCOME = 'Income'

def GeneralCategories():
    category_pairs = set()
    for expense_item in ExpenseCategory:
        category_pairs.add((expense_item.name, expense_item.value))
    for income_item in IncomeCategory:
        category_pairs.add((income_item.name, income_item.value))
    return StrEnum('Categories', list(category_pairs))