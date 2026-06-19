"""ML Predictor — loads trained models and makes predictions"""
import os
import pickle
import json
import math
from datetime import datetime, timedelta
from app.config import settings
from app.ml.cascade_predictor import cascade_predictor, CascadeResult
from app.ml.station_efficiency import load_leaderboard_cache, lookup_efficiency
from app.ml.weather_service import get_current_rainfall_mm

# Event cause severity mapping (must match training)
CAUSE_SEVERITY = {
    "vehicle_breakdown": 2.0, "pot_holes": 2.5, "road_conditions": 3.0,
    "water_logging": 4.0, "others": 2.5, "tree_fall": 5.0, "congestion": 4.5,
    "accident": 6.0, "construction": 5.5, "debris": 3.0, "fog_low_visibility": 3.5,
    "public_event": 7.5, "procession": 7.0, "vip_movement": 8.5, "protest": 8.0,
    "test_demo": 1.0,
}

CAUSE_LABELS = sorted(CAUSE_SEVERITY.keys())

# Historical stats from training data
HIST_CLOSURE_RATE = {
    "vehicle_breakdown": 0.043, "others": 0.086, "pot_holes": 0.024,
    "construction": 0.265, "water_logging": 0.085, "accident": 0.030,
    "tree_fall": 0.394, "road_conditions": 0.124, "congestion": 0.044,
    "public_event": 0.464, "procession": 0.264, "vip_movement": 0.800,
    "protest": 0.400, "debris": 0.083, "fog_low_visibility": 0.0,
}

# AVG_RESOLUTION in HOURS (converted from raw minutes in training data)
AVG_RESOLUTION = {
    "vehicle_breakdown": 1.0,  "others": 1.6,  "pot_holes": 2.9,
    "construction": 2.0,       "water_logging": 2.0, "accident": 0.8,
    "tree_fall": 1.3,          "road_conditions": 2.9, "congestion": 1.2,
    "public_event": 4.0,       "procession": 1.5, "vip_movement": 3.0,
    "protest": 0.7,            "debris": 6.4, "fog_low_visibility": 2.0,
}

CORRIDOR_FREQ = {
    "Non-corridor": 0.382, "Mysore Road": 0.091, "Bellary Road 1": 0.075,
    "Tumkur Road": 0.056, "Bellary Road 2": 0.046, "Hosur Road": 0.036,
}

CITY_CENTER = (12.9871, 77.5960)
DEFAULT_CASCADE_PROB = 0.05

