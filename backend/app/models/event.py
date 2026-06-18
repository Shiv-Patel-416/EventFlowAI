"""SQLAlchemy Event model"""
import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(50), unique=True)
    event_type = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    address = Column(Text)
    end_address = Column(Text)
    event_cause = Column(String(50), nullable=False)
    requires_road_closure = Column(Boolean, default=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True))
    status = Column(String(20), default="active")
    priority = Column(String(10), default="Low")
    corridor = Column(String(200))
    zone = Column(String(100))
    junction = Column(String(200))
    police_station = Column(String(200))
    description = Column(Text)
    veh_type = Column(String(50))
    veh_no = Column(String(50))
    gba_identifier = Column(String(200))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
