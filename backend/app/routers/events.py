"""Events Router — CRUD operations for traffic events"""
from fastapi import APIRouter, Query
from app.schemas.schemas import EventCreate, EventResponse, EventListResponse
from typing import Optional
import csv
import os
import uuid
from datetime import datetime

router = APIRouter()

# Load events from processed data
EVENTS_STORE = []

def _load_events():
    """Load events from raw CSV on startup."""
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
):
    _load_events()
    
    filtered = EVENTS_STORE
    
    if status:
        filtered = [e for e in filtered if e["status"] == status]
    if event_cause:
        filtered = [e for e in filtered if e["event_cause"] == event_cause.lower()]
    if event_type:
        filtered = [e for e in filtered if e["event_type"] == event_type]
    if corridor:
        filtered = [e for e in filtered if e["corridor"] == corridor]
    if priority:
        filtered = [e for e in filtered if e["priority"] == priority]
    if zone:
        filtered = [e for e in filtered if e.get("zone") == zone]
    
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_events = filtered[start:end]
    
    return EventListResponse(
        events=[EventResponse(**e) for e in page_events],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/stats")
async def event_stats():
    _load_events()
    
    from collections import Counter
    causes = Counter(e["event_cause"] for e in EVENTS_STORE)
    corridors = Counter(e["corridor"] for e in EVENTS_STORE)
    statuses = Counter(e["status"] for e in EVENTS_STORE)
    types = Counter(e["event_type"] for e in EVENTS_STORE)
    
    return {
        "total_events": len(EVENTS_STORE),
        "by_cause": dict(causes.most_common(17)),
        "by_corridor": dict(corridors.most_common(20)),
        "by_status": dict(statuses),
        "by_type": dict(types),
    }

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    _load_events()
    
    for e in EVENTS_STORE:
        if e["id"] == event_id or e.get("external_id") == event_id:
            return EventResponse(**e)
    
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Event not found")

@router.post("", response_model=EventResponse)
async def create_event(data: EventCreate):
    _load_events()
    
    event = {
        "id": str(uuid.uuid4()),
        "external_id": None,
        "event_type": data.event_type,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "address": data.address,
        "event_cause": data.event_cause.lower(),
        "requires_road_closure": data.requires_road_closure,
        "start_datetime": data.start_datetime,
        "end_datetime": data.end_datetime,
        "status": "active",
        "priority": data.priority,
        "corridor": data.corridor,
        "zone": data.zone,
        "junction": data.junction,
        "police_station": data.police_station,
        "description": data.description,
        "veh_type": data.veh_type,
        "created_at": datetime.now().isoformat(),
    }
    
    EVENTS_STORE.insert(0, event)
    return EventResponse(**event)

@router.get("/heatmap/data")
async def heatmap_data():
    _load_events()
    
    points = []
    for e in EVENTS_STORE:
        severity = {"vehicle_breakdown": 0.3, "accident": 0.8, "public_event": 0.9,
                    "procession": 0.85, "vip_movement": 0.95, "protest": 0.9,
                    "construction": 0.5, "tree_fall": 0.6, "water_logging": 0.5,
                    "congestion": 0.7, "pot_holes": 0.3, "road_conditions": 0.4,
                    "others": 0.3}
        
        points.append({
            "latitude": e["latitude"],
            "longitude": e["longitude"],
            "intensity": severity.get(e["event_cause"], 0.3),
            "event_cause": e["event_cause"]
        })
    
    return {"points": points, "total": len(points)}
