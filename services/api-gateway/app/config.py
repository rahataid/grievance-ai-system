# API Gateway config
import os
from pathlib import Path

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "grievance.events")
ENTRY_ROUTING_KEY = "audio.raw"

BASE_DIR = os.getenv("BASE_DIR", Path(__file__).resolve().parent.parent.parent.parent)

