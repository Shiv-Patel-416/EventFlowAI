"""ML Predictor — loads trained models and makes predictions"""
import os
import pickle
import json
import math
from datetime import datetime, timedelta
from app.config import settings

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

AVG_RESOLUTION = {
    "vehicle_breakdown": 0.97, "others": 93.57, "pot_holes": 173.25,
    "construction": 118.02, "water_logging": 117.20, "accident": 0.80,
    "tree_fall": 79.41, "road_conditions": 172.08, "congestion": 1.24,
    "public_event": 4.0, "procession": 0.91, "vip_movement": 3.0,
    "protest": 0.41, "debris": 382.97, "fog_low_visibility": 2.0,
}

CORRIDOR_FREQ = {
    "Non-corridor": 0.382, "Mysore Road": 0.091, "Bellary Road 1": 0.075,
    "Tumkur Road": 0.056, "Bellary Road 2": 0.046, "Hosur Road": 0.036,
}

CITY_CENTER = (12.9871, 77.5960)

class MLPredictor:
    def __init__(self):
        self.severity_model = None
        self.closure_model = None
        self.duration_model = None
        self.metadata = None
        self._loaded = False
    
    def load_models(self):
        """Load all trained models."""
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
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def _build_features(self, event_data: dict) -> list:
        """Build feature vector from event data."""
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
        
        hour = ist.hour
        dow = ist.weekday()
        month = ist.month
        
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        dow_sin = math.sin(2 * math.pi * dow / 7)
        dow_cos = math.cos(2 * math.pi * dow / 7)
        
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
        
        is_peak = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
        is_weekend = 1 if dow >= 5 else 0
        is_holiday = 0
        
        lat = float(event_data.get('latitude', 12.97))
        lon = float(event_data.get('longitude', 77.59))
        dist = self._haversine(lat, lon, CITY_CENTER[0], CITY_CENTER[1])
        
        corridor = event_data.get('corridor', 'Non-corridor')
        is_main_corridor = 0 if corridor in ('Non-corridor', 'Unknown', '', None) else 1
        corridor_freq = CORRIDOR_FREQ.get(corridor, 0.01)
        zone_freq = 0.05
        junction_freq = 0.01
        
        cause = event_data.get('event_cause', 'others').lower()
        cause_encoded = CAUSE_LABELS.index(cause) if cause in CAUSE_LABELS else len(CAUSE_LABELS)
        cause_severity = CAUSE_SEVERITY.get(cause, 3.0)
        
        priority = event_data.get('priority', 'Low')
        priority_encoded = 1 if priority == 'High' else 0
        
        is_planned = 1 if event_data.get('event_type', '') == 'planned' else 0
        desc = event_data.get('description', '') or ''
        has_desc = 1 if len(desc) > 0 else 0
        desc_len = min(len(desc), 500)
        
        closure_rate_cause = HIST_CLOSURE_RATE.get(cause, 0.05)
        closure_rate_corridor = 0.05  # default
        avg_res = AVG_RESOLUTION.get(cause, 2.0)
        
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
        ]
        
        return features
    
    def predict(self, event_data: dict) -> dict:
        """Make prediction for an event."""
        features = self._build_features(event_data)
        
        if self._loaded and self.severity_model:
            severity = self.severity_model.predict_one(features)
            closure_prob = self.closure_model.predict_one(features)
            duration = self.duration_model.predict_one(features)
        else:
            # Fallback: rule-based prediction
            cause = event_data.get('event_cause', 'others').lower()
            severity = CAUSE_SEVERITY.get(cause, 3.0)
            closure_prob = HIST_CLOSURE_RATE.get(cause, 0.05)
            duration = AVG_RESOLUTION.get(cause, 2.0)
        
        # Clamp values
        severity = max(0, min(10, severity))
        closure_prob = max(0, min(1, closure_prob))
        duration = max(0.1, min(72, duration))
        
        # Apply event-specific boosts
        cause = event_data.get('event_cause', '').lower()
        if cause in ('public_event', 'procession', 'vip_movement', 'protest'):
            severity = max(severity, 6.0)
            if cause == 'vip_movement':
                severity = max(severity, 8.0)
                closure_prob = max(closure_prob, 0.8)
        
        if event_data.get('requires_road_closure'):
            severity *= 1.2
            severity = min(severity, 10.0)
            closure_prob = max(closure_prob, 0.7)
        
        # Severity label
        if severity <= 3:
            label = "Low"
        elif severity <= 5:
            label = "Medium"
        elif severity <= 7:
            label = "High"
        else:
            label = "Critical"
        
        # Confidence
        confidence = 0.85 if self._loaded else 0.70
        
        return {
            'severity_score': round(severity, 2),
            'severity_label': label,
            'closure_probability': round(closure_prob, 4),
            'estimated_duration_hours': round(duration, 2),
            'confidence': confidence,
            'model_version': self.metadata.get('model_version', 'v1.0.0') if self.metadata else 'v1.0.0-fallback',
        }


# Singleton instance
predictor = MLPredictor()
