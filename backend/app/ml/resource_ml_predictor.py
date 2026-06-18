"""
EventFlow AI — Runtime ML Resource Predictor (Step 4B)

Loads the 4 trained ML resource models (police, barricades, checkpoints,
emergency) and provides:
  1. predict_resources()  — single-event ML recommendation
  2. conditional_forecast() — "if you send K police, duration = X" table
  3. resource_efficiency_score() — gap metric vs rule-based baseline
"""
import json, math, os, pickle
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.config import settings
from app.ml.model_classes import GradientBoostingModel, SimpleDecisionStump

CITY_CENTER = (12.9871, 77.5960)
CAUSE_SEVERITY = {
    "vehicle_breakdown": 2.0, "pot_holes": 2.5, "road_conditions": 3.0,
    "water_logging": 4.0, "others": 2.5, "tree_fall": 5.0, "congestion": 4.5,
    "accident": 6.0, "construction": 5.5, "debris": 3.0,
    "fog_low_visibility": 3.5, "public_event": 7.5, "procession": 7.0,
    "vip_movement": 8.5, "protest": 8.0,
}
CAUSE_LABELS = sorted(CAUSE_SEVERITY.keys())
COST = {"police": 500, "barricades": 200, "checkpoints": 1500, "emergency": 3000}

RESOURCE_FEATURE_COLS = [
    'hour_ist','hour_sin','hour_cos','day_of_week','dow_sin','dow_cos',
    'month','time_slot','is_peak_hour','is_weekend','is_holiday',
    'latitude','longitude','distance_to_center_km',
    'is_main_corridor','corridor_event_freq','zone_event_freq','junction_event_freq',
    'event_cause_encoded','cause_base_severity','priority_encoded','is_planned',
    'has_description','description_length',
    'hist_closure_rate_cause','hist_closure_rate_corridor','avg_resolution_time_cause',
    'cascade_probability', 'severity_score', 'requires_road_closure',
]

HIST_CLOSURE_RATE = {
    "vehicle_breakdown":0.043,"others":0.086,"pot_holes":0.024,
    "construction":0.265,"water_logging":0.085,"accident":0.030,
    "tree_fall":0.394,"road_conditions":0.124,"congestion":0.044,
    "public_event":0.464,"procession":0.264,"vip_movement":0.800,
    "protest":0.400,"debris":0.083,"fog_low_visibility":0.0,
}
AVG_RESOLUTION = {
    "vehicle_breakdown":0.97,"others":93.57,"pot_holes":173.25,
    "construction":118.02,"water_logging":117.20,"accident":0.80,
    "tree_fall":79.41,"road_conditions":172.08,"congestion":1.24,
    "public_event":4.0,"procession":0.91,"vip_movement":3.0,
    "protest":0.41,"debris":382.97,"fog_low_visibility":2.0,
}
CORRIDOR_FREQ = {
    "Non-corridor":0.382,"Mysore Road":0.091,"Bellary Road 1":0.075,
    "Tumkur Road":0.056,"Bellary Road 2":0.046,"Hosur Road":0.036,
}


@dataclass
class ResourceMLResult:
    traffic_police: int
    barricades: int
    checkpoints: int
    emergency_units: int
    total_cost_estimate: float
    resource_efficiency_score: float
    optimization_method: str
    confidence: float
    conditional_forecast: List[Dict] = field(default_factory=list)
    model_versions: Dict[str, str] = field(default_factory=dict)
    explanation: str = ""


