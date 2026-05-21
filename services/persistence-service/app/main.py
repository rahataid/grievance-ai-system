# Entry point for Persistence Service
import asyncio
import json
import aio_pika
from app.config import RABBIT_URL, EXCHANGE, QUEUE, IN_KEY
from app.processor.persistance import save_to_db
from shared.utils.logger import get_queue_logger

queue_logger = get_queue_logger()


async def process(message, exchange):
    async with message.process():
        data = json.loads(message.body.decode())
        audio_id = data.get("request_id")

        try:
            await save_to_db(data)

            queue_logger.info(
                "Persisted message",
                extra={
                    "service": "persistence-service",
                    "queue": QUEUE,
                    "exchange": EXCHANGE,
                    "routing_key": IN_KEY,
                    "request_id": audio_id,
                    "event": "process.success",
                },
            )

            print("✅ persisted:", audio_id)

        except Exception as e:
            queue_logger.error(
                "Failed to persist message",
                exc_info=True,
                extra={
                    "service": "persistence-service",
                    "queue": QUEUE,
                    "exchange": EXCHANGE,
                    "routing_key": IN_KEY,
                    "request_id": audio_id,
                    "event": "process.failure",
                    "error": str(e),
                },
            )
            print(f"❌ Failed to persist: {e}")
            raise


async def main():
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=1)

    exchange = await ch.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await ch.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=IN_KEY)
    queue_logger.info(
        "Queue bound to exchange",
        extra={
            "service": "persistence-service",
            "queue": QUEUE,
            "exchange": EXCHANGE,
            "routing_key": IN_KEY,
            "event": "queue.bind",
        },
    )

    await queue.consume(lambda m: process(m, exchange))

    print("💾 persistence running")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())