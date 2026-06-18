"""
EventFlow AI — Data Pipeline
Cleans raw Astram event data and engineers features for ML models.
Includes Cascade Probability injection (Step 3C).
"""

import csv
import json
import math
import os
import pickle
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# Import cascade analyzer for co-occurrence-based feature injection
from ml.src.cascade_analyzer import (
    build_cooccurrence_matrix,
    compute_cascade_scores,
    save_matrix,
)

IST = timezone(timedelta(hours=5, minutes=30))
CITY_CENTER = (12.9871, 77.5960)

# Karnataka holidays 2023-2024
HOLIDAYS = {
    "2023-11-13", "2023-11-14", "2023-11-27", "2023-12-25",
    "2024-01-01", "2024-01-15", "2024-01-26", "2024-02-14",
    "2024-03-08", "2024-03-25", "2024-03-29", "2024-04-01",
    "2024-04-09", "2024-04-11", "2024-04-14", "2024-04-17",
}

# Event cause severity base scores
CAUSE_SEVERITY = {
    "vehicle_breakdown": 2.0,
    "pot_holes": 2.5,
    "road_conditions": 3.0,
    "water_logging": 4.0,
    "others": 2.5,
    "tree_fall": 5.0,
    "congestion": 4.5,
    "accident": 6.0,
    "construction": 5.5,
    "debris": 3.0,
    "fog / low visibility": 3.5,
    "public_event": 7.5,
    "procession": 7.0,
    "vip_movement": 8.5,
    "protest": 8.0,
    "test_demo": 1.0,
}

CORRIDOR_IMPORTANCE = {}  # Will be populated from data

CAUSE_LABELS = sorted(CAUSE_SEVERITY.keys())
EVENT_TYPE_MAP = {"unplanned": 0, "planned": 1}
PRIORITY_MAP = {"Low": 0, "High": 1}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def parse_datetime(dt_str):
    """Parse datetime string to datetime object."""
    if not dt_str or dt_str.strip() in ('NULL', 'null', ''):
        return None
    try:
        # Remove fractional seconds and timezone for simpler parsing
        clean = dt_str.strip()
        if '+' in clean:
            base = clean.split('+')[0]
        else:
            base = clean
        if '.' in base:
            base = base.split('.')[0]
        return datetime.strptime(base, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def to_ist(dt):
    """Convert UTC datetime to IST."""
    if dt is None:
        return None
    return dt + timedelta(hours=5, minutes=30)

def load_raw_data(filepath):
    """Load raw CSV data."""
    rows = []
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"Loaded {len(rows)} raw records")
    return rows

def clean_data(rows):
    """Clean and normalize raw data."""
    cleaned = []
    for r in rows:
        # Skip test events
        if r['event_cause'].lower() == 'test_demo':
            continue
        
        # Normalize event_cause
        cause = r['event_cause'].lower().strip()
        if cause == 'fog / low visibility':
            cause = 'fog_low_visibility'
        cause = cause.replace(' ', '_')
        
        # Parse coordinates
        try:
            lat = float(r['latitude'])
            lon = float(r['longitude'])
            if lat == 0 or lon == 0:
                continue
        except:
            continue
        
        # Parse datetime
        start_dt = parse_datetime(r['start_datetime'])
        if start_dt is None:
            continue
        start_ist = to_ist(start_dt)
        
        end_dt = parse_datetime(r.get('end_datetime', ''))
        closed_dt = parse_datetime(r.get('closed_datetime', ''))
        resolved_dt = parse_datetime(r.get('resolved_datetime', ''))
        
        # Calculate resolution time
        resolution_dt = closed_dt or resolved_dt
        resolution_hours = None
        if resolution_dt and start_dt:
            diff = (resolution_dt - start_dt).total_seconds() / 3600
            if 0 < diff < 720:
                resolution_hours = diff
        
        # Calculate planned duration
        planned_duration = None
        if end_dt and start_dt:
            diff = (end_dt - start_dt).total_seconds() / 3600
            if 0 < diff < 720:
                planned_duration = diff
        
        # Clean other fields
        corridor = r.get('corridor', '').strip() or 'Unknown'
        zone = r.get('zone', '').strip()
        if zone in ('NULL', 'null', ''):
            zone = 'Unknown'
        junction = r.get('junction', '').strip()
        if junction in ('NULL', 'null', ''):
            junction = 'Unknown'
        police_station = r.get('police_station', '').strip()
        if police_station in ('NULL', 'null', ''):
            police_station = 'Unknown'
        
        priority = r.get('priority', 'Low').strip()
        if priority in ('NULL', 'null', ''):
            priority = 'Low'
        
        requires_closure = r.get('requires_road_closure', 'FALSE').strip().upper() == 'TRUE'
        is_planned = r.get('event_type', '').strip() == 'planned'
        
        description = r.get('description', '').strip()
        if description in ('NULL', 'null'):
            description = ''
        
        veh_type = r.get('veh_type', '').strip()
        if veh_type in ('NULL', 'null', ''):
            veh_type = 'none'
        
        cleaned.append({
            'id': r['id'],
            'event_type': r.get('event_type', 'unplanned').strip(),
            'is_planned': is_planned,
            'latitude': lat,
            'longitude': lon,
            'event_cause': cause,
            'requires_road_closure': requires_closure,
            'start_datetime_utc': start_dt.isoformat(),
            'start_datetime_ist': start_ist.isoformat(),
            'hour_ist': start_ist.hour,
            'day_of_week': start_ist.weekday(),
            'month': start_ist.month,
            'is_weekend': start_ist.weekday() >= 5,
            'is_holiday': start_ist.strftime('%Y-%m-%d') in HOLIDAYS,
            'resolution_hours': resolution_hours,
            'planned_duration_hours': planned_duration,
            'status': r.get('status', '').strip(),
            'priority': priority,
            'corridor': corridor,
            'zone': zone,
            'junction': junction,
            'police_station': police_station,
            'description': description,
            'description_length': len(description),
            'has_description': len(description) > 0,
            'veh_type': veh_type,
            'gba_identifier': r.get('gba_identifier', '').strip(),
        })
    
    print(f"Cleaned: {len(cleaned)} records (removed {len(rows) - len(cleaned)})")
    return cleaned

