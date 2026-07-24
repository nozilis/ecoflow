from fastapi import APIRouter, status, Depends, HTTPException
from dependencies import get_current_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import Transaction
from schemas import TransactionCreate, TransactionResponse, TransactionUpdate
from sqlalchemy import select
from enums import TransactionType, ExpenseCategory, IncomeCategory
from publisher import publish_transaction_events

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction: TransactionCreate, user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    create_transaction = Transaction(user_id = user_id, amount = transaction.amount, transaction_type = transaction.transaction_type, category = transaction.category, description = transaction.description)
    db.add(create_transaction)
    await db.commit()
    await db.refresh(create_transaction)
    await publish_transaction_events('created', user_id, amount=transaction.amount, transaction_type=transaction.transaction_type, category=transaction.category, created_at=create_transaction.created_at)
    return TransactionResponse.model_validate(create_transaction)

@router.get('/', status_code=status.HTTP_200_OK)
async def get_transactions(user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db), page: int = 1, page_size: int = 20):
    result = await db.execute(select(Transaction).where(Transaction.user_id == user_id).limit(page_size).offset((page-1)*page_size))
    db_transactions = result.scalars().all()
    return [TransactionResponse.model_validate(t) for t in db_transactions]

@router.delete('/{transaction_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: int, user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_transaction_is_exist = await db.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)) 
    db_transaction = db_transaction_is_exist.scalar_one_or_none()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Транзакция не найдена')
    await db.delete(db_transaction)
    await db.commit()
    await publish_transaction_events('deleted', user_id, amount=db_transaction.amount, transaction_type=db_transaction.transaction_type, category=db_transaction.category, created_at=db_transaction.created_at)

@router.patch('/{transaction_id}', status_code=status.HTTP_200_OK)
async def update_transaction(transaction_id: int, transaction_update_request: TransactionUpdate, user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_transaction_is_exist = await db.execute(select(Transaction).where(Transaction.user_id == user_id, Transaction.id == transaction_id))
    db_transaction = db_transaction_is_exist.scalar_one_or_none()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Транзакция не найдена')
    transaction_update_dump = transaction_update_request.model_dump(exclude_unset=True)
    final_type = transaction_update_request.transaction_type if transaction_update_request.transaction_type is not None else db_transaction.transaction_type
    final_category = transaction_update_dump.get('category', db_transaction.category)
    if final_type == TransactionType.EXPENSE:
        if final_category not in [category for category in ExpenseCategory]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Категория транзакции заполнена неверно!')
    else:
        if final_category not in [category for category in IncomeCategory]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Категория транзакции заполнена неверно!')
    transaction_update_dump_items = transaction_update_dump.items()
    for item, value in transaction_update_dump_items:
        setattr(db_transaction, item, value)
    await db.commit()
    await publish_transaction_events('updated', user_id, amount=transaction_update_dump.get('amount', db_transaction.amount), transaction_type=transaction_update_dump.get('transaction_type', db_transaction.transaction_type), category=transaction_update_dump.get('category', db_transaction.category), created_at=db_transaction.created_at)
    return TransactionResponse.model_validate(db_transaction)