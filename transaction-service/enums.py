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