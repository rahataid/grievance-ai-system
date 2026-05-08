# API Gateway config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "grievance.events")
ENTRY_ROUTING_KEY = "audio.raw"
