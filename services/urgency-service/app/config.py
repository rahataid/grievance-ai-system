# Urgency Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE = "grievance.events"

QUEUE = "urgency.queue"

IN_KEY = "nlp.analyzed"
OUT_KEY = "urgency.derived"
