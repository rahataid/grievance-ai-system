import json
from uuid import uuid4

import aio_pika
from fastapi import APIRouter, File, HTTPException, Security, UploadFile, status

from app.config import RABBIT_URL, EXCHANGE_NAME, ENTRY_ROUTING_KEY
from app.schemas import (
    AudioStatus,
    PipelineStage,
    UploadAudioResponse,
    AudioStatusResponse,
    GrievanceData,
)
from services.auth_service.app.api_keys import API_KEY_HEADER
from shared.utils.logger import get_queue_logger

queue_logger = get_queue_logger()
router = APIRouter(prefix="/audio", tags=["Audio"])

async def _publish_audio_event(payload: dict) -> None:
    queue_logger.info(
        "Opening RabbitMQ connection",
        extra={
            "service": "api-gateway",
            "exchange": EXCHANGE_NAME,
            "routing_key": ENTRY_ROUTING_KEY,
            "event": "publish.start",
        },
    )
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    queue_logger.info(
        "Exchange ready for publish",
        extra={
            "service": "api-gateway",
            "exchange": EXCHANGE_NAME,
            "routing_key": ENTRY_ROUTING_KEY,
            "event": "exchange.declared",
        },
    )

    try:
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=ENTRY_ROUTING_KEY,
        )
        queue_logger.info(
            "Exchange publish success",
            extra={
                "service": "api-gateway",
                "exchange": EXCHANGE_NAME,
                "routing_key": ENTRY_ROUTING_KEY,
                "event": "publish.success",
                "request_id": payload.get("request_id"),
            },
        )
    finally:
        await connection.close()


@router.post(
    "",
    response_model=UploadAudioResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an audio file for grievance processing",
    responses={401: {"description": "Unauthorized"}},
)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file to process"),
    _api_key: str | None = Security(API_KEY_HEADER),
):
    """
    Upload an audio file. The file is queued for the processing pipeline.
    Returns a unique `audio_id` that can be used to poll the processing status.
    """
    audio_bytes = await file.read()
    audio_id = str(uuid4())

    payload = {
        "request_id": audio_id,
        "filename": file.filename or f"{audio_id}.wav",
        "audio_bytes": audio_bytes.decode("latin1"),
    }

    queue_logger.info(
        "Publishing audio upload event",
        extra={
            "service": "api-gateway",
            "source": "upload_audio",
            "queue_request_id": audio_id,
            "queue_filename": payload["filename"],
            "exchange": EXCHANGE_NAME,
            "queue_routing_key": ENTRY_ROUTING_KEY,
            "event": "publish.attempt",
        },
    )

    try:
        await _publish_audio_event(payload)
    except Exception as exc:
        queue_logger.error(
            "Failed to publish audio event",
            exc_info=True,
            extra={
                "service": "api-gateway",
                "source": "upload_audio",
                "queue_request_id": audio_id,
                "queue_filename": payload["filename"],
                "exchange": EXCHANGE_NAME,
                "queue_routing_key": ENTRY_ROUTING_KEY,
                "event": "publish.failure",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish audio: {exc}",
        ) from exc

    queue_logger.info(
        "Published audio upload event",
        extra={
            "service": "api-gateway",
            "source": "upload_audio",
            "queue_request_id": audio_id,
            "queue_filename": payload["filename"],
            "exchange": EXCHANGE_NAME,
            "queue_routing_key": ENTRY_ROUTING_KEY,
            "event": "publish.success",
        },
    )

    return UploadAudioResponse(
        audio_id=audio_id,
        status=AudioStatus.uploaded,
    )


@router.get(
    "/{audio_id}",
    response_model=AudioStatusResponse,
    summary="Get audio processing status and results",
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Audio not found"},
        500: {"description": "Processing error"},
    },
)
async def get_audio_status(
    audio_id: str,
    _api_key: str | None = Security(API_KEY_HEADER),
):
    """
    Retrieve the current pipeline stage and any available processed data
    for the given `audio_id`.

    Poll this endpoint until `status` is `completed` or `failed`.
    """
    # TODO: query persistence-service for the audio record
    return AudioStatusResponse(
        audio_id=audio_id,
        status=AudioStatus.processing,
        current_stage=PipelineStage.asr_service,
        url="/path/audio.wav",
        grievance=GrievanceData(
            transcript="text if available",
            language="en",
            sentiment="negative",
            category="health",
            urgency="high",
            severity_score=0.87,
        ),
    )
