# Language Service config
import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://sentiment:password@localhost:5672/")
EXCHANGE_NAME = "grievance.events"

QUEUE_NAME = "language.detect_queue"

ROUTING_KEY_IN = "transcription.completed"

# branching outputs
ROUTING_KEY_EN = "text.translated"       # skip translation
ROUTING_KEY_NON_EN = "language.detected" # go to translation