def engineer_features(records):
    """Create ML features from cleaned records."""
    
    # Pre-compute aggregations
    corridor_counts = Counter(r['corridor'] for r in records)
    zone_counts = Counter(r['zone'] for r in records)
    junction_counts = Counter(r['junction'] for r in records)
    cause_counts = Counter(r['event_cause'] for r in records)
    ps_counts = Counter(r['police_station'] for r in records)
    
    # Historical closure rates by location/cause
    closure_by_cause = defaultdict(list)
    closure_by_corridor = defaultdict(list)
    resolution_by_cause = defaultdict(list)
    
    for r in records:
        closure_by_cause[r['event_cause']].append(r['requires_road_closure'])
        closure_by_corridor[r['corridor']].append(r['requires_road_closure'])
        if r['resolution_hours'] is not None:
            resolution_by_cause[r['event_cause']].append(r['resolution_hours'])
    
    closure_rate_cause = {k: sum(v)/len(v) for k, v in closure_by_cause.items()}
    closure_rate_corridor = {k: sum(v)/len(v) for k, v in closure_by_corridor.items()}
    avg_resolution_cause = {k: sum(v)/len(v) for k, v in resolution_by_cause.items()}
    
    # Encode corridors, zones, etc. with frequency encoding
    corridor_freq = {k: v/len(records) for k, v in corridor_counts.items()}
    zone_freq = {k: v/len(records) for k, v in zone_counts.items()}
    junction_freq = {k: v/len(records) for k, v in junction_counts.items()}
    ps_freq = {k: v/len(records) for k, v in ps_counts.items()}
    
    # Build event index by location for rolling features
    events_by_corridor_date = defaultdict(list)
    events_by_zone_date = defaultdict(list)
    for r in records:
        date_str = r['start_datetime_ist'][:10]
        events_by_corridor_date[(r['corridor'], date_str)].append(r)
        events_by_zone_date[(r['zone'], date_str)].append(r)
    
    features_list = []
    
    for r in records:
        # Temporal features
        hour = r['hour_ist']
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        
        dow = r['day_of_week']
        dow_sin = math.sin(2 * math.pi * dow / 7)
        dow_cos = math.cos(2 * math.pi * dow / 7)
        
        # Time slot
        if 7 <= hour <= 10:
            time_slot = 0  # morning rush
        elif 11 <= hour <= 16:
            time_slot = 1  # midday
        elif 17 <= hour <= 21:
            time_slot = 2  # evening rush
        elif 22 <= hour or hour <= 1:
            time_slot = 3  # late evening
        else:
            time_slot = 4  # night
        
        is_peak = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
        
        # Spatial features
        dist_to_center = haversine(r['latitude'], r['longitude'], CITY_CENTER[0], CITY_CENTER[1])
        
        # Event features
        cause = r['event_cause']
        cause_base_severity = CAUSE_SEVERITY.get(cause, 3.0)
        
        # Corridor importance (non-corridor = low)
        is_main_corridor = 0 if r['corridor'] in ('Non-corridor', 'Unknown') else 1
        
        # Compute severity score (target variable)
        severity = cause_base_severity
        if r['requires_road_closure']:
            severity *= 1.4
        if r['priority'] == 'High':
            severity *= 1.2
        if is_main_corridor:
            severity *= 1.15
        if is_peak:
            severity *= 1.1
        severity = min(severity, 10.0)
        severity = round(severity, 2)
        
        # Historical features
        hist_closure_rate_cause = closure_rate_cause.get(cause, 0.1)
        hist_closure_rate_corridor = closure_rate_corridor.get(r['corridor'], 0.05)
        avg_res_time = avg_resolution_cause.get(cause, 2.0)
        
        corridor_event_freq = corridor_freq.get(r['corridor'], 0.01)
        zone_event_freq = zone_freq.get(r['zone'], 0.01)
        junction_event_freq = junction_freq.get(r['junction'], 0.01)
        
        # Encode categoricals
        cause_encoded = CAUSE_LABELS.index(cause) if cause in CAUSE_LABELS else len(CAUSE_LABELS)
        priority_encoded = PRIORITY_MAP.get(r['priority'], 0)
        is_planned = 1 if r['is_planned'] else 0
        has_description = 1 if r['has_description'] else 0
        requires_closure_int = 1 if r['requires_road_closure'] else 0
        is_weekend = 1 if r['is_weekend'] else 0
        is_holiday = 1 if r['is_holiday'] else 0
        
        feature = {
            # Identifiers (not used in training)
            'id': r['id'],
            'start_datetime_ist': r['start_datetime_ist'],
            'corridor': r['corridor'],
            'zone': r['zone'],
            'junction': r['junction'],
            'event_cause_name': cause,
            
            # Target variables
            'severity_score': severity,
            'requires_road_closure': requires_closure_int,
            'resolution_hours': r['resolution_hours'],
            
            # Temporal features
            'hour_ist': hour,
            'hour_sin': round(hour_sin, 4),
            'hour_cos': round(hour_cos, 4),
            'day_of_week': dow,
            'dow_sin': round(dow_sin, 4),
            'dow_cos': round(dow_cos, 4),
            'month': r['month'],
            'time_slot': time_slot,
            'is_peak_hour': is_peak,
            'is_weekend': is_weekend,
            'is_holiday': is_holiday,
            
            # Spatial features
            'latitude': r['latitude'],
            'longitude': r['longitude'],
            'distance_to_center_km': round(dist_to_center, 3),
            'is_main_corridor': is_main_corridor,
            'corridor_event_freq': round(corridor_event_freq, 4),
            'zone_event_freq': round(zone_event_freq, 4),
            'junction_event_freq': round(junction_event_freq, 4),
            
            # Event features
            'event_cause_encoded': cause_encoded,
            'cause_base_severity': cause_base_severity,
            'priority_encoded': priority_encoded,
            'is_planned': is_planned,
            'has_description': has_description,
            'description_length': min(r['description_length'], 500),
            
            # Historical features
            'hist_closure_rate_cause': round(hist_closure_rate_cause, 4),
            'hist_closure_rate_corridor': round(hist_closure_rate_corridor, 4),
            'avg_resolution_time_cause': round(avg_res_time, 2),

            # Cascade feature (Step 3C) — injected after co-occurrence analysis
            # Placeholder; will be overwritten by compute_cascade_scores()
            'cascade_probability': 0.05,
        }
        
        features_list.append(feature)
    
    print(f"Engineered features for {len(features_list)} records")
    return features_list

