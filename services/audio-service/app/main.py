# Entry point for Audio Service
import asyncio
import json
import aio_pika

from app.config import RABBIT_URL, EXCHANGE_NAME, AUDIO_UPLOADED
from app.processor.audio_processor import convert_to_wav
from app.utils.file_handler import save_file


QUEUE_NAME = "audio.upload_queue"


async def process_message(message: aio_pika.IncomingMessage, exchange):
    async with message.process():
        data = json.loads(message.body.decode())

        filename = data["filename"]
        audio_bytes = data["audio_bytes"].encode("latin1")

        # 1. Save file
        file_path = save_file(audio_bytes, filename)

        # 2. Convert
        wav_path = convert_to_wav(file_path)

        # 3. Update payload
        data["audio_path"] = wav_path
        data["event"] = AUDIO_UPLOADED

        # 4. Publish to next stage
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=AUDIO_UPLOADED
        )

        print(f"Processed audio → {wav_path}")


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

    # 👇 This queue listens for raw uploads
    await queue.bind(exchange, routing_key="audio.raw")

    await queue.consume(lambda msg: process_message(msg, exchange))

    print("🎧 Audio service running...")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())