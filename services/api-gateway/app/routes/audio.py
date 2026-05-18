import json
from uuid import uuid4

import aio_pika
from fastapi import APIRouter, Depends, File, HTTPException, Security, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import RABBIT_URL, EXCHANGE_NAME, ENTRY_ROUTING_KEY
from app.schemas import (
    AudioResponse,
    AudioUpdateRequest,
    AudioStatus,
    PipelineStage,
    UploadAudioResponse,
    AudioStatusResponse,
    GrievanceData,
    MessageResponse,
)
from shared.database.session import get_db        
from shared.database.models.audio import Audio
from services.auth_service.app.api_keys import API_KEY_HEADER
from services.crud import audio as audio_crud

router = APIRouter(prefix="/audio", tags=["Audio"])


async def _publish_audio_event(payload: dict) -> None:
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    try:
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=ENTRY_ROUTING_KEY,
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
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an audio file and enqueue it for grievance processing.
    """
    audio_bytes = await file.read()
    audio_id = str(uuid4())
    filename = file.filename or f"{audio_id}.wav"

    payload = {
        "request_id": audio_id,
        "filename": filename,
        "audio_bytes": audio_bytes.decode("latin1"),
    }

    try:
        await _publish_audio_event(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish audio: {exc}",
        ) from exc

    # Persist to DB 
    audio_record = Audio(
        id=audio_id,
        app_id=_api_key.app_id if hasattr(_api_key, "app_id") else None, 
        url=f"/audio/{filename}",
        status=AudioStatus.uploaded.value,
        current_stage=PipelineStage.asr_service.value,
    )
    db.add(audio_record)
    await db.commit()

    return UploadAudioResponse(audio_id=audio_id, status=AudioStatus.uploaded)


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
    db: AsyncSession = Depends(get_db),
):
    """
    Return the processing status and latest grievance result for a specific audio record.
    """
    result = await db.execute(
        select(Audio)
        .where(Audio.id == audio_id)
        .options(selectinload(Audio.grievances))
    )
    audio = result.scalar_one_or_none()

    if audio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")

    grievance = audio.grievances[-1] if audio.grievances else None

    return AudioStatusResponse(
        audio_id=str(audio.id),
        status=AudioStatus(audio.status),
        current_stage=PipelineStage(audio.current_stage),
        url=audio.url,
        grievance=GrievanceData(
            transcript=grievance.transcript if grievance else None,
            language=grievance.language if grievance else None,
            sentiment=grievance.sentiment if grievance else None,
            category=grievance.category if grievance else None,
            urgency=grievance.urgency if grievance else None,
            severity_score=grievance.severity_score if grievance else None,
        ) if grievance else None,
    )


def _serialize_audio(audio: Audio) -> AudioResponse:
    return AudioResponse(
        id=str(audio.id),
        app_id=str(audio.app_id),
        url=audio.url,
        status=audio.status,
        current_stage=audio.current_stage,
    )


@router.get(
    "",
    response_model=list[AudioResponse],
    summary="List audio records",
    responses={401: {"description": "Unauthorized"}},
)
async def list_audio(
    app_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    _api_key: str | None = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
):
    """
    Return audio records for a specific application when `app_id` is provided, otherwise return all audio records.
    """
    if app_id:
        audios = await audio_crud.get_audios_by_app(db, app_id, skip=skip, limit=limit)
    else:
        audios = await audio_crud.get_all_audios(db, skip=skip, limit=limit)
    return [_serialize_audio(audio) for audio in audios]


@router.patch(
    "/{audio_id}",
    response_model=AudioResponse,
    summary="Update audio record",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "Audio not found"}},
)
async def update_audio(
    audio_id: str,
    body: AudioUpdateRequest,
    _api_key: str | None = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing audio record.
    """
    audio = await audio_crud.update_audio(
        db,
        audio_id,
        url=body.url,
        status=body.status,
        current_stage=body.current_stage,
    )
    if audio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")
    return _serialize_audio(audio)


@router.delete(
    "/{audio_id}",
    response_model=MessageResponse,
    summary="Delete audio record",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "Audio not found"}},
)
async def delete_audio(
    audio_id: str,
    _api_key: str | None = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an audio record by its identifier.
    """
    deleted = await audio_crud.delete_audio(db, audio_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")
    return MessageResponse(message="Audio deleted successfully")