# Entry point for Persistence Service
import asyncio
import json
import aio_pika
from app.config import RABBIT_URL, EXCHANGE, QUEUE, IN_KEY
from app.processor.persistance import save_to_db


async def process(message, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        await save_to_db(data)

        print("✅ persisted:", data["request_id"])


async def main():
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=1)

    exchange = await ch.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await ch.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=IN_KEY)

    await queue.consume(lambda m: process(m, exchange))

    print("💾 persistence running")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())