import aio_pika
import json
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

async def publish_events(message_body, routing_key, connection):
    channel = await connection.channel()

    message = aio_pika.Message(
        body=message_body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )

    exchange = await channel.declare_exchange("ecoflow_events", aio_pika.ExchangeType.TOPIC, durable=True)

    await exchange.publish(
        message=message,
        routing_key=routing_key
    )

    logger.info(f'Sent: {message_body}')
    await channel.close()

async def publish_transaction_events(event_type, user_id, connection, **kwargs):
    data_dict = {'user_id': user_id, **kwargs} 
    message_body = json.dumps(data_dict, default=lambda o:o.value if isinstance(o, Enum) else (o.isoformat() if isinstance(o, datetime) else None)).encode("utf-8")
    await publish_events(message_body, f'transaction.{event_type}', connection)
    logger.info(f'Event {event_type} by user {user_id} successfully published')