class ResourceMLPredictor:
    def __init__(self):
        self.models: Dict[str, object] = {}
        self.duration_model = None
        self.metadata = None
        self._loaded = False

    def load_models(self, models_dir: Optional[str] = None) -> bool:
        if models_dir is None:
            models_dir = settings.MODELS_DIR
        targets = ['police','barricades','checkpoints','emergency']
        loaded = 0
        for t in targets:
            path = os.path.join(models_dir, f'resource_{t}_model.pkl')
            if os.path.exists(path):
                with open(path,'rb') as f:
                    self.models[t] = pickle.load(f)
                loaded += 1
        dur_path = os.path.join(models_dir, 'duration_model.pkl')
        if os.path.exists(dur_path):
            with open(dur_path,'rb') as f:
                self.duration_model = pickle.load(f)
        meta_path = os.path.join(models_dir, 'resource_model_metadata.json')
        if os.path.exists(meta_path):
            with open(meta_path,'r') as f:
                self.metadata = json.load(f)
        self._loaded = loaded == 4
        status = "✅" if self._loaded else f"⚠️ ({loaded}/4)"
        print(f"[ResourceMLPredictor] Models loaded {status}")
        return self._loaded

    # ── Feature builder ──────────────────────────────────────────
    def _build_features(self, event_data: dict,
                        cascade_prob: float = 0.05,
                        severity_score: float = 5.0) -> list:
        from datetime import datetime, timedelta
        dt_str = event_data.get('start_datetime','')
        try:
            base = dt_str.split('+')[0].split('.')[0].replace('T',' ')
            ist  = datetime.strptime(base,'%Y-%m-%d %H:%M:%S') + timedelta(hours=5,minutes=30)
        except Exception:
            ist = datetime.now()

        hour = ist.hour; dow = ist.weekday(); month = ist.month
        hour_sin = math.sin(2*math.pi*hour/24); hour_cos = math.cos(2*math.pi*hour/24)
        dow_sin  = math.sin(2*math.pi*dow/7);   dow_cos  = math.cos(2*math.pi*dow/7)
        if   7<=hour<=10: ts=0
        elif 11<=hour<=16:ts=1
        elif 17<=hour<=21:ts=2
        elif 22<=hour or hour<=1:ts=3
        else: ts=4
        is_peak    = 1 if (7<=hour<=10 or 17<=hour<=21) else 0
        is_weekend = 1 if dow>=5 else 0
        lat = float(event_data.get('latitude',12.97))
        lon = float(event_data.get('longitude',77.59))
        dist = self._haversine(lat,lon,CITY_CENTER[0],CITY_CENTER[1])
        corridor  = event_data.get('corridor','Non-corridor') or 'Non-corridor'
        is_main   = 0 if corridor in ('Non-corridor','Unknown','',None) else 1
        cor_freq  = CORRIDOR_FREQ.get(corridor,0.01)
        cause     = (event_data.get('event_cause','others') or 'others').lower()
        cause_enc = CAUSE_LABELS.index(cause) if cause in CAUSE_LABELS else len(CAUSE_LABELS)
        cause_sev = CAUSE_SEVERITY.get(cause,3.0)
        priority  = event_data.get('priority','Low')
        pri_enc   = 1 if priority=='High' else 0
        is_plan   = 1 if event_data.get('event_type','')=='planned' else 0
        desc      = event_data.get('description','') or ''
        closure_r = HIST_CLOSURE_RATE.get(cause,0.05)
        avg_res   = AVG_RESOLUTION.get(cause,2.0)
        closure   = 1 if event_data.get('requires_road_closure') else 0

        return [
            hour, hour_sin, hour_cos, dow, dow_sin, dow_cos,
            month, ts, is_peak, is_weekend, 0,
            lat, lon, dist, is_main, cor_freq, 0.05, 0.01,
            cause_enc, cause_sev, pri_enc, is_plan,
            1 if desc else 0, min(len(desc),500),
            closure_r, 0.05, avg_res,
            cascade_prob, severity_score, closure,
        ]

    @staticmethod
    def _haversine(lat1,lon1,lat2,lon2):
        R=6371.0; dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
        a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R*2*math.asin(max(0,a)**0.5)

    # ── Core prediction ──────────────────────────────────────────
    def predict_resources(self, event_data: dict,
                          severity_score: float = 5.0,
                          cascade_prob: float = 0.05,
                          duration_hours: float = 4.0,
                          max_police: int = 50,
                          max_barricades: int = 100,
                          max_checkpoints: int = 20,
                          max_emergency: int = 10) -> ResourceMLResult:

        features = self._build_features(event_data, cascade_prob, severity_score)

        if self._loaded:
            police     = max(0, round(self.models['police'].predict_one(features)))
            barricades = max(0, round(self.models['barricades'].predict_one(features)))
            checkpoints= max(0, round(self.models['checkpoints'].predict_one(features)))
            emergency  = max(0, round(self.models['emergency'].predict_one(features)))
            method     = "ml_stacking_ensemble"
            confidence = 0.88
        else:
            # Rule-based fallback
            police     = max(2, math.ceil(severity_score*1.5))
            barricades = max(0, math.ceil(severity_score*1.2))
            checkpoints= max(0, math.ceil(severity_score*0.4))
            emergency  = max(0, math.ceil(severity_score*0.2))
            method     = "rule_based_fallback"
            confidence = 0.70

        # Apply caps
        police      = min(police,      max_police)
        barricades  = min(barricades,  max_barricades)
        checkpoints = min(checkpoints, max_checkpoints)
        emergency   = min(emergency,   max_emergency)

        total_cost = (
            police*COST['police']*duration_hours +
            barricades*COST['barricades']*duration_hours +
            checkpoints*COST['checkpoints']*duration_hours +
            emergency*COST['emergency']*duration_hours
        )

        # Resource efficiency: how close to minimum needed?
        min_needed = max(1, severity_score * 1.2)
        total_deployed = police + barricades + checkpoints + emergency
        efficiency = round(1.0 - abs(total_deployed - min_needed*4) / max(total_deployed,1), 4)
        efficiency = max(0.0, min(1.0, efficiency))

        # Conditional forecasting
        cond = self._conditional_forecast(event_data, severity_score, cascade_prob, duration_hours)

        explanation = (
            f"ML model ({method}) recommends: {police} police, {barricades} barricades, "
            f"{checkpoints} checkpoints, {emergency} emergency units. "
            f"Resource efficiency score: {efficiency:.2%}. "
            f"Estimated cost: ₹{round(total_cost):,} for {duration_hours}h deployment."
        )

        return ResourceMLResult(
            traffic_police=police,
            barricades=barricades,
            checkpoints=checkpoints,
            emergency_units=emergency,
            total_cost_estimate=round(total_cost, 2),
            resource_efficiency_score=efficiency,
            optimization_method=method,
            confidence=confidence,
            conditional_forecast=cond,
            explanation=explanation,
        )

    def _conditional_forecast(self, event_data, severity_score, cascade_prob, duration_hours):
        """Generate police-count → duration forecast table."""
        if not self.duration_model:
            return []
        table = []
        for k in range(0, 21, 2):
            ratio = k / max(severity_score * 1.5, 1)
            adj_sev = severity_score * max(0.4, 1.0 - (ratio-1)*0.1)
            feats = self._build_features(event_data, cascade_prob, adj_sev)
            dur = max(0.1, self.duration_model.predict_one(feats))
            dur = min(72, dur)
            cost = k * COST['police'] * dur
            table.append({
                "police_deployed": k,
                "estimated_duration_hours": round(dur, 2),
                "estimated_cost_inr": round(cost, 0),
                "efficiency_ratio": round(k / max(dur, 0.1), 3),
            })
        return table


# Singleton
resource_ml_predictor = ResourceMLPredictor()
