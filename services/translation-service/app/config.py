# Translation Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = "grievance.events"

QUEUE_NAME = "translation.queue"

ROUTING_KEY_IN = "language.detected"
ROUTING_KEY_OUT = "text.translated"