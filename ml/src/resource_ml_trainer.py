"""
EventFlow AI — ML Resource Estimator Training (Step 4B)
Trains 5 ML models to predict optimal resource allocation.
Algorithms: GradientBoosting, RandomForest, Ridge, kNN, Stacking Ensemble
Outputs: 4 trained models (police, barricades, checkpoints, emergency)
         + full metrics report + conditional forecasting table
"""
import csv, json, math, os, random, pickle
from collections import defaultdict

# ── Re-use the GradientBoostingModel from model_classes ──────────────────────
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)
from app.ml.model_classes import GradientBoostingModel, SimpleDecisionStump

# ─────────────────────────────────────────────────────────────────────────────
# Historical resource deployment table derived from Bengaluru incident data.
# When labelled deployment data is absent we SYNTHESISE ground-truth using
# the known rule-based baseline + Gaussian noise + cause-specific adjustments.
# This is standard practice for "no-label" datasets.
# ─────────────────────────────────────────────────────────────────────────────
CAUSE_RESOURCE_PROFILES = {
    "vehicle_breakdown": {"police": (1,3),  "barricades": (0,2),  "checkpoints": (0,1), "emergency": (0,1)},
    "pot_holes":         {"police": (1,3),  "barricades": (0,2),  "checkpoints": (0,1), "emergency": (0,1)},
    "road_conditions":   {"police": (2,4),  "barricades": (1,3),  "checkpoints": (0,1), "emergency": (0,1)},
    "water_logging":     {"police": (2,5),  "barricades": (2,5),  "checkpoints": (0,2), "emergency": (0,2)},
    "debris":            {"police": (2,4),  "barricades": (1,3),  "checkpoints": (0,1), "emergency": (0,1)},
    "tree_fall":         {"police": (3,6),  "barricades": (3,6),  "checkpoints": (1,2), "emergency": (1,2)},
    "fog_low_visibility":{"police": (2,4),  "barricades": (1,3),  "checkpoints": (0,2), "emergency": (0,1)},
    "congestion":        {"police": (4,8),  "barricades": (2,5),  "checkpoints": (1,3), "emergency": (0,1)},
    "accident":          {"police": (4,8),  "barricades": (3,6),  "checkpoints": (1,2), "emergency": (2,4)},
    "construction":      {"police": (5,10), "barricades": (5,10), "checkpoints": (2,4), "emergency": (0,2)},
    "public_event":      {"police": (8,16), "barricades": (6,12), "checkpoints": (2,5), "emergency": (1,3)},
    "procession":        {"police": (7,14), "barricades": (5,10), "checkpoints": (2,4), "emergency": (1,2)},
    "vip_movement":      {"police": (15,25),"barricades": (10,18),"checkpoints": (4,8), "emergency": (2,4)},
    "protest":           {"police": (10,20),"barricades": (8,15), "checkpoints": (3,6), "emergency": (2,4)},
    "others":            {"police": (2,5),  "barricades": (1,4),  "checkpoints": (0,2), "emergency": (0,1)},
}

CAUSE_SEVERITY = {
    "vehicle_breakdown": 2.0, "pot_holes": 2.5, "road_conditions": 3.0,
    "water_logging": 4.0, "others": 2.5, "tree_fall": 5.0, "congestion": 4.5,
    "accident": 6.0, "construction": 5.5, "debris": 3.0,
    "fog_low_visibility": 3.5, "public_event": 7.5, "procession": 7.0,
    "vip_movement": 8.5, "protest": 8.0,
}
CAUSE_LABELS = sorted(CAUSE_SEVERITY.keys())
COST_POLICE, COST_BARRICADE, COST_CHECKPOINT, COST_EMERGENCY = 500, 200, 1500, 3000

# ─────────────────────────────────────────────────────────────────────────────
# Algorithm 2 – Random Forest (bagged gradient boosters)
# ─────────────────────────────────────────────────────────────────────────────
class RandomForestRegressor:
    def __init__(self, n_trees=20, n_estimators=60, learning_rate=0.1, subsample=0.8, seed=42):
        self.n_trees = n_trees
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.seed = seed
        self.trees = []
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        self.feature_names = feature_names or []
        random.seed(self.seed)
        n = len(X)
        for t in range(self.n_trees):
            k = max(1, int(n * self.subsample))
            idx = random.choices(range(n), k=k)
            Xs = [X[i] for i in idx]
            ys = [y[i] for i in idx]
            model = GradientBoostingModel(n_estimators=self.n_estimators,
                                          learning_rate=self.learning_rate, task='regression')
            model.fit(Xs, ys, feature_names=feature_names)
            self.trees.append(model)

    def predict_one(self, x):
        return sum(t.predict_one(x) for t in self.trees) / max(len(self.trees), 1)

    def predict(self, X):
        return [self.predict_one(x) for x in X]


# ─────────────────────────────────────────────────────────────────────────────
# Algorithm 3 – Ridge Regression (closed-form, no external lib)
# ─────────────────────────────────────────────────────────────────────────────
class RidgeRegression:
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.weights = []
        self.bias = 0.0
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        self.feature_names = feature_names or []
        n, p = len(X), len(X[0])
        # Standardise
        means = [sum(X[i][j] for i in range(n))/n for j in range(p)]
        stds  = [max((sum((X[i][j]-means[j])**2 for i in range(n))/n)**0.5, 1e-8) for j in range(p)]
        Xs = [[(X[i][j]-means[j])/stds[j] for j in range(p)] for i in range(n)]
        self._means, self._stds = means, stds
        # Gradient descent
        w = [0.0]*p; b = 0.0; lr = 0.01
        for _ in range(500):
            preds = [sum(w[j]*Xs[i][j] for j in range(p))+b for i in range(n)]
            dw = [(2/n)*sum((preds[i]-y[i])*Xs[i][j] for i in range(n)) + 2*self.alpha*w[j] for j in range(p)]
            db = (2/n)*sum(preds[i]-y[i] for i in range(n))
            w = [w[j]-lr*dw[j] for j in range(p)]
            b -= lr*db
        self.weights, self.bias = w, b

    def predict_one(self, x):
        p = len(x)
        xs = [(x[j]-self._means[j])/self._stds[j] for j in range(p)]
        return sum(self.weights[j]*xs[j] for j in range(p)) + self.bias

    def predict(self, X):
        return [self.predict_one(x) for x in X]


# ─────────────────────────────────────────────────────────────────────────────
# Algorithm 4 – k-Nearest Neighbours Regressor
# ─────────────────────────────────────────────────────────────────────────────
class KNNRegressor:
    def __init__(self, k=7):
        self.k = k
        self.X_train = []
        self.y_train = []
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        self.feature_names = feature_names or []
        self.X_train = X
        self.y_train = y

    def _dist(self, a, b):
        return sum((a[i]-b[i])**2 for i in range(len(a)))**0.5

    def predict_one(self, x):
        dists = sorted(range(len(self.X_train)), key=lambda i: self._dist(x, self.X_train[i]))
        neighbours = dists[:self.k]
        return sum(self.y_train[i] for i in neighbours) / max(len(neighbours), 1)

    def predict(self, X):
        return [self.predict_one(x) for x in X]


# ─────────────────────────────────────────────────────────────────────────────
# Algorithm 5 – Stacking Ensemble (meta-learner on top of 4 models)
# ─────────────────────────────────────────────────────────────────────────────
class StackingEnsemble:
    def __init__(self, base_models, meta_alpha=0.5):
        self.base_models = base_models  # list of fitted model objects
        self.meta = RidgeRegression(alpha=meta_alpha)
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        self.feature_names = feature_names or []
        # Build meta-features from base model predictions
        meta_X = [[m.predict_one(x) for m in self.base_models] for x in X]
        self.meta.fit(meta_X, y, feature_names=[f'base_{i}' for i in range(len(self.base_models))])

    def predict_one(self, x):
        meta_x = [m.predict_one(x) for m in self.base_models]
        return self.meta.predict_one(meta_x)

    def predict(self, X):
        return [self.predict_one(x) for x in X]


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────
def metrics(y_true, y_pred):
    n = len(y_true)
    mae  = sum(abs(y_true[i]-y_pred[i]) for i in range(n))/n
    mse  = sum((y_true[i]-y_pred[i])**2 for i in range(n))/n
    rmse = mse**0.5
    mean = sum(y_true)/n
    ss_tot = sum((y_true[i]-mean)**2 for i in range(n))
    ss_res = sum((y_true[i]-y_pred[i])**2 for i in range(n))
    r2   = 1-(ss_res/ss_tot) if ss_tot>0 else 0.0
    within1 = sum(1 for i in range(n) if abs(y_true[i]-y_pred[i])<=1)/n
    within2 = sum(1 for i in range(n) if abs(y_true[i]-y_pred[i])<=2)/n
    efficiency = 1.0 - sum(abs(y_pred[i]-y_true[i]) for i in range(n))/sum(max(y_true[i],1) for i in range(n))
    return {"mae":round(mae,4),"rmse":round(rmse,4),"r2":round(r2,4),
            "within_1_unit":round(within1,4),"within_2_units":round(within2,4),
            "resource_efficiency":round(efficiency,4)}


def split(X, y, ratio=0.2, seed=42):
    random.seed(seed)
    idx = list(range(len(X))); random.shuffle(idx)
    s = int(len(X)*(1-ratio))
    return [X[i] for i in idx[:s]], [X[i] for i in idx[s:]], [y[i] for i in idx[:s]], [y[i] for i in idx[s:]]


# ─────────────────────────────────────────────────────────────────────────────
# Feature builder (same 28 features as main pipeline + resource_count)
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    'hour_ist','hour_sin','hour_cos','day_of_week','dow_sin','dow_cos',
    'month','time_slot','is_peak_hour','is_weekend','is_holiday',
    'latitude','longitude','distance_to_center_km',
    'is_main_corridor','corridor_event_freq','zone_event_freq','junction_event_freq',
    'event_cause_encoded','cause_base_severity','priority_encoded','is_planned',
    'has_description','description_length',
    'hist_closure_rate_cause','hist_closure_rate_corridor','avg_resolution_time_cause',
    'cascade_probability',
    'severity_score','requires_road_closure',
]

CITY_CENTER = (12.9871, 77.5960)


def _haversine(lat1, lon1, lat2, lon2):
    R=6371.0; dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R*2*math.asin(max(0,a)**0.5)


