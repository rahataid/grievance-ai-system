import hashlib
import logging
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Session
from shared.database.base import Base
from shared.database.session import get_db

logger = logging.getLogger(__name__)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    expires_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)
    scopes = Column(String, nullable=True)  # Store as comma-separated or JSON string
    rate_limit = Column(Integer, nullable=True)


# AuthContext for propagation
from typing import List, Optional
import json

class AuthContext:
    def __init__(self, user_id: Optional[str], tenant_id: Optional[str], scopes: Optional[List[str]], api_key_id: int, identifier: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.scopes = scopes or []
        self.api_key_id = api_key_id
        self.identifier = identifier

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "scopes": self.scopes,
            "api_key_id": self.api_key_id,
            "identifier": self.identifier,
        }

def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()

def verify_api_key(
    api_key: str = Security(API_KEY_HEADER),
    db: Session = Depends(get_db),
) -> AuthContext:
    """FastAPI dependency that validates the X-API-Key header."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    key_hash = hash_api_key(api_key)
    record = (
        db.query(ApiKey)
        .filter(ApiKey.api_key_hash == key_hash, ApiKey.is_active.is_(True))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )
    if record.expires_on and record.expires_on < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )
    record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Authenticated: {record.identifier}")
    # Parse scopes (assume comma-separated or JSON string)
    scopes = []
    if record.scopes:
        try:
            scopes = json.loads(record.scopes)
            if not isinstance(scopes, list):
                scopes = []
        except Exception:
            scopes = [s.strip() for s in record.scopes.split(",") if s.strip()]
    return AuthContext(
        user_id=record.user_id,
        tenant_id=record.tenant_id,
        scopes=scopes,
        api_key_id=record.id,
        identifier=record.identifier,
    )
