"""Retrain models with proper class references for pickle compatibility."""
import sys
import os
import csv
import json
import math
import random
import pickle
from collections import defaultdict

# Add the backend app to sys.path so pickle stores the right module reference
backend_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
sys.path.insert(0, backend_path)

# Import model classes from the backend module
from app.ml.model_classes import GradientBoostingModel, SimpleDecisionStump

def load_features(filepath):
    features = []
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            features.append(row)
    print(f"Loaded {len(features)} records")
    return features

def prepare_data(features):
    feature_cols = [
        'hour_ist', 'hour_sin', 'hour_cos',
        'day_of_week', 'dow_sin', 'dow_cos',
        'month', 'time_slot', 'is_peak_hour',
        'is_weekend', 'is_holiday',
        'latitude', 'longitude', 'distance_to_center_km',
        'is_main_corridor', 'corridor_event_freq',
        'zone_event_freq', 'junction_event_freq',
        'event_cause_encoded', 'cause_base_severity',
        'priority_encoded', 'is_planned',
        'has_description', 'description_length',
        'hist_closure_rate_cause', 'hist_closure_rate_corridor',
        'avg_resolution_time_cause',
        # Step 3C: Cascade feature — injected by cascade_analyzer
        'cascade_probability',
    ]
    
    X, y_sev, y_clo, y_dur = [], [], [], []
    for f in features:
        row = [float(f.get(col, 0) or 0) for col in feature_cols]
        X.append(row)
        y_sev.append(float(f['severity_score']))
        y_clo.append(int(float(f['requires_road_closure'])))
        dur = f.get('resolution_hours', '')
        y_dur.append(float(dur) if dur and dur not in ('', 'None') else None)
    
    return X, y_sev, y_clo, y_dur, feature_cols

def split(X, y, ratio=0.2, seed=42):
    random.seed(seed)
    n = len(X)
    idx = list(range(n))
    random.shuffle(idx)
    s = int(n * (1 - ratio))
    return [X[i] for i in idx[:s]], [X[i] for i in idx[s:]], [y[i] for i in idx[:s]], [y[i] for i in idx[s:]]

def evaluate(y_true, y_pred):
    n = len(y_true)
    mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n
    mse = sum((y_true[i] - y_pred[i])**2 for i in range(n)) / n
    rmse = math.sqrt(mse)
    y_mean = sum(y_true) / n
    ss_tot = sum((y_true[i] - y_mean)**2 for i in range(n))
    ss_res = sum((y_true[i] - y_pred[i])**2 for i in range(n))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return {'mae': round(mae, 4), 'rmse': round(rmse, 4), 'r2': round(r2, 4)}

if __name__ == '__main__':
    features_path = os.path.join(os.path.dirname(__file__), 'data', 'processed', 'features.csv')
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    features = load_features(features_path)
    X, y_sev, y_clo, y_dur, cols = prepare_data(features)
    
    # Train severity model
    print("Training Severity Model...")
    Xtr, Xte, ytr, yte = split(X, y_sev)
    sev_model = GradientBoostingModel(n_estimators=200, learning_rate=0.05, task='regression')
    sev_model.fit(Xtr, ytr, feature_names=cols)
    pred = sev_model.predict(Xte)
    metrics_sev = evaluate(yte, pred)
    print(f"  Severity: {metrics_sev}")
    
    with open(os.path.join(models_dir, 'severity_model.pkl'), 'wb') as f:
        pickle.dump(sev_model, f)
    
    # Train closure model
    print("Training Closure Model...")
    Xtr, Xte, ytr, yte = split(X, y_clo)
    clo_model = GradientBoostingModel(n_estimators=200, learning_rate=0.05, task='classification')
    clo_model.fit(Xtr, ytr, feature_names=cols)
    
    with open(os.path.join(models_dir, 'closure_model.pkl'), 'wb') as f:
        pickle.dump(clo_model, f)
    
    # Train duration model
    print("Training Duration Model...")
    X_dur = [X[i] for i in range(len(X)) if y_dur[i] is not None]
    y_dur_clean = [min(y_dur[i], 48.0) for i in range(len(y_dur)) if y_dur[i] is not None]
    Xtr, Xte, ytr, yte = split(X_dur, y_dur_clean)
    dur_model = GradientBoostingModel(n_estimators=150, learning_rate=0.05, task='regression')
    dur_model.fit(Xtr, ytr, feature_names=cols)
    pred = dur_model.predict(Xte)
    metrics_dur = evaluate(yte, pred)
    print(f"  Duration: {metrics_dur}")
    
    with open(os.path.join(models_dir, 'duration_model.pkl'), 'wb') as f:
        pickle.dump(dur_model, f)
    
    # Save metadata
    meta = {
        'feature_columns': cols,
        'n_features': len(cols),
        'severity_metrics': metrics_sev,
        'duration_metrics': metrics_dur,
        'training_samples': len(X),
        'model_version': 'v1.0.0',
    }
    with open(os.path.join(models_dir, 'model_metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    
    print("All models retrained with proper class references!")
