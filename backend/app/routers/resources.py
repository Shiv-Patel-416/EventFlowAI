"""Resources Router"""
from fastapi import APIRouter
from app.schemas.schemas import ResourceOptimizeRequest, ResourceResponse
from app.optimization.resource_optimizer import optimize_resources
import uuid

router = APIRouter()

@router.post("/optimize", response_model=ResourceResponse)
async def optimize(data: ResourceOptimizeRequest):
    result = optimize_resources(
        severity_score=data.severity_score,
        event_cause=data.event_cause,
        requires_road_closure=data.requires_road_closure,
        latitude=data.latitude,
        longitude=data.longitude,
        max_police=data.max_police,
        max_barricades=data.max_barricades,
        max_checkpoints=data.max_checkpoints,
        max_emergency=data.max_emergency,
    )
    
    return ResourceResponse(
        id=str(uuid.uuid4()),
        event_id=data.event_id,
        traffic_police=result['traffic_police'],
        barricades=result['barricades'],
        checkpoints=result['checkpoints'],
        emergency_units=result['emergency_units'],
        total_cost_estimate=result['total_cost_estimate'],
        optimization_status=result['optimization_status'],
        deployment_plan=result['deployment_plan']
    )
