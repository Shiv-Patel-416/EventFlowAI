"""ML Model Classes — needed for pickle deserialization.
Must be importable for pickle.load to work.
"""

import math
import random
from collections import defaultdict


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
        feature_indices = random.sample(range(n_features), min(max(n_features // 2, 1), n_features))
        
        for feat_idx in feature_indices:
            values = [X[i][feat_idx] for i in range(n_samples)]
            sorted_vals = sorted(set(values))
            if len(sorted_vals) <= 1:
                continue
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
                probs = [1.0 / (1.0 + math.exp(-max(min(p, 10), -10))) for p in predictions]
                residuals = [y[j] - probs[j] for j in range(n_samples)]
            else:
                residuals = [y[j] - predictions[j] for j in range(n_samples)]
            
            stump = SimpleDecisionStump()
            stump.fit(X, residuals)
            self.trees.append(stump)
            
            for j in range(n_samples):
                predictions[j] += self.learning_rate * stump.predict_one(X[j])
    
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
