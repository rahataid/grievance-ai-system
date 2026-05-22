# Entry point for NLP Service
import asyncio
import json
import aio_pika

from app.config import (
    RABBIT_URL,
    EXCHANGE_NAME,
    QUEUE_NAME,
    ROUTING_KEY_IN,
    ROUTING_KEY_OUT
)
from app.processor.main import analyze
from shared.database.session import SessionLocal
from shared.utils.logger import get_queue_logger
from shared.database.crud import audio as audio_crud

queue_logger = get_queue_logger()


async def process_message(message: aio_pika.IncomingMessage, exchange):
    async with message.process():
        data = json.loads(message.body.decode())
        audio_id = data.get("request_id")

        async with SessionLocal() as db:
            await audio_crud.update_audio(
                db=db,
                audio_id=audio_id,
                status="processing",
                current_stage="nlp_service",
            )

        text = data.get("translated_text") or data.get("transcript")
        category = data.get("category")

        if not text:
            print("❌ No text found for NLP")
            return

        # 🧠 NLP processing
        result = await analyze(text, category)

        # merge results into payload
        data.update(result)
        data["event"] = ROUTING_KEY_OUT

        # 🚀 publish downstream
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=ROUTING_KEY_OUT
        )

        queue_logger.info(
            "Published NLP event",
            extra={
                "service": "nlp-service",
                "queue": QUEUE_NAME,
                "exchange": EXCHANGE_NAME,
                "routing_key": ROUTING_KEY_OUT,
                "request_id": data.get("request_id"),
                "event": "publish.success",
            },
        )

        print(f"🧠 NLP done → {result}")


async def main():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    await channel.set_qos(prefetch_count=1)

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True
    )

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    # 👇 listens to translated text
    await queue.bind(exchange, routing_key=ROUTING_KEY_IN)
    queue_logger.info(
        "Queue bound to exchange",
        extra={
            "service": "nlp-service",
            "queue": QUEUE_NAME,
            "exchange": EXCHANGE_NAME,
            "routing_key": ROUTING_KEY_IN,
            "event": "queue.bind",
        },
    )

    await queue.consume(lambda msg: process_message(msg, exchange))

    print("🧠 NLP service running...")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())