from fastapi import APIRouter, status, Depends, HTTPException
from dependencies import get_current_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import Transaction
from schemas import TransactionCreate, TransactionResponse
from sqlalchemy import select

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)

@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction: TransactionCreate, user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    to_db_transaction = Transaction(user_id = user_id, amount = transaction.amount, transaction_type = transaction.transaction_type, category = transaction.category, description = transaction.description)
    db.add(to_db_transaction)
    await db.commit()
    return TransactionResponse.model_validate(to_db_transaction)

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