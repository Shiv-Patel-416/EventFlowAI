"""SQLAlchemy Prediction model"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    severity_score = Column(Float, nullable=False)
    severity_label = Column(String(20))
    closure_probability = Column(Float, nullable=False)
    estimated_duration_hours = Column(Float)
    confidence = Column(Float)
    feature_vector = Column(JSONB)
    model_version = Column(String(20), default="v1.0.0")
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())
