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


async def process_message(message: aio_pika.IncomingMessage, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        text = data.get("translated_text") or data.get("transcript")

        if not text:
            print("❌ No text found for NLP")
            return

        # 🧠 NLP processing
        result = await analyze(text)

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

    await queue.consume(lambda msg: process_message(msg, exchange))

    print("🧠 NLP service running...")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())