class MLPredictor:
    def __init__(self):
        self.severity_model = None
        self.closure_model  = None
        self.duration_model = None
        self.metadata       = None
        self._loaded        = False
        # Cascade predictor is a sibling singleton loaded separately
        self._cascade_ready = False
    
    def load_models(self):
        """Load all trained models and the cascade matrix."""
        models_dir = settings.MODELS_DIR

        try:
            with open(os.path.join(models_dir, 'severity_model.pkl'), 'rb') as f:
                self.severity_model = pickle.load(f)
            with open(os.path.join(models_dir, 'closure_model.pkl'), 'rb') as f:
                self.closure_model = pickle.load(f)
            with open(os.path.join(models_dir, 'duration_model.pkl'), 'rb') as f:
                self.duration_model = pickle.load(f)
            with open(os.path.join(models_dir, 'model_metadata.json'), 'r') as f:
                self.metadata = json.load(f)
            self._loaded = True
            print(f"Models loaded from {models_dir}")
        except FileNotFoundError as e:
            print(f"Warning: Could not load models: {e}")
            self._loaded = False

        # Load cascade matrix (non-fatal if missing)
        cascade_matrix_path = os.path.join(
            os.path.dirname(models_dir), "ml", "data",
            "processed", "cascade_matrix.json"
        )
        self._cascade_ready = cascade_predictor.load_matrix(cascade_matrix_path)

        # Step 7: Load police station leaderboard for efficiency feature
        leaderboard_path = os.path.join(
            os.path.dirname(models_dir), "data",
            "processed", "leaderboard.json"
        )
        load_leaderboard_cache(leaderboard_path)
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def _build_features(self, event_data: dict,
                        cascade_prob: float = DEFAULT_CASCADE_PROB,
                        station_efficiency: float = 1.0,
                        rainfall_mm: float = 0.0) -> list:
        """Build feature vector (27 base + cascade_probability + station_efficiency + rainfall_mm = 30 features)."""
        # Parse datetime
        dt_str = event_data.get('start_datetime', '')
        try:
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_str.split('+')[0].split('.')[0], '%Y-%m-%d %H:%M:%S')
            ist = dt + timedelta(hours=5, minutes=30)
        except:
            ist = datetime.now()
        
        hour  = ist.hour
        dow   = ist.weekday()
        month = ist.month
        
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        dow_sin  = math.sin(2 * math.pi * dow / 7)
        dow_cos  = math.cos(2 * math.pi * dow / 7)
        
        if 7 <= hour <= 10:
            time_slot = 0
        elif 11 <= hour <= 16:
            time_slot = 1
        elif 17 <= hour <= 21:
            time_slot = 2
        elif 22 <= hour or hour <= 1:
            time_slot = 3
        else:
            time_slot = 4
        
        is_peak   = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
        is_weekend = 1 if dow >= 5 else 0
        is_holiday = 0
        
        lat  = float(event_data.get('latitude', 12.97))
        lon  = float(event_data.get('longitude', 77.59))
        dist = self._haversine(lat, lon, CITY_CENTER[0], CITY_CENTER[1])
        
        corridor         = event_data.get('corridor', 'Non-corridor')
        is_main_corridor = 0 if corridor in ('Non-corridor', 'Unknown', '', None) else 1
        corridor_freq    = CORRIDOR_FREQ.get(corridor, 0.01)
        zone_freq        = 0.05
        junction_freq    = 0.01
        
        cause         = event_data.get('event_cause', 'others').lower()
        cause_encoded = CAUSE_LABELS.index(cause) if cause in CAUSE_LABELS else len(CAUSE_LABELS)
        cause_severity = CAUSE_SEVERITY.get(cause, 3.0)
        
        priority         = event_data.get('priority', 'Low')
        priority_encoded = 1 if priority == 'High' else 0
        
        is_planned = 1 if event_data.get('event_type', '') == 'planned' else 0
        desc       = event_data.get('description', '') or ''
        has_desc   = 1 if len(desc) > 0 else 0
        desc_len   = min(len(desc), 500)
        
        closure_rate_cause     = HIST_CLOSURE_RATE.get(cause, 0.05)
        closure_rate_corridor  = 0.05
        avg_res                = AVG_RESOLUTION.get(cause, 2.0)
        
        features = [
            hour, hour_sin, hour_cos,
            dow, dow_sin, dow_cos,
            month, time_slot, is_peak,
            is_weekend, is_holiday,
            lat, lon, dist,
            is_main_corridor, corridor_freq,
            zone_freq, junction_freq,
            cause_encoded, cause_severity,
            priority_encoded, is_planned,
            has_desc, desc_len,
            closure_rate_cause, closure_rate_corridor,
            avg_res,
            # Feature 28: cascade probability (Step 3C)
            cascade_prob,
            # Feature 29: station efficiency score (Step 7)
            station_efficiency,
            # Feature 30: Real-Time Weather (rainfall in mm)
            rainfall_mm,
        ]
        return features
    
    def predict(self, event_data: dict) -> dict:
        """Make prediction for an event, including cascade analysis."""

        # ── Step 1: Compute cascade probability (Step 3C) ──
        try:
            ist_hour = datetime.now().hour  # quick fallback
            dt_str = event_data.get('start_datetime', '')
            if dt_str:
                try:
                    base_dt = datetime.strptime(
                        dt_str.split('+')[0].split('.')[0].replace('T', ' '),
                        '%Y-%m-%d %H:%M:%S'
                    )
                    ist_hour = (base_dt + timedelta(hours=5, minutes=30)).hour
                except Exception:
                    pass

            cascade_result: CascadeResult = cascade_predictor.predict_cascade(
                event_cause=event_data.get('event_cause', 'others'),
                junction=event_data.get('junction', 'Unknown') or 'Unknown',
                latitude=float(event_data.get('latitude', 12.97)),
                longitude=float(event_data.get('longitude', 77.59)),
                hour_ist=ist_hour,
                priority=event_data.get('priority', 'Low'),
            )
            cascade_prob = cascade_result.cascade_probability
        except Exception as exc:
            print(f"[Predictor] Cascade scoring failed: {exc}")
            cascade_prob   = DEFAULT_CASCADE_PROB
            cascade_result = None

        # ── Step 7: Look up police station efficiency score ──────────────────
        station = event_data.get('police_station', 'Unknown') or 'Unknown'
        station_eff = lookup_efficiency(station)

        # ── Step 8: Fetch real-time weather data ─────────────────────────────
        lat = float(event_data.get('latitude', CITY_CENTER[0]))
        lon = float(event_data.get('longitude', CITY_CENTER[1]))
        rainfall = get_current_rainfall_mm(lat, lon)

        # ── Step 2: Build feature vector (30 features) ─────────────────────
        features = self._build_features(event_data,
                                        cascade_prob=cascade_prob,
                                        station_efficiency=station_eff,
                                        rainfall_mm=rainfall)

        # ── Step 3: Run ML models ──────────────────────────────────────
        if self._loaded and self.severity_model:
            severity     = self.severity_model.predict_one(features)
            closure_prob = self.closure_model.predict_one(features)
            duration     = self.duration_model.predict_one(features)
        else:
            # Fallback: rule-based prediction
            cause        = event_data.get('event_cause', 'others').lower()
            severity     = CAUSE_SEVERITY.get(cause, 3.0)
            closure_prob = HIST_CLOSURE_RATE.get(cause, 0.05)
            duration     = AVG_RESOLUTION.get(cause, 2.0)
            # Still apply cascade duration multiplier in fallback mode
            if cascade_result:
                duration *= cascade_result.duration_multiplier

        # ── Step 4: Clamp RAW ML outputs ─────────────────────────────────────
        severity         = max(0.0, min(10.0, severity))
        closure_prob     = max(0.0, min(1.0,  closure_prob))
        # Cap raw ML duration at 12h max — real duration built formulaically in Step 5
        raw_ml_duration  = max(0.1, min(12.0, duration))

        # ── Step 5: Location-aware, formula-driven scoring ───────────────────
        cause = event_data.get('event_cause', '').lower()
        lat   = float(event_data.get('latitude',  CITY_CENTER[0]))
        lon   = float(event_data.get('longitude', CITY_CENTER[1]))
        dist_km = self._haversine(lat, lon, CITY_CENTER[0], CITY_CENTER[1])

        # LOCATION MULTIPLIER: linear decay from city center
        # location_mult = max(0.55, 1.0 - dist_km × 0.015)
        # MG Road (1.2km)   → 0.982   Whitefield (16km) → 0.760
        # Electronic City (17km) → 0.745   Hebbal (8km)  → 0.880
        location_mult = max(0.55, 1.0 - dist_km * 0.015)

        # SEVERITY: blend ML output with cause baseline, scaled by location
        base_cause_sev = CAUSE_SEVERITY.get(cause, 3.0)
        blended_sev = 0.6 * severity + 0.4 * (base_cause_sev * location_mult)

        if cause in ('public_event', 'procession', 'protest'):
            blended_sev = max(blended_sev, 5.0 * location_mult)
        if cause == 'vip_movement':
            blended_sev  = max(blended_sev, 7.5 * location_mult)
            closure_prob = max(closure_prob, 0.75 * location_mult)
        if event_data.get('requires_road_closure'):
            blended_sev  += 1.5 * location_mult
            closure_prob  = max(closure_prob, 0.70)
        priority = event_data.get('priority', 'Low')
        if priority == 'Critical':
            blended_sev += 0.5
        severity = min(10.0, max(0.0, blended_sev))

        # DURATION FORMULA ────────────────────────────────────────────────
        # Base = ML output (capped 12h) — primary predictor
        # hist_avg (now in hours) is a small correction weight only
        hist_avg  = AVG_RESOLUTION.get(cause, 2.0)
        base_dur  = 0.75 * raw_ml_duration + 0.25 * hist_avg

        # D_final = base × location_factor × cause_factor × closure_factor × priority_factor
        # location: center zones take longer to clear (more cascade, more traffic layers)
        # formula: 1.0 + 0.20 * location_mult  →  center=×1.196, outskirts=×1.110
        loc_factor      = 1.0 + 0.20 * location_mult

        # closure adds delay proportional to how busy the location is
        closure_factor  = (1.0 + 0.15 * location_mult) if event_data.get('requires_road_closure') else 1.0

        cause_factors   = {
            'vip_movement': 1.30, 'procession': 1.20, 'protest': 1.15,
            'public_event': 1.10, 'accident': 1.08, 'construction': 1.05,
            'tree_fall': 1.05,  'water_logging': 1.03,
        }
        cause_factor    = cause_factors.get(cause, 1.0)
        priority_factor = 1.10 if priority == 'Critical' else (1.05 if priority == 'High' else 1.0)
        # Cascade: cap multiplier at 1.3 to avoid runaway
        cascade_mult    = min(1.30, cascade_result.duration_multiplier if cascade_result else 1.0)

        duration = base_dur * loc_factor * cause_factor * closure_factor * priority_factor * cascade_mult
        duration = max(0.5, min(20.0, duration))

        # ── Step 6: Labels and confidence ────────────────────────────
        if severity <= 3:
            label = "Low"
        elif severity <= 5:
            label = "Medium"
        elif severity <= 7:
            label = "High"
        else:
            label = "Critical"

        confidence = 0.85 if self._loaded else 0.70

        # ── Step 7: Build response dict ───────────────────────────────
        response = {
            'severity_score':            round(severity, 2),
            'severity_label':            label,
            'closure_probability':       round(closure_prob, 4),
            'estimated_duration_hours':  round(duration, 2),
            'confidence':                confidence,
            'model_version':             (
                self.metadata.get('model_version', 'v2.0.0')
                if self.metadata else 'v2.0.0-fallback'
            ),
            # Step 3C cascade data (exposed to API)
            'cascade_probability':       cascade_prob,
            'cascade_risk_level':        cascade_result.risk_level if cascade_result else 'Unknown',
            'cascade_affected_junctions': cascade_result.likely_affected_junctions if cascade_result else [],
            'cascade_duration_multiplier': cascade_result.duration_multiplier if cascade_result else 1.0,
            'cascade_explanation':       cascade_result.explanation if cascade_result else '',
        }
        return response


# Singleton instance
predictor = MLPredictor()

# Constant used in predict() for fallback cascade prob
DEFAULT_CASCADE_PROB = 0.05
