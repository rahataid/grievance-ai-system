from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class AudioStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class PipelineStage(str, Enum):
    audio_service = "audio_service"
    asr_service = "asr_service"
    language_service = "language_service"
    translation_service = "translation_service"
    nlp_service = "nlp_service"
    urgency_service = "urgency_service"
    persistence_service = "persistence_service"
    completed = "completed"


# ── Auth schemas ───────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    status: str
    app: str


class CreateApiKeyResponse(BaseModel):
    api_key: str


class RevokeApiKeyResponse(BaseModel):
    message: str

# ── Audio schemas ──────────────────────────────────────────────────────────────

class UploadAudioResponse(BaseModel):
    audio_id: str
    status: AudioStatus


class GrievanceData(BaseModel):
    transcript: Optional[str] = None
    language: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    severity_score: Optional[float] = None


class AudioStatusResponse(BaseModel):
    audio_id: str
    status: AudioStatus
    current_stage: Optional[PipelineStage] = None
    url: Optional[str] = None
    grievance: Optional[GrievanceData] = None


# ── Error schemas ──────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    detail: str
