# ASR Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = "grievance.events"

QUEUE_NAME = "audio_transcription_queue"

ROUTING_KEY_IN = "audio.uploaded"
ROUTING_KEY_OUT = "transcription.completed"