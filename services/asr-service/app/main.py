# Entry point for ASR Service
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
from app.processor.asr import transcribe


async def process_message(message: aio_pika.IncomingMessage, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        audio_path = data.get("audio_path")

        if not audio_path:
            print("❌ No audio_path found")
            return

        # 🎤 Transcribe
        transcript = await transcribe(audio_path)

        # Update payload
        data["transcript"] = transcript
        data["event"] = ROUTING_KEY_OUT

        # 🚀 Send to next stage
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=ROUTING_KEY_OUT
        )

        print(f"✅ Transcribed: {transcript}")


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

    # 👇 IMPORTANT binding
    await queue.bind(exchange, routing_key=ROUTING_KEY_IN)

    await queue.consume(lambda msg: process_message(msg, exchange))

    print("🧠 ASR service running...")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())