RABBIT_URL = "amqp://guest:guest@localhost/"
EXCHANGE_NAME = "grievance.events"

ROUTING_KEYS = {
    "audio_uploaded": "audio.uploaded",
    "transcription_completed": "transcription.completed",
}
