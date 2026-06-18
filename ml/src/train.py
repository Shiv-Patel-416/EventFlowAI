"""
EventFlow AI — Model Training
Trains severity, closure, and duration models.
Duration model now includes cascade_probability as a feature (Step 3C).
"""

import csv
import json
import math
import os
import pickle
import random
from collections import defaultdict

# We'll use simple implementations since we don't know what's installed
# The models will be gradient-boosted decision tree approximations

class SimpleDecisionStump:
    """A simple decision stump for gradient boosting."""
    def __init__(self):
        self.feature_idx = 0
        self.threshold = 0.0
        self.left_val = 0.0
        self.right_val = 0.0
    
    def fit(self, X, residuals, sample_weights=None):
        n_samples = len(X)
        if n_samples == 0:
            return
        n_features = len(X[0])
        
        best_loss = float('inf')
        
        # Try random subset of features (like colsample)
        feature_indices = random.sample(range(n_features), min(max(n_features // 2, 1), n_features))
        
        for feat_idx in feature_indices:
            values = [X[i][feat_idx] for i in range(n_samples)]
            sorted_vals = sorted(set(values))
            
            if len(sorted_vals) <= 1:
                continue
            
            # Try a few thresholds
            n_thresholds = min(10, len(sorted_vals) - 1)
            step = max(1, len(sorted_vals) // n_thresholds)
            thresholds = [sorted_vals[i] for i in range(0, len(sorted_vals) - 1, step)]
            
            for thresh in thresholds:
                left_res = [residuals[i] for i in range(n_samples) if X[i][feat_idx] <= thresh]
                right_res = [residuals[i] for i in range(n_samples) if X[i][feat_idx] > thresh]
                
                if not left_res or not right_res:
                    continue
                
                left_val = sum(left_res) / len(left_res)
                right_val = sum(right_res) / len(right_res)
                
                loss = sum((residuals[i] - (left_val if X[i][feat_idx] <= thresh else right_val))**2 for i in range(n_samples))
                
                if loss < best_loss:
                    best_loss = loss
                    self.feature_idx = feat_idx
                    self.threshold = thresh
                    self.left_val = left_val
                    self.right_val = right_val
    
    def predict_one(self, x):
        if x[self.feature_idx] <= self.threshold:
            return self.left_val
        return self.right_val

class GradientBoostingModel:
    """Simple gradient boosting implementation."""
    
    def __init__(self, n_estimators=200, learning_rate=0.05, max_features=0.8, task='regression'):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_features = max_features
        self.task = task
        self.trees = []
        self.base_prediction = 0.0
        self.feature_names = []
    
    def fit(self, X, y, feature_names=None):
        self.feature_names = feature_names or [f'f{i}' for i in range(len(X[0]))]
        n_samples = len(X)
        
        if self.task == 'classification':
            # Convert to log-odds for logistic regression
            pos = sum(y)
            neg = n_samples - pos
            if pos == 0 or neg == 0:
                self.base_prediction = 0.0
            else:
                self.base_prediction = math.log(pos / neg)
        else:
            self.base_prediction = sum(y) / n_samples
        
        predictions = [self.base_prediction] * n_samples
        
        for i in range(self.n_estimators):
            if self.task == 'classification':
                # Logistic loss gradient
                probs = [1.0 / (1.0 + math.exp(-p)) for p in predictions]
                residuals = [y[j] - probs[j] for j in range(n_samples)]
            else:
                residuals = [y[j] - predictions[j] for j in range(n_samples)]
            
            stump = SimpleDecisionStump()
            stump.fit(X, residuals)
            self.trees.append(stump)
            
            for j in range(n_samples):
                predictions[j] += self.learning_rate * stump.predict_one(X[j])
            
            if (i + 1) % 50 == 0:
                if self.task == 'classification':
                    probs = [1.0 / (1.0 + math.exp(-min(max(p, -10), 10))) for p in predictions]
                    loss = -sum(y[j] * math.log(max(probs[j], 1e-10)) + (1-y[j]) * math.log(max(1-probs[j], 1e-10)) for j in range(n_samples)) / n_samples
                    print(f"  Iteration {i+1}/{self.n_estimators}: log_loss={loss:.4f}")
                else:
                    mse = sum((y[j] - predictions[j])**2 for j in range(n_samples)) / n_samples
                    print(f"  Iteration {i+1}/{self.n_estimators}: MSE={mse:.4f}, RMSE={math.sqrt(mse):.4f}")
    
    def predict(self, X):
        results = []
        for x in X:
            pred = self.base_prediction
            for tree in self.trees:
                pred += self.learning_rate * tree.predict_one(x)
            
            if self.task == 'classification':
                prob = 1.0 / (1.0 + math.exp(-min(max(pred, -10), 10)))
                results.append(prob)
            else:
                results.append(pred)
        return results
    
    def predict_one(self, x):
        return self.predict([x])[0]
    
    def feature_importance(self):
        importance = defaultdict(int)
        for tree in self.trees:
            importance[self.feature_names[tree.feature_idx]] += 1
        total = sum(importance.values()) or 1
        return {k: round(v/total, 4) for k, v in sorted(importance.items(), key=lambda x: -x[1])}


def load_features(filepath):
    """Load processed features CSV."""
    features = []
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            features.append(row)
    print(f"Loaded {len(features)} feature records")
    return features

def prepare_training_data(features):
    """Prepare X, y arrays for training."""
    
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
        # Step 3C: Cascade feature — explains long-tail durations
        'cascade_probability',
    ]
    
    X = []
    y_severity = []
    y_closure = []
    y_duration = []
    
    for f in features:
        row = []
        for col in feature_cols:
            val = f.get(col, 0)
            try:
                row.append(float(val))
            except:
                row.append(0.0)
        
        X.append(row)
        y_severity.append(float(f['severity_score']))
        y_closure.append(int(float(f['requires_road_closure'])))
        
        dur = f.get('resolution_hours', '')
        if dur and dur not in ('', 'None'):
            y_duration.append(float(dur))
        else:
            y_duration.append(None)
    
    return X, y_severity, y_closure, y_duration, feature_cols

def train_test_split(X, y, test_ratio=0.2, seed=42):
    """Simple train/test split."""
    random.seed(seed)
    n = len(X)
    indices = list(range(n))
    random.shuffle(indices)
    split = int(n * (1 - test_ratio))
    
    train_idx = indices[:split]
    test_idx = indices[split:]
    
    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    
    return X_train, X_test, y_train, y_test

def evaluate_regression(y_true, y_pred):
    """Calculate regression metrics."""
    n = len(y_true)
    mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n
    mse = sum((y_true[i] - y_pred[i])**2 for i in range(n)) / n
    rmse = math.sqrt(mse)
    
    y_mean = sum(y_true) / n
    ss_tot = sum((y_true[i] - y_mean)**2 for i in range(n))
    ss_res = sum((y_true[i] - y_pred[i])**2 for i in range(n))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {'mae': round(mae, 4), 'rmse': round(rmse, 4), 'r2': round(r2, 4), 'mse': round(mse, 4)}

def evaluate_classification(y_true, y_prob, threshold=0.5):
    """Calculate classification metrics."""
    y_pred = [1 if p >= threshold else 0 for p in y_prob]
    n = len(y_true)
    
    tp = sum(1 for i in range(n) if y_true[i] == 1 and y_pred[i] == 1)
    fp = sum(1 for i in range(n) if y_true[i] == 0 and y_pred[i] == 1)
    fn = sum(1 for i in range(n) if y_true[i] == 1 and y_pred[i] == 0)
    tn = sum(1 for i in range(n) if y_true[i] == 0 and y_pred[i] == 0)
    
    accuracy = (tp + tn) / n if n > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # AUC-ROC approximation
    pos_probs = [y_prob[i] for i in range(n) if y_true[i] == 1]
    neg_probs = [y_prob[i] for i in range(n) if y_true[i] == 0]
    auc = 0
    if pos_probs and neg_probs:
        concordant = sum(1 for p in pos_probs for n_p in neg_probs if p > n_p)
        auc = concordant / (len(pos_probs) * len(neg_probs))
    
    return {
        'accuracy': round(accuracy, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
        'auc_roc': round(auc, 4),
        'confusion': {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn}
    }

def train_models(features_path, models_dir):
    """Train all ML models."""
    print("=" * 60)
    print("EventFlow AI — Model Training")
    print("=" * 60)
    
    # Load data
    features = load_features(features_path)
    X, y_severity, y_closure, y_duration, feature_cols = prepare_training_data(features)
    
    os.makedirs(models_dir, exist_ok=True)
    
    results = {}
    
    # ========== Model 1: Severity Score Prediction ==========
    print("\n" + "="*50)
    print("Training: Severity Score Predictor (Regression)")
    print("="*50)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_severity, test_ratio=0.2)
    
    severity_model = GradientBoostingModel(
        n_estimators=200,
        learning_rate=0.05,
        task='regression'
    )
    severity_model.fit(X_train, y_train, feature_names=feature_cols)
    
    y_pred = severity_model.predict(X_test)
    severity_metrics = evaluate_regression(y_test, y_pred)
    results['severity'] = severity_metrics
    
    print(f"\nSeverity Model Results:")
    print(f"  MAE: {severity_metrics['mae']}")
    print(f"  RMSE: {severity_metrics['rmse']}")
    print(f"  R²: {severity_metrics['r2']}")
    
    importance = severity_model.feature_importance()
    print(f"\nTop Features:")
    for k, v in list(importance.items())[:10]:
        print(f"  {k}: {v}")
    
    # Save model
    with open(os.path.join(models_dir, 'severity_model.pkl'), 'wb') as f:
        pickle.dump(severity_model, f)
    
    # ========== Model 2: Road Closure Classification ==========
    print("\n" + "="*50)
    print("Training: Road Closure Classifier")
    print("="*50)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_closure, test_ratio=0.2)
    
    closure_model = GradientBoostingModel(
        n_estimators=200,
        learning_rate=0.05,
        task='classification'
    )
    closure_model.fit(X_train, y_train, feature_names=feature_cols)
    
    y_prob = closure_model.predict(X_test)
    closure_metrics = evaluate_classification(y_test, y_prob)
    results['closure'] = closure_metrics
    
    print(f"\nClosure Model Results:")
    print(f"  Accuracy: {closure_metrics['accuracy']}")
    print(f"  Precision: {closure_metrics['precision']}")
    print(f"  Recall: {closure_metrics['recall']}")
    print(f"  F1: {closure_metrics['f1']}")
    print(f"  AUC-ROC: {closure_metrics['auc_roc']}")
    
    with open(os.path.join(models_dir, 'closure_model.pkl'), 'wb') as f:
        pickle.dump(closure_model, f)
    
    # ========== Model 3: Duration Estimator ==========
    print("\n" + "="*50)
    print("Training: Duration Estimator (Regression)")
    print("="*50)
    
    # Filter to records with resolution time
    X_dur = [X[i] for i in range(len(X)) if y_duration[i] is not None]
    y_dur = [y_duration[i] for i in range(len(y_duration)) if y_duration[i] is not None]
    
    # Cap duration at 48h for training stability
    y_dur_capped = [min(d, 48.0) for d in y_dur]
    
    print(f"  Training on {len(X_dur)} records with known duration")
    
    X_train, X_test, y_train, y_test = train_test_split(X_dur, y_dur_capped, test_ratio=0.2)
    
    duration_model = GradientBoostingModel(
        n_estimators=150,
        learning_rate=0.05,
        task='regression'
    )
    duration_model.fit(X_train, y_train, feature_names=feature_cols)
    
    y_pred = duration_model.predict(X_test)
    duration_metrics = evaluate_regression(y_test, y_pred)
    results['duration'] = duration_metrics
    
    print(f"\nDuration Model Results:")
    print(f"  MAE: {duration_metrics['mae']}")
    print(f"  RMSE: {duration_metrics['rmse']}")
    print(f"  R²: {duration_metrics['r2']}")
    
    with open(os.path.join(models_dir, 'duration_model.pkl'), 'wb') as f:
        pickle.dump(duration_model, f)
    
    # Save feature column names and metadata
    model_meta = {
        'feature_columns': feature_cols,
        'n_features': len(feature_cols),
        'cascade_feature_included': True,
        'severity_metrics': results['severity'],
        'closure_metrics': results['closure'],
        'duration_metrics': results['duration'],
        'training_samples': len(X),
        'model_version': 'v2.0.0',  # bumped: cascade feature added
    }
    
    with open(os.path.join(models_dir, 'model_metadata.json'), 'w') as f:
        json.dump(model_meta, f, indent=2)
    
    print("\n" + "="*50)
    print("All models trained and saved!")
    print("="*50)
    
    return results

if __name__ == '__main__':
    features_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'features.csv')
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    train_models(features_path, models_dir)
