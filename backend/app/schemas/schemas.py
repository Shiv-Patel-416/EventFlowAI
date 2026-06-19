"""Pydantic schemas for API request/response"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============ Auth Schemas ============
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "officer"
    police_station: Optional[str] = None
    zone: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    police_station: Optional[str]
    zone: Optional[str]
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ Event Schemas ============
class EventCreate(BaseModel):
    event_type: str = Field(..., description="planned or unplanned")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    address: Optional[str] = None
    end_address: Optional[str] = None
    event_cause: str
    requires_road_closure: bool = False
    start_datetime: str
    end_datetime: Optional[str] = None
    priority: str = "Low"
    corridor: Optional[str] = None
    zone: Optional[str] = None
    junction: Optional[str] = None
    police_station: Optional[str] = None
    description: Optional[str] = None
    veh_type: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    external_id: Optional[str]
    event_type: str
    latitude: float
    longitude: float
    address: Optional[str]
    event_cause: str
    requires_road_closure: bool
    start_datetime: str
    end_datetime: Optional[str]
    status: str
    priority: str
    corridor: Optional[str]
    zone: Optional[str]
    junction: Optional[str]
    police_station: Optional[str]
    description: Optional[str]
    veh_type: Optional[str]
    created_at: Optional[str]

class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


# ============ Prediction Schemas ============
class PredictionRequest(BaseModel):
    event_type: str = "planned"
    event_cause: str
    latitude: float
    longitude: float
    corridor: Optional[str] = "Non-corridor"
    zone: Optional[str] = "Unknown"
    junction: Optional[str] = "Unknown"
    police_station: Optional[str] = "Unknown"
    priority: str = "High"
    start_datetime: str
    end_datetime: Optional[str] = None
    description: Optional[str] = None
    requires_road_closure: bool = False

class ConditionalForecastEntry(BaseModel):
    """Step 4B: police_count → predicted duration → cost."""
    police_deployed: int
    estimated_duration_hours: float
    estimated_cost_inr: float
    efficiency_ratio: float

class ResourceRecommendation(BaseModel):
    traffic_police: int
    barricades: int
    checkpoints: int
    emergency_units: int
    total_estimated_cost: float
    # Step 4B ML fields
    resource_efficiency_score: Optional[float] = None
    optimization_method: Optional[str] = None
    confidence: Optional[float] = None
    conditional_forecast: Optional[List[ConditionalForecastEntry]] = None
    explanation: Optional[str] = None

class DiversionRoute(BaseModel):
    route_name: str
    distance_km: float
    estimated_time_min: float
    congestion_level: str
    coordinates: List[List[float]]


class CascadeInfo(BaseModel):
    """Congestion Cascade Prediction result (Step 3C)."""
    cascade_probability: float = Field(
        description="Probability [0–1] that this event triggers secondary incidents"
    )
    risk_level: str = Field(
        description="Low | Medium | High | Critical"
    )
    likely_affected_junctions: List[str] = Field(
        default_factory=list,
        description="Junctions historically correlated with this origin"
    )
    duration_multiplier: float = Field(
        description="Estimated stretch factor on resolution time due to cascades"
    )
    explanation: str = Field(
        description="Human-readable cascade risk summary"
    )

class PredictionResponse(BaseModel):
    prediction_id: str
    severity_score: float
    severity_label: str
    closure_probability: float
    estimated_duration_hours: float
    confidence: float
    resource_recommendation: ResourceRecommendation
    diversion_routes: List[DiversionRoute]
    model_version: str
    predicted_at: str
    # Step 3C: Cascade prediction field
    cascade_info: Optional[CascadeInfo] = None
    # Real-Time Weather Integration
    rainfall_mm: Optional[float] = None


# ============ Resource Schemas ============
class ResourceOptimizeRequest(BaseModel):
    event_id: Optional[str] = None
    severity_score: float
    event_cause: str
    requires_road_closure: bool = False
    latitude: float
    longitude: float
    max_police: int = 50
    max_barricades: int = 100
    max_checkpoints: int = 20
    max_emergency: int = 10

class ResourceResponse(BaseModel):
    id: str
    event_id: Optional[str]
    traffic_police: int
    barricades: int
    checkpoints: int
    emergency_units: int
    total_cost_estimate: float
    optimization_status: str
    deployment_plan: Optional[Dict[str, Any]]


# ============ Diversion Schemas ============
class DiversionRequest(BaseModel):
    latitude: float
    longitude: float
    event_cause: str
    requires_road_closure: bool = False
    severity_score: float = 5.0
    radius_km: float = 2.0

class DiversionResponse(BaseModel):
    routes: List[DiversionRoute]
    affected_area_radius_km: float
    total_alternatives: int


# ============ Feedback Schemas ============
class FeedbackCreate(BaseModel):
    event_id: str
    prediction_id: Optional[str] = None
    actual_severity: float
    actual_duration_hours: Optional[float] = None
    actual_road_closure: Optional[bool] = None
    actual_police_used: Optional[int] = None
    actual_barricades_used: Optional[int] = None
    officer_notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str
    event_id: str
    actual_severity: float
    prediction_accuracy: Optional[float]
    resource_efficiency: Optional[float]
    submitted_at: str


# ============ Dashboard Schemas ============
class DashboardStats(BaseModel):
    total_events: int
    active_events: int
    events_today: int
    avg_severity: float
    prediction_accuracy: float
    total_predictions: int
    road_closures_today: int
    top_corridors: List[Dict[str, Any]]
    event_cause_distribution: List[Dict[str, Any]]
    hourly_distribution: List[Dict[str, Any]]
    recent_events: List[EventResponse]
    zone_stats: List[Dict[str, Any]]
    severity_distribution: Dict[str, int]

class AnalyticsResponse(BaseModel):
    zone_comparison: List[Dict[str, Any]]
    trend_data: List[Dict[str, Any]]
    cause_analysis: List[Dict[str, Any]]
    resolution_times: Dict[str, float]
    prediction_performance: Dict[str, float]

class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    intensity: float
    event_cause: str
