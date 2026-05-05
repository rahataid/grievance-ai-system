# NLP Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = "grievance.events"

QUEUE_NAME = "nlp.analysis_queue"

ROUTING_KEY_IN = "text.translated"
ROUTING_KEY_OUT = "nlp.analyzed"