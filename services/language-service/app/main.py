# Entry point for Language Service
import asyncio
import json
import aio_pika

from app.config import (
    RABBIT_URL,
    EXCHANGE_NAME,
    QUEUE_NAME,
    ROUTING_KEY_IN,
    ROUTING_KEY_EN,
    ROUTING_KEY_NON_EN
)
from app.processor.detector import detect_language


async def process_message(message: aio_pika.IncomingMessage, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        text = data.get("transcript")

        if not text:
            print("❌ No transcript found")
            return

        # 🌍 Detect language
        lang = detect_language(text)

        data["language"] = lang

        # 🔀 Branching logic
        if lang == "en":
            routing_key = ROUTING_KEY_EN
            print("➡️ English detected → skipping translation")
        else:
            routing_key = ROUTING_KEY_NON_EN
            print("🌐 Non-English → sending to translation")

        data["event"] = routing_key

        # 🚀 Publish next event
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )


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

    # 👇 listens to ASR output
    await queue.bind(exchange, routing_key=ROUTING_KEY_IN)

    await queue.consume(lambda msg: process_message(msg, exchange))

    print("🌍 Language service running...")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())