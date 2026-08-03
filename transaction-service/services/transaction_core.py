from models import Transaction
from sqlalchemy import select
from enums import TransactionType, ExpenseCategory, IncomeCategory
from publisher import publish_transaction_events
from schemas import TransactionResponse
import json
import logging

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, db, user_id, redis, rabbitmq):
        self.db = db
        self.user_id = user_id
        self.redis = redis
        self.rabbitmq = rabbitmq

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
                self.rabbitmq, 
                amount=amount, 
                transaction_type=transaction_type, 
                category=category, 
                created_at=create_transaction.created_at
                )
        await self.cache_delete_handle()
        return create_transaction

    async def get_transactions(self, page, page_size):
        cache_key = f'transactions:{self.user_id}:{page}:{page_size}'
        cached_data = await self.redis.get(cache_key)
        if cached_data is not None:
            data = json.loads(cached_data)
            return data
        transactions = await self.db.execute(select(Transaction).where(Transaction.user_id == self.user_id).limit(page_size).offset((page-1)*page_size))
        get_transactions = transactions.scalars().all()
        db_transactions = [TransactionResponse.model_validate(item).model_dump() for item in get_transactions]
        data_to_cache = json.dumps(db_transactions)
        await self.redis.set(cache_key, data_to_cache, 300)
        return db_transactions

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
                self.rabbitmq,
                amount=db_transaction.amount, 
                transaction_type=db_transaction.transaction_type, 
                category=db_transaction.category, 
                created_at=db_transaction.created_at
                )
        await self.cache_delete_handle()

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
            self.rabbitmq,
            amount=transaction_update_dump.get('amount', db_transaction.amount), 
            transaction_type=transaction_update_dump.get('transaction_type', db_transaction.transaction_type), 
            category=transaction_update_dump.get('category', db_transaction.category), 
            created_at=db_transaction.created_at, 
            recent_amount=recent_amount, 
            recent_type=recent_type)
        await self.cache_delete_handle()
        return db_transaction   

    async def cache_delete_handle(self):
        async for cache_key in self.redis.scan_iter(match=f'transactions:{self.user_id}:*'):
            await self.redis.delete(cache_key)
            logger.info(f'Cache with key {cache_key} successfully deleted')

class TransactionNotFound(Exception):
    pass

class InvalidCategory(Exception):
    pass