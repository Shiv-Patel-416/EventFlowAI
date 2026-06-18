"""Diversions Router"""
from fastapi import APIRouter
from app.schemas.schemas import DiversionRequest, DiversionResponse, DiversionRoute
from app.graph.diversion_engine import diversion_engine

router = APIRouter()

@router.post("/plan", response_model=DiversionResponse)
async def plan_diversion(data: DiversionRequest):
    result = diversion_engine.recommend_diversions(
        event_lat=data.latitude,
        event_lon=data.longitude,
        event_cause=data.event_cause,
        requires_road_closure=data.requires_road_closure,
        severity_score=data.severity_score,
        radius_km=data.radius_km,
    )
    
    return DiversionResponse(
        routes=[DiversionRoute(**r) for r in result['routes']],
        affected_area_radius_km=result['affected_area_radius_km'],
        total_alternatives=result['total_alternatives']
    )
