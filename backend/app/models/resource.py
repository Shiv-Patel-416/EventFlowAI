"""SQLAlchemy Resource model"""
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"))
    traffic_police = Column(Integer, default=0)
    barricades = Column(Integer, default=0)
    checkpoints = Column(Integer, default=0)
    emergency_units = Column(Integer, default=0)
    total_cost_estimate = Column(Float)
    optimization_status = Column(String(20), default="pending")
    deployment_plan = Column(JSONB)
    planned_at = Column(DateTime(timezone=True), server_default=func.now())
    deployed_at = Column(DateTime(timezone=True))


class Diversion(Base):
    __tablename__ = "diversions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"))
    primary_route = Column(JSONB)
    alt_route_1 = Column(JSONB)
    alt_route_2 = Column(JSONB)
    primary_distance_km = Column(Float)
    primary_duration_min = Column(Float)
    status = Column(String(20), default="proposed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    actual_severity = Column(Float)
    actual_duration_hours = Column(Float)
    actual_road_closure = Column(String(5))
    actual_police_used = Column(Integer)
    actual_barricades_used = Column(Integer)
    officer_notes = Column(String(1000))
    prediction_accuracy = Column(Float)
    resource_efficiency = Column(Float)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
