# Persistence Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE = "grievance.events"

QUEUE = "persistence.write_queue"

IN_KEY = "urgency.derived"