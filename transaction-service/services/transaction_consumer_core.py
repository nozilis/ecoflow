from models import Transaction
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class TransactionConsumerService:
    def __init__(self, data, session, redis):
        self.data = data
        self.session = session
        self.redis = redis

    async def handle_user_deleted(self):
        user_id = self.data['user_id']
        user_transactions_is_exist = await self.session.execute(select(Transaction).where(Transaction.user_id == user_id))
        db_user_transactions = user_transactions_is_exist.scalars().all()
        if db_user_transactions:
            for transaction in db_user_transactions:
                await self.session.delete(transaction)
            await self.session.commit()
            logger.info(f'Transactions for user {user_id} successfully deleted')
            await self.cache_delete_handle()

    async def cache_delete_handle(self):
        user_id = self.data['user_id']
        async for cache_key in self.redis.scan_iter(match=f'transactions:{user_id}:*'):
            await self.redis.delete(cache_key)
        logger.info(f'Cache for user {user_id} successfully deleted')