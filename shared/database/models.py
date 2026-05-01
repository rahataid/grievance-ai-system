from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from shared.database.base import Base

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_on = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    user_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)
    scopes = Column(String, nullable=True)
    rate_limit = Column(Integer, nullable=True)
    grievances = relationship("Grievance", back_populates="api_key")

class Grievance(Base):
    __tablename__ = "grievances"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beneficiary_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    transcript = Column(String, nullable=False)
    language = Column(String, nullable=False)
    grievance_detected = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    severity_score = Column(Float, nullable=True)
    recommended_action = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    api_key = relationship("APIKey", back_populates="grievances")
