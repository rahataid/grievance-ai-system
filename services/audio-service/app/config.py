# Audio Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = "grievance.events"

AUDIO_UPLOADED = "audio.uploaded"