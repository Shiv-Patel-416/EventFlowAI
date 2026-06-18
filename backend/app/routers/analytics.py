"""Analytics Router"""
from fastapi import APIRouter
from collections import Counter, defaultdict
from app.routers.events import EVENTS_STORE, _load_events

router = APIRouter()

@router.get("/overview")
async def analytics_overview():
    _load_events()
    
    causes = Counter(e["event_cause"] for e in EVENTS_STORE)
    corridors = Counter(e["corridor"] for e in EVENTS_STORE)
    zones = Counter(e.get("zone", "Unknown") for e in EVENTS_STORE if e.get("zone"))
    priorities = Counter(e["priority"] for e in EVENTS_STORE)
    
    closures_by_cause = defaultdict(lambda: {"total": 0, "closures": 0})
    for e in EVENTS_STORE:
        cause = e["event_cause"]
        closures_by_cause[cause]["total"] += 1
        if e["requires_road_closure"]:
            closures_by_cause[cause]["closures"] += 1
    
    closure_rates = {
        cause: round(data["closures"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        for cause, data in closures_by_cause.items()
    }
    
    # Hourly distribution
    hourly = Counter()
    for e in EVENTS_STORE:
        dt = e.get("start_datetime", "")
        if dt and " " in dt:
            try:
                hour = int(dt.split(" ")[1].split(":")[0])
                hourly[hour] += 1
            except:
                pass
    
    hourly_data = [{"hour": h, "count": hourly.get(h, 0)} for h in range(24)]
    
    return {
        "total_events": len(EVENTS_STORE),
        "cause_distribution": [{"cause": k, "count": v} for k, v in causes.most_common()],
        "corridor_distribution": [{"corridor": k, "count": v} for k, v in corridors.most_common(15)],
        "zone_distribution": [{"zone": k, "count": v} for k, v in zones.most_common()],
        "priority_distribution": dict(priorities),
        "closure_rates": closure_rates,
        "hourly_distribution": hourly_data,
    }

@router.get("/zone/{zone_name}")
async def zone_analytics(zone_name: str):
    _load_events()
    
    zone_events = [e for e in EVENTS_STORE if e.get("zone") == zone_name]
    causes = Counter(e["event_cause"] for e in zone_events)
    corridors = Counter(e["corridor"] for e in zone_events)
    
    return {
        "zone": zone_name,
        "total_events": len(zone_events),
        "cause_distribution": dict(causes.most_common()),
        "corridor_distribution": dict(corridors.most_common(10)),
        "closure_rate": sum(1 for e in zone_events if e["requires_road_closure"]) / max(len(zone_events), 1) * 100,
    }

@router.get("/corridor/{corridor_name}")
async def corridor_analytics(corridor_name: str):
    _load_events()
    
    corr_events = [e for e in EVENTS_STORE if e.get("corridor") == corridor_name]
    causes = Counter(e["event_cause"] for e in corr_events)
    
    return {
        "corridor": corridor_name,
        "total_events": len(corr_events),
        "cause_distribution": dict(causes.most_common()),
        "closure_rate": sum(1 for e in corr_events if e["requires_road_closure"]) / max(len(corr_events), 1) * 100,
    }

@router.get("/heatmap")
async def heatmap():
    _load_events()
    
    from app.routers.events import EVENTS_STORE
    points = []
    for e in EVENTS_STORE:
        intensity_map = {
            "vehicle_breakdown": 0.3, "accident": 0.8, "public_event": 0.9,
            "procession": 0.85, "vip_movement": 0.95, "protest": 0.9,
            "construction": 0.5, "tree_fall": 0.6, "water_logging": 0.5,
            "congestion": 0.7, "pot_holes": 0.3, "others": 0.3
        }
        points.append({
            "lat": e["latitude"],
            "lng": e["longitude"],
            "intensity": intensity_map.get(e["event_cause"], 0.3),
            "cause": e["event_cause"]
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
