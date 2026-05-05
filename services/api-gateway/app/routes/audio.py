from fastapi import APIRouter, Header, HTTPException, UploadFile, File, status
from typing import Optional

from app.schemas import (
    AudioStatus,
    PipelineStage,
    UploadAudioResponse,
    AudioStatusResponse,
    GrievanceData,
)

router = APIRouter(prefix="/audio", tags=["Audio"])


def _require_auth(x_api_key: Optional[str], authorization: Optional[str]) -> None:
    """Raise 401 if neither credential is supplied."""
    if not x_api_key and not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@router.post(
    "",
    response_model=UploadAudioResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an audio file for grievance processing",
    responses={401: {"description": "Unauthorized"}},
)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file to process"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
):
    """
    Upload an audio file. The file is queued for the processing pipeline.
    Returns a unique `audio_id` that can be used to poll the processing status.
    """
    _require_auth(x_api_key, authorization)
    # TODO: forward file to audio-service and publish to pipeline queue
    return UploadAudioResponse(
        audio_id="00000000-0000-0000-0000-000000000000",
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
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
):
    """
    Retrieve the current pipeline stage and any available processed data
    for the given `audio_id`.

    Poll this endpoint until `status` is `completed` or `failed`.
    """
    _require_auth(x_api_key, authorization)
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