def save_processed(features, output_dir):
    """Save processed features to CSV and metadata."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as CSV
    filepath = os.path.join(output_dir, 'features.csv')
    if features:
        keys = features[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(features)
    
    # Save metadata
    meta = {
        'total_records': len(features),
        'feature_columns': [k for k in features[0].keys() if k not in ('id', 'start_datetime_ist', 'corridor', 'zone', 'junction', 'event_cause_name', 'severity_score', 'requires_road_closure', 'resolution_hours')],
        'target_columns': ['severity_score', 'requires_road_closure', 'resolution_hours'],
        'id_columns': ['id', 'start_datetime_ist', 'corridor', 'zone', 'junction', 'event_cause_name'],
        'cause_labels': CAUSE_LABELS,
        'cause_severity_map': CAUSE_SEVERITY,
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    
    print(f"Saved {len(features)} records to {filepath}")
    return filepath

def run_pipeline(raw_path, output_dir):
    """Run the complete data pipeline, including cascade feature injection."""
    print("=" * 60)
    print("EventFlow AI — Data Pipeline (with Cascade Analysis)")
    print("=" * 60)

    # ── Step 1: Load raw data ────────────────────────
    rows = load_raw_data(raw_path)

    # ── Step 2: Clean & normalise ────────────────────
    cleaned = clean_data(rows)

    # ── Step 3: Cascade co-occurrence matrix ─────────
    print("\n[Cascade Analyzer] Building co-occurrence matrix...")
    matrix = build_cooccurrence_matrix(raw_path)
    save_matrix(matrix, output_dir)

    # ── Step 4: Inject cascade scores into cleaned records ──
    print("\n[Cascade Analyzer] Scoring each event for cascade probability...")
    cleaned = compute_cascade_scores(cleaned, matrix)

    # ── Step 5: Full feature engineering ────────────
    features = engineer_features(cleaned)

    # Propagate cascade_probability from enriched cleaned records
    # (engineer_features re-builds features from cleaned, so we copy it over)
    cascade_map = {r['id']: r['cascade_probability'] for r in cleaned}
    for f in features:
        f['cascade_probability'] = cascade_map.get(f['id'], 0.05)

    # ── Step 6: Save ─────────────────────────────────
    save_processed(features, output_dir)

    # ── Summary stats ────────────────────────────────
    severities   = [f['severity_score'] for f in features]
    closures     = [f['requires_road_closure'] for f in features]
    cascades     = [f['cascade_probability'] for f in features]
    print(f"\nSeverity Score : min={min(severities):.1f}, "
          f"max={max(severities):.1f}, mean={sum(severities)/len(severities):.2f}")
    print(f"Road Closure   : {sum(closures)} / {len(closures)} "
          f"({sum(closures)/len(closures)*100:.1f}%)")
    print(f"Cascade Prob   : min={min(cascades):.3f}, "
          f"max={max(cascades):.3f}, mean={sum(cascades)/len(cascades):.3f}")

    res_times = [f['resolution_hours'] for f in features if f['resolution_hours'] is not None]
    if res_times:
        print(f"Resolution Time: mean={sum(res_times)/len(res_times):.2f}h, "
              f"available for {len(res_times)} records")

    return features

if __name__ == '__main__':
    import sys
    raw_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'events_raw.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    run_pipeline(raw_path, output_dir)
