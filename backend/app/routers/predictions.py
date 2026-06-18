"""Predictions Router — ML prediction endpoints"""
from fastapi import APIRouter
from app.schemas.schemas import (
    PredictionRequest, PredictionResponse,
    ResourceRecommendation, DiversionRoute, CascadeInfo,
)
from app.ml.predictor import predictor
from app.optimization.resource_optimizer import optimize_resources
from app.graph.diversion_engine import diversion_engine
from datetime import datetime
import uuid

router = APIRouter()

# Load models on import
try:
    predictor.load_models()
except Exception as e:
    print(f"Warning: Could not load ML models: {e}")


@router.post("/predict", response_model=PredictionResponse)
async def predict_impact(data: PredictionRequest):
    """Predict traffic impact for an event, including cascade risk (Step 3C)."""

    # ── Run ML prediction (includes cascade scoring internally) ──
    event_data = data.model_dump()
    prediction = predictor.predict(event_data)

    # ── Run resource optimization ─────────────────────────────────
    resources = optimize_resources(
        severity_score=prediction['severity_score'],
        event_cause=data.event_cause,
        requires_road_closure=data.requires_road_closure,
        latitude=data.latitude,
        longitude=data.longitude,
        duration_hours=prediction['estimated_duration_hours']
    )

    # ── Run diversion planning ────────────────────────────────────
    diversions = diversion_engine.recommend_diversions(
        event_lat=data.latitude,
        event_lon=data.longitude,
        event_cause=data.event_cause,
        requires_road_closure=data.requires_road_closure,
        severity_score=prediction['severity_score']
    )

    # ── Assemble cascade_info block ───────────────────────────────
    cascade_info = CascadeInfo(
        cascade_probability=prediction.get('cascade_probability', 0.05),
        risk_level=prediction.get('cascade_risk_level', 'Unknown'),
        likely_affected_junctions=prediction.get('cascade_affected_junctions', []),
        duration_multiplier=prediction.get('cascade_duration_multiplier', 1.0),
        explanation=prediction.get('cascade_explanation', ''),
    )

    # ── Build full response ───────────────────────────────────────
    return PredictionResponse(
        prediction_id=str(uuid.uuid4()),
        severity_score=prediction['severity_score'],
        severity_label=prediction['severity_label'],
        closure_probability=prediction['closure_probability'],
        estimated_duration_hours=prediction['estimated_duration_hours'],
        confidence=prediction['confidence'],
        resource_recommendation=ResourceRecommendation(
            traffic_police=resources['traffic_police'],
            barricades=resources['barricades'],
            checkpoints=resources['checkpoints'],
            emergency_units=resources['emergency_units'],
            total_estimated_cost=resources['total_cost_estimate']
        ),
        diversion_routes=[
            DiversionRoute(**route)
            for route in diversions['routes'][:3]
        ],
        model_version=prediction['model_version'],
        predicted_at=datetime.now().isoformat(),
        cascade_info=cascade_info,
    )


@router.get("/model-info")
async def model_info():
    """Get information about loaded ML models."""
    return {
        "loaded": predictor._loaded,
        "metadata": predictor.metadata,
        "model_version": (
            predictor.metadata.get('model_version', 'unknown')
            if predictor.metadata else 'not loaded'
        ),
        # Step 3C: Cascade matrix status
        "cascade_matrix_loaded": predictor._cascade_ready,
    }