def load_features(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader: rows.append(r)
    print(f"Loaded {len(rows)} feature records")
    return rows


def synthesise_labels(rows, seed=0):
    """
    Generate synthetic resource ground-truth from historical range profiles
    + severity-driven scaling + random noise.  Simulates what trained
    dispatchers would actually deploy.
    """
    random.seed(seed)
    labelled = []
    for r in rows:
        cause = r.get('event_cause_name', 'others').lower().replace(' ','_')
        profile = CAUSE_RESOURCE_PROFILES.get(cause, CAUSE_RESOURCE_PROFILES['others'])
        sev   = float(r.get('severity_score', 5.0))
        scale = max(0.5, sev/5.0)
        is_peak = int(r.get('is_peak_hour', 0))
        is_high = 1 if r.get('priority_encoded','0')=='1' else 0
        closure = 1 if r.get('requires_road_closure','0')=='1' else 0

        def sample(key):
            lo, hi = profile[key]
            base = random.uniform(lo*scale, hi*scale)
            base += is_peak*0.5 + is_high*0.3 + closure*0.5
            return max(0, round(base + random.gauss(0, 0.3)))

        pol = sample('police')
        bar = sample('barricades')
        chk = sample('checkpoints')
        eme = sample('emergency')
        # Efficiency label: was event resolved in <=60 min?
        res_h = r.get('resolution_hours','')
        fast  = 1 if (res_h and res_h not in ('','None') and float(res_h)*60<=60) else 0
        labelled.append({**r, 'label_police':pol,'label_barricades':bar,
                         'label_checkpoints':chk,'label_emergency':eme,'resolved_fast':fast})
    return labelled


def build_X(rows):
    X = []
    for r in rows:
        row = []
        for c in FEATURE_COLS:
            try: row.append(float(r.get(c, 0) or 0))
            except: row.append(0.0)
        X.append(row)
    return X


# ─────────────────────────────────────────────────────────────────────────────
# Conditional Forecasting Table
# ─────────────────────────────────────────────────────────────────────────────
def conditional_forecast(X_test, y_dur_true, duration_model, base_police_preds, step=2, max_p=20):
    """
    For each test sample, compute: given police=k, what is predicted duration?
    Returns a summary table averaged over the test set.
    """
    table = []
    for k in range(0, max_p+1, step):
        # Inject police count as a feature proxy via severity scaling
        adjusted_X = []
        for x in X_test:
            x2 = list(x)
            # Feature index 28 = severity_score; scale it by relative police ratio
            ratio = k / max(base_police_preds[0], 1)  # relative to avg recommended
            x2[28] = x[28] * max(0.5, 1.0 - (ratio - 1.0) * 0.1)
            adjusted_X.append(x2)
        preds = duration_model.predict(adjusted_X)
        avg_dur = sum(preds)/max(len(preds),1)
        # Approx R² vs ground truth
        if y_dur_true:
            ss_res = sum((y_dur_true[i]-preds[i])**2 for i in range(len(preds)))
            mean   = sum(y_dur_true)/len(y_dur_true)
            ss_tot = sum((v-mean)**2 for v in y_dur_true)
            r2 = round(1-(ss_res/ss_tot) if ss_tot>0 else 0, 3)
        else:
            r2 = 0.0
        table.append({"police_deployed":k,"predicted_duration_hours":round(avg_dur,2),"r2":r2})
    return table


# ─────────────────────────────────────────────────────────────────────────────
# Train all resource models
# ─────────────────────────────────────────────────────────────────────────────
def train_resource_models(features_path, models_dir, duration_model_path=None):
    print("="*60)
    print("EventFlow AI — ML Resource Estimator Training (Step 4B)")
    print("="*60)

    rows   = load_features(features_path)
    rows   = synthesise_labels(rows)
    X_all  = build_X(rows)

    targets = {
        'police':      [float(r['label_police'])     for r in rows],
        'barricades':  [float(r['label_barricades'])  for r in rows],
        'checkpoints': [float(r['label_checkpoints']) for r in rows],
        'emergency':   [float(r['label_emergency'])   for r in rows],
    }

    os.makedirs(models_dir, exist_ok=True)
    all_metrics = {}

    for target, y_all in targets.items():
        print(f"\n{'='*50}\nTraining: {target.upper()} predictor\n{'='*50}")
        Xtr,Xte,ytr,yte = split(X_all, y_all)

        # ── Model 1: Gradient Boosting ────────────────────────────
        gb = GradientBoostingModel(n_estimators=300, learning_rate=0.04, task='regression')
        gb.fit(Xtr, ytr, feature_names=FEATURE_COLS)
        gb_pred = gb.predict(Xte)

        # ── Model 2: Random Forest ────────────────────────────────
        rf = RandomForestRegressor(n_trees=15, n_estimators=80, learning_rate=0.08, subsample=0.8)
        rf.fit(Xtr, ytr, feature_names=FEATURE_COLS)
        rf_pred = rf.predict(Xte)

        # ── Model 3: Ridge Regression ─────────────────────────────
        rr = RidgeRegression(alpha=0.5)
        rr.fit(Xtr, ytr, feature_names=FEATURE_COLS)
        rr_pred = rr.predict(Xte)

        # ── Model 4: kNN ──────────────────────────────────────────
        knn = KNNRegressor(k=7)
        knn.fit(Xtr, ytr, feature_names=FEATURE_COLS)
        knn_pred = knn.predict(Xte)

        # ── Model 5: Stacking Ensemble ────────────────────────────
        stack = StackingEnsemble([gb, rf, rr, knn], meta_alpha=0.5)
        stack.fit(Xtr, ytr, feature_names=FEATURE_COLS)
        stack_pred = stack.predict(Xte)

        # ── Pick best model by R² ─────────────────────────────────
        candidates = {
            'gradient_boosting': (gb,      gb_pred),
            'random_forest':     (rf,      rf_pred),
            'ridge_regression':  (rr,      rr_pred),
            'knn':               (knn,     knn_pred),
            'stacking_ensemble': (stack,   stack_pred),
        }
        model_metrics = {}
        for name,(model,pred) in candidates.items():
            m = metrics(yte, pred)
            model_metrics[name] = m
            print(f"  [{name:20s}] R²={m['r2']:.4f} MAE={m['mae']:.4f} "
                  f"Efficiency={m['resource_efficiency']:.4f} ±1unit={m['within_1_unit']:.4f}")

        best_name = max(model_metrics, key=lambda k: model_metrics[k]['r2'])
        best_model, best_pred = candidates[best_name]
        print(f"\n  ✅ Best: {best_name} (R²={model_metrics[best_name]['r2']:.4f})")

        all_metrics[target] = {
            'all_models': model_metrics,
            'best_model': best_name,
            'best_metrics': model_metrics[best_name],
        }

        # Save best model
        with open(os.path.join(models_dir, f'resource_{target}_model.pkl'), 'wb') as f:
            pickle.dump(best_model, f)

    # ── Conditional Forecasting Table ────────────────────────────
    print("\n" + "="*50)
    print("Conditional Forecasting: Police Count → Duration")
    print("="*50)
    cond_table = []
    dur_model_loaded = False
    if duration_model_path and os.path.exists(duration_model_path):
        with open(duration_model_path,'rb') as f:
            dur_model = pickle.load(f)
        dur_model_loaded = True
        y_dur = []
        for r in rows:
            v = r.get('resolution_hours','')
            if v and v not in ('','None'):
                y_dur.append(float(v))
        Xte_sample = X_all[:200]
        y_dur_sample = y_dur[:200] if len(y_dur)>=200 else y_dur
        police_preds = [float(r.get('label_police',5)) for r in rows[:200]]
        avg_police = sum(police_preds)/max(len(police_preds),1)
        cond_table = conditional_forecast(Xte_sample, y_dur_sample, dur_model, [avg_police])
        print(f"{'Police':>8} | {'Est. Duration (h)':>18} | {'R²':>6}")
        print("-"*38)
        for row in cond_table:
            print(f"  {row['police_deployed']:>5}  | {row['predicted_duration_hours']:>17.2f}h | {row['r2']:>6.3f}")

    # ── Resource Efficiency Score ─────────────────────────────────
    efficiency_scores = {t: all_metrics[t]['best_metrics']['resource_efficiency'] for t in targets}
    overall_efficiency = sum(efficiency_scores.values())/len(efficiency_scores)
    print(f"\nOverall Resource Efficiency Score: {overall_efficiency:.4f}")

    # ── Save metadata ─────────────────────────────────────────────
    meta = {
        'feature_columns': FEATURE_COLS,
        'n_features': len(FEATURE_COLS),
        'target_resources': list(targets.keys()),
        'model_metrics': all_metrics,
        'conditional_forecast_table': cond_table,
        'overall_resource_efficiency': round(overall_efficiency, 4),
        'model_version': 'v2.0.0-resource-ml',
        'algorithms_evaluated': ['gradient_boosting','random_forest','ridge_regression','knn','stacking_ensemble'],
    }
    with open(os.path.join(models_dir,'resource_model_metadata.json'),'w') as f:
        json.dump(meta, f, indent=2)
    print(f"\nAll resource models saved to {models_dir}")
    return meta


if __name__ == '__main__':
    base        = os.path.dirname(__file__)
    feat_path   = os.path.join(base, '..', 'data', 'processed', 'features.csv')
    models_dir  = os.path.join(base, '..', 'models')
    dur_path    = os.path.join(models_dir, 'duration_model.pkl')
    train_resource_models(feat_path, models_dir, duration_model_path=dur_path)
