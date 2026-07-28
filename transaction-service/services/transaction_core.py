from models import Transaction
from sqlalchemy import select
from enums import TransactionType, ExpenseCategory, IncomeCategory
from publisher import publish_transaction_events
import logging

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    async def create_transaction(self, amount, transaction_type, category, description):
        create_transaction = Transaction(
            user_id = self.user_id, 
            amount = amount, 
            transaction_type = transaction_type, 
            category = category, 
            description = description
            )
        self.db.add(create_transaction)
        await self.db.commit()
        await self.db.refresh(create_transaction)
        logger.info(f'Transaction {create_transaction.id} by user {self.user_id} successfully created')
        await publish_transaction_events(
                'created', 
                self.user_id, 
                amount=amount, 
                transaction_type=transaction_type, 
                category=category, 
                created_at=create_transaction.created_at
                )
        return create_transaction

    async def get_transactions(self, page, page_size):
        transactions = await self.db.execute(select(Transaction).where(Transaction.user_id == self.user_id).limit(page_size).offset((page-1)*page_size))
        get_transactions = transactions.scalars().all()
        return get_transactions

    async def delete_transaction(self, transaction_id):
        transaction_is_exist = await self.db.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == self.user_id)) 
        db_transaction = transaction_is_exist.scalar_one_or_none()
        if db_transaction is None:
            logger.warning(f'Transaction {transaction_id} not found')
            raise TransactionNotFound('Transaction not found')
        await self.db.delete(db_transaction)
        await self.db.commit()
        logger.info(f'Transaction {transaction_id} successfully deleted')
        await publish_transaction_events(
                'deleted', 
                self.user_id, 
                amount=db_transaction.amount, 
                transaction_type=db_transaction.transaction_type, 
                category=db_transaction.category, 
                created_at=db_transaction.created_at
                )

    async def update_transaction(self, transaction_id, transaction_update_request):
        transaction_is_exist = await self.db.execute(select(Transaction).where(Transaction.user_id == self.user_id, Transaction.id == transaction_id))
        db_transaction = transaction_is_exist.scalar_one_or_none()
        if db_transaction is None:
            logger.warning(f'Transaction {transaction_id} not found')
            raise TransactionNotFound('Transaction not found')
        recent_amount, recent_type = db_transaction.amount, db_transaction.transaction_type
        transaction_update_dump = transaction_update_request.model_dump(exclude_unset=True)
        final_type = transaction_update_request.transaction_type if transaction_update_request.transaction_type is not None else db_transaction.transaction_type
        final_category = transaction_update_dump.get('category', db_transaction.category)
        if final_type == TransactionType.EXPENSE:
            if final_category not in [category for category in ExpenseCategory]:
                raise InvalidCategory('Invalid transaction category')
        else:
            if final_category not in [category for category in IncomeCategory]:
                raise InvalidCategory('Invalid transaction category')
        transaction_update_dump_items = transaction_update_dump.items()
        for item, value in transaction_update_dump_items:
            setattr(db_transaction, item, value)
        await self.db.commit()
        logger.info(f'Transaction {transaction_id} successfully updated')
        await publish_transaction_events(
            'updated', 
            self.user_id, 
            amount=transaction_update_dump.get('amount', db_transaction.amount), 
            transaction_type=transaction_update_dump.get('transaction_type', db_transaction.transaction_type), 
            category=transaction_update_dump.get('category', db_transaction.category), 
            created_at=db_transaction.created_at, 
            recent_amount=recent_amount, 
            recent_type=recent_type)
        return db_transaction   

class TransactionNotFound(Exception):
    pass

class InvalidCategory(Exception):
    pass