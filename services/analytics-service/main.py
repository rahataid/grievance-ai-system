import asyncio
import json
import aio_pika
from app.config import RABBIT_URL, EXCHANGE, QUEUE, IN_KEY


async def process(message, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        print("📊 analytics update:", {
            "sentiment": data.get("sentiment"),
            "category": data.get("category")
        })


async def main():
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()

    exchange = await ch.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await ch.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=IN_KEY)

    await queue.consume(lambda m: process(m, exchange))

    print("📊 analytics running")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())