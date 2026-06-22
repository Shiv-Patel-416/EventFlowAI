"""Analytics Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter, defaultdict
from app.database import get_db
from app.models.event import Event

router = APIRouter()

@router.get("/overview")
async def analytics_overview(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    
    causes = Counter(e.event_cause for e in events if e.event_cause)
    corridors = Counter(e.corridor for e in events if e.corridor)
    zones = Counter(e.zone for e in events if e.zone)
    priorities = Counter(e.priority for e in events if e.priority)
    
    closures_by_cause = defaultdict(lambda: {"total": 0, "closures": 0})
    for e in events:
        cause = e.event_cause
        if not cause:
            continue
        closures_by_cause[cause]["total"] += 1
        if e.requires_road_closure:
            closures_by_cause[cause]["closures"] += 1
    
    closure_rates = {
        cause: round(data["closures"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        for cause, data in closures_by_cause.items()
    }
    
    hourly = Counter()
    for e in events:
        if e.start_datetime:
            try:
                hour = e.start_datetime.hour
                hourly[hour] += 1
            except:
                pass
    
    hourly_data = [{"hour": h, "count": hourly.get(h, 0)} for h in range(24)]
    
    return {
        "total_events": len(events),
        "cause_distribution": [{"cause": k, "count": v} for k, v in causes.most_common()],
        "corridor_distribution": [{"corridor": k, "count": v} for k, v in corridors.most_common(15)],
        "zone_distribution": [{"zone": k, "count": v} for k, v in zones.most_common()],
        "priority_distribution": dict(priorities),
        "closure_rates": closure_rates,
        "hourly_distribution": hourly_data,
    }

@router.get("/zone/{zone_name}")
async def zone_analytics(zone_name: str, db: Session = Depends(get_db)):
    zone_events = db.query(Event).filter(Event.zone == zone_name).all()
    causes = Counter(e.event_cause for e in zone_events if e.event_cause)
    corridors = Counter(e.corridor for e in zone_events if e.corridor)
    
    return {
        "zone": zone_name,
        "total_events": len(zone_events),
        "cause_distribution": dict(causes.most_common()),
        "corridor_distribution": dict(corridors.most_common(10)),
        "closure_rate": sum(1 for e in zone_events if e.requires_road_closure) / max(len(zone_events), 1) * 100,
    }

@router.get("/corridor/{corridor_name}")
async def corridor_analytics(corridor_name: str, db: Session = Depends(get_db)):
    corr_events = db.query(Event).filter(Event.corridor == corridor_name).all()
    causes = Counter(e.event_cause for e in corr_events if e.event_cause)
    
    return {
        "corridor": corridor_name,
        "total_events": len(corr_events),
        "cause_distribution": dict(causes.most_common()),
        "closure_rate": sum(1 for e in corr_events if e.requires_road_closure) / max(len(corr_events), 1) * 100,
    }

@router.get("/heatmap")
async def heatmap(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    points = []
    intensity_map = {
        "vehicle_breakdown": 0.3, "accident": 0.8, "public_event": 0.9,
        "procession": 0.85, "vip_movement": 0.95, "protest": 0.9,
        "construction": 0.5, "tree_fall": 0.6, "water_logging": 0.5,
        "congestion": 0.7, "pot_holes": 0.3, "others": 0.3
    }
    for e in events:
        points.append({
            "lat": e.latitude,
            "lng": e.longitude,
            "intensity": intensity_map.get(e.event_cause, 0.3) if e.event_cause else 0.3,
            "cause": e.event_cause
        })
    return {"points": points}

@router.get("/model-performance")
async def model_performance():
    """Return model performance metrics from training."""
    import json, os
    meta_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml', 'models', 'model_metadata.json')
    try:
        with open(meta_path) as f:
            return json.load(f)
    except:
        return {"error": "Model metadata not found"}
