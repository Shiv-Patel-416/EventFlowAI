"""Predictions Router — ML prediction endpoints"""
from fastapi import APIRouter
from app.schemas.schemas import (
    PredictionRequest, PredictionResponse,
    ResourceRecommendation, DiversionRoute, CascadeInfo,
    ConditionalForecastEntry,
)
from app.ml.predictor import predictor
from app.ml.resource_ml_predictor import resource_ml_predictor
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

try:
    resource_ml_predictor.load_models()
except Exception as e:
    print(f"Warning: Could not load resource ML models: {e}")


@router.post("/predict", response_model=PredictionResponse)
async def predict_impact(data: PredictionRequest):
    """Predict traffic impact — severity, duration, cascade, ML resources (Steps 3C + 4B)."""

    event_data = data.model_dump()

    # ── Step 1: Core ML prediction (severity + duration + cascade) ──
    prediction = predictor.predict(event_data)
    cascade_prob   = prediction.get('cascade_probability', 0.05)
    severity_score = prediction['severity_score']
    duration_hours = prediction['estimated_duration_hours']

    # ── Step 2: ML-based resource recommendation (Step 4B) ─────────
    ml_resources = resource_ml_predictor.predict_resources(
        event_data=event_data,
        severity_score=severity_score,
        cascade_prob=cascade_prob,
        duration_hours=duration_hours,
        max_police=data.__dict__.get('max_police', 50),
        max_barricades=data.__dict__.get('max_barricades', 100),
        max_checkpoints=data.__dict__.get('max_checkpoints', 20),
        max_emergency=data.__dict__.get('max_emergency', 10),
    )

    # ── Step 3: Rule-based fallback (hybrid: use ML if loaded) ─────
    # If ML models not trained yet, fall back gracefully
    if resource_ml_predictor._loaded:
        police      = ml_resources.traffic_police
        barricades  = ml_resources.barricades
        checkpoints = ml_resources.checkpoints
        emergency   = ml_resources.emergency_units
        total_cost  = ml_resources.total_cost_estimate
        efficiency  = ml_resources.resource_efficiency_score
        method      = ml_resources.optimization_method
        conf        = ml_resources.confidence
        cond_table  = [ConditionalForecastEntry(**e) for e in ml_resources.conditional_forecast]
        explanation = ml_resources.explanation
    else:
        rule = optimize_resources(
            severity_score=severity_score,
            event_cause=data.event_cause,
            requires_road_closure=data.requires_road_closure,
            latitude=data.latitude,
            longitude=data.longitude,
            duration_hours=duration_hours,
        )
        police      = rule['traffic_police']
        barricades  = rule['barricades']
        checkpoints = rule['checkpoints']
        emergency   = rule['emergency_units']
        total_cost  = rule['total_cost_estimate']
        efficiency  = None
        method      = "constraint_based_ilp_fallback"
        conf        = 0.70
        cond_table  = []
        explanation = "Rule-based fallback (ML resource models not yet trained)."

    # ── Step 4: Diversion planning ──────────────────────────────────
    diversions = diversion_engine.recommend_diversions(
        event_lat=data.latitude,
        event_lon=data.longitude,
        event_cause=data.event_cause,
        requires_road_closure=data.requires_road_closure,
        severity_score=severity_score,
    )

    # ── Step 5: Cascade info block ──────────────────────────────────
    cascade_info = CascadeInfo(
        cascade_probability=cascade_prob,
        risk_level=prediction.get('cascade_risk_level', 'Unknown'),
        likely_affected_junctions=prediction.get('cascade_affected_junctions', []),
        duration_multiplier=prediction.get('cascade_duration_multiplier', 1.0),
        explanation=prediction.get('cascade_explanation', ''),
    )

    return PredictionResponse(
        prediction_id=str(uuid.uuid4()),
        severity_score=severity_score,
        severity_label=prediction['severity_label'],
        closure_probability=prediction['closure_probability'],
        estimated_duration_hours=duration_hours,
        confidence=prediction['confidence'],
        resource_recommendation=ResourceRecommendation(
            traffic_police=police,
            barricades=barricades,
            checkpoints=checkpoints,
            emergency_units=emergency,
            total_estimated_cost=total_cost,
            resource_efficiency_score=efficiency,
            optimization_method=method,
            confidence=conf,
            conditional_forecast=cond_table if cond_table else None,
            explanation=explanation,
        ),
        diversion_routes=[DiversionRoute(**r) for r in diversions['routes'][:3]],
        model_version=prediction['model_version'],
        predicted_at=datetime.now().isoformat(),
        cascade_info=cascade_info,
    )


@router.get("/model-info")
async def model_info():
    """Get information about all loaded ML models."""
    resource_meta = resource_ml_predictor.metadata or {}
    return {
        "core_models_loaded":     predictor._loaded,
        "resource_models_loaded": resource_ml_predictor._loaded,
        "cascade_matrix_loaded":  predictor._cascade_ready,
        "core_model_version":     (predictor.metadata.get('model_version','unknown')
                                   if predictor.metadata else 'not loaded'),
        "resource_model_version": resource_meta.get('model_version','not trained'),
        "resource_efficiency":    resource_meta.get('overall_resource_efficiency'),
        "algorithms_evaluated":   resource_meta.get('algorithms_evaluated',[]),
        "resource_metrics":       resource_meta.get('model_metrics',{}),
        "conditional_forecast_table": resource_meta.get('conditional_forecast_table',[]),
    }
