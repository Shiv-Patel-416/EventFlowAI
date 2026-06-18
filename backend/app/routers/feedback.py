"""Feedback Router"""
from fastapi import APIRouter
from app.schemas.schemas import FeedbackCreate, FeedbackResponse
from datetime import datetime
import uuid

router = APIRouter()

FEEDBACK_STORE = []

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackCreate):
    feedback = {
        "id": str(uuid.uuid4()),
        "event_id": data.event_id,
        "prediction_id": data.prediction_id,
        "actual_severity": data.actual_severity,
        "actual_duration_hours": data.actual_duration_hours,
        "actual_road_closure": data.actual_road_closure,
        "actual_police_used": data.actual_police_used,
        "actual_barricades_used": data.actual_barricades_used,
        "officer_notes": data.officer_notes,
        "prediction_accuracy": None,
        "resource_efficiency": None,
        "submitted_at": datetime.now().isoformat()
    }
    
    FEEDBACK_STORE.append(feedback)
    
    return FeedbackResponse(
        id=feedback["id"],
        event_id=feedback["event_id"],
        actual_severity=feedback["actual_severity"],
        prediction_accuracy=feedback.get("prediction_accuracy"),
        resource_efficiency=feedback.get("resource_efficiency"),
        submitted_at=feedback["submitted_at"]
    )

@router.get("")
async def list_feedback():
    return {"feedback": FEEDBACK_STORE, "total": len(FEEDBACK_STORE)}
