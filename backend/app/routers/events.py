"""Events Router — CRUD operations for traffic events (Supabase Integrated)"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas.schemas import EventCreate, EventResponse, EventListResponse
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from typing import Optional
import uuid
import csv
import os
from datetime import datetime

router = APIRouter()

# Restored for compatibility with other mocked routers (dashboard, analytics)
EVENTS_STORE = []

def _load_events():
    """Load events from raw CSV on startup for mock routers."""
    global EVENTS_STORE
    if EVENTS_STORE:
        return
    
    raw_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml', 'data', 'raw', 'events_raw.csv')
    if not os.path.exists(raw_path):
        return
    
    with open(raw_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get('latitude', 0))
                lon = float(row.get('longitude', 0))
                if lat == 0 or lon == 0:
                    continue
                
                EVENTS_STORE.append({
                    "id": row.get('id', str(uuid.uuid4())),
                    "external_id": row.get('id'),
                    "event_type": row.get('event_type', 'unplanned'),
                    "latitude": lat,
                    "longitude": lon,
                    "address": row.get('address', ''),
                    "event_cause": row.get('event_cause', 'others').lower(),
                    "requires_road_closure": row.get('requires_road_closure', 'FALSE').upper() == 'TRUE',
                    "start_datetime": row.get('start_datetime', ''),
                    "end_datetime": row.get('end_datetime') if row.get('end_datetime', 'NULL') != 'NULL' else None,
                    "status": row.get('status', 'active'),
                    "priority": row.get('priority', 'Low'),
                    "corridor": row.get('corridor', 'Non-corridor'),
                    "zone": row.get('zone', '') if row.get('zone', 'NULL') != 'NULL' else None,
                    "junction": row.get('junction', '') if row.get('junction', 'NULL') != 'NULL' else None,
                    "police_station": row.get('police_station', '') if row.get('police_station', 'NULL') != 'NULL' else None,
                    "description": row.get('description', '') if row.get('description', 'NULL') != 'NULL' else None,
                    "veh_type": row.get('veh_type', '') if row.get('veh_type', 'NULL') != 'NULL' else None,
                    "created_at": row.get('created_date', ''),
                })
            except Exception:
                continue

@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    event_cause: Optional[str] = None,
    event_type: Optional[str] = None,
    corridor: Optional[str] = None,
    priority: Optional[str] = None,
    zone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    
    if status:
        query = query.filter(Event.status == status)
    if event_cause:
        query = query.filter(Event.event_cause == event_cause.lower())
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if corridor:
        query = query.filter(Event.corridor == corridor)
    if priority:
        query = query.filter(Event.priority == priority)
    if zone:
        query = query.filter(Event.zone == zone)
    
    total = query.count()
    start = (page - 1) * page_size
    page_events = query.offset(start).limit(page_size).all()
    
    return EventListResponse(
        events=[EventResponse(
            id=str(e.id),
            external_id=e.external_id,
            event_type=e.event_type,
            latitude=e.latitude,
            longitude=e.longitude,
            address=e.address,
            event_cause=e.event_cause,
            requires_road_closure=e.requires_road_closure,
            start_datetime=e.start_datetime.isoformat() if e.start_datetime else "",
            end_datetime=e.end_datetime.isoformat() if e.end_datetime else None,
            status=e.status,
            priority=e.priority,
            corridor=e.corridor,
            zone=e.zone,
            junction=e.junction,
            police_station=e.police_station,
            description=e.description,
            veh_type=e.veh_type,
            created_at=e.created_at.isoformat() if e.created_at else None
        ) for e in page_events],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/stats")
async def event_stats(db: Session = Depends(get_db)):
    total_events = db.query(Event).count()
    
    causes_raw = db.query(Event.event_cause, func.count(Event.id)).group_by(Event.event_cause).all()
    corridors_raw = db.query(Event.corridor, func.count(Event.id)).filter(Event.corridor.isnot(None)).group_by(Event.corridor).all()
    statuses_raw = db.query(Event.status, func.count(Event.id)).group_by(Event.status).all()
    types_raw = db.query(Event.event_type, func.count(Event.id)).group_by(Event.event_type).all()
    
    # Sort and slice like the mock
    causes_sorted = sorted(causes_raw, key=lambda x: x[1], reverse=True)[:17]
    corridors_sorted = sorted(corridors_raw, key=lambda x: x[1], reverse=True)[:20]
    
    return {
        "total_events": total_events,
        "by_cause": {k: v for k, v in causes_sorted},
        "by_corridor": {k: v for k, v in corridors_sorted},
        "by_status": {k: v for k, v in statuses_raw},
        "by_type": {k: v for k, v in types_raw},
    }

@router.get("/heatmap/data")
async def heatmap_data(db: Session = Depends(get_db)):
    events = db.query(Event.latitude, Event.longitude, Event.event_cause).all()
    
    points = []
    severity = {"vehicle_breakdown": 0.3, "accident": 0.8, "public_event": 0.9,
                "procession": 0.85, "vip_movement": 0.95, "protest": 0.9,
                "construction": 0.5, "tree_fall": 0.6, "water_logging": 0.5,
                "congestion": 0.7, "pot_holes": 0.3, "road_conditions": 0.4,
                "others": 0.3}
    
    for lat, lon, cause in events:
        points.append({
            "latitude": lat,
            "longitude": lon,
            "intensity": severity.get(cause, 0.3),
            "event_cause": cause
        })
    
    return {"points": points, "total": len(points)}

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, db: Session = Depends(get_db)):
    try:
        uuid_obj = uuid.UUID(event_id)
        e = db.query(Event).filter(Event.id == uuid_obj).first()
    except ValueError:
        e = db.query(Event).filter(Event.external_id == event_id).first()
        
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return EventResponse(
        id=str(e.id),
        external_id=e.external_id,
        event_type=e.event_type,
        latitude=e.latitude,
        longitude=e.longitude,
        address=e.address,
        event_cause=e.event_cause,
        requires_road_closure=e.requires_road_closure,
        start_datetime=e.start_datetime.isoformat() if e.start_datetime else "",
        end_datetime=e.end_datetime.isoformat() if e.end_datetime else None,
        status=e.status,
        priority=e.priority,
        corridor=e.corridor,
        zone=e.zone,
        junction=e.junction,
        police_station=e.police_station,
        description=e.description,
        veh_type=e.veh_type,
        created_at=e.created_at.isoformat() if e.created_at else None
    )

@router.post("", response_model=EventResponse)
async def create_event(data: EventCreate, db: Session = Depends(get_db)):
    new_event = Event(
        event_type=data.event_type,
        latitude=data.latitude,
        longitude=data.longitude,
        address=data.address,
        event_cause=data.event_cause.lower(),
        requires_road_closure=data.requires_road_closure,
        start_datetime=data.start_datetime, # Could parse to datetime object if needed, but string might work if SQLAlchemy handles it
        end_datetime=data.end_datetime,
        status="active",
        priority=data.priority,
        corridor=data.corridor,
        zone=data.zone,
        junction=data.junction,
        police_station=data.police_station,
        description=data.description,
        veh_type=data.veh_type
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return EventResponse(
        id=str(new_event.id),
        external_id=new_event.external_id,
        event_type=new_event.event_type,
        latitude=new_event.latitude,
        longitude=new_event.longitude,
        address=new_event.address,
        event_cause=new_event.event_cause,
        requires_road_closure=new_event.requires_road_closure,
        start_datetime=new_event.start_datetime.isoformat() if new_event.start_datetime else "",
        end_datetime=new_event.end_datetime.isoformat() if new_event.end_datetime else None,
        status=new_event.status,
        priority=new_event.priority,
        corridor=new_event.corridor,
        zone=new_event.zone,
        junction=new_event.junction,
        police_station=new_event.police_station,
        description=new_event.description,
        veh_type=new_event.veh_type,
        created_at=new_event.created_at.isoformat() if new_event.created_at else None
    )
