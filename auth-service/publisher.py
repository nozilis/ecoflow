import aio_pika
from decouple import config
import json
from datetime import datetime

async def publish_event(message_body, routing_key):
    connection = await aio_pika.connect_robust(
        f"amqp://{config('RABBITMQ_DEFAULT_USER')}:{config('RABBITMQ_DEFAULT_PASS')}@rabbitmq/"
    )

    async with connection:
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

        print(f" Sent: {message_body}")
        
async def publish_user_events(event_type, user_id, **kwargs):
    data_dict = {'id': user_id, **kwargs}
    message_body = json.dumps(data_dict, default=lambda o: o.isoformat() if isinstance(o, datetime) else None).encode("utf-8")
    await publish_event(message_body, f'user.{event_type}')