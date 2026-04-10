#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier
from tabpfn import TabPFNClassifier
from sklearn.model_selection import KFold
import warnings
import os

warnings.filterwarnings('ignore')
os.environ['TABPFN_ALLOW_CPU_LARGE_DATASET'] = '1'

data_dir = "/Users/weijiaresearchteam/Desktop/Fibrosis"

df_train = pd.read_csv(f"{data_dir}/training.txt", sep="\t", encoding="utf-8", low_memory=False)
df_val = pd.read_csv(f"{data_dir}/HBV_validation.txt", sep="\t", encoding="utf-8", low_memory=False)

feature_names =['Age', 'PLT', 'ALT', 'AST', 'Tyrosine', 'Taurocholic acid']

def bootstrap_ci_metric(y_true, y_pred_or_probs, metric_func, n_iterations=1000, confidence=0.95):
    np.random.seed(42)
    n = len(y_true)
    bootstrapped_metrics =[]

    for _ in range(n_iterations):
        indices = np.random.choice(n, n, replace=True)
        if len(np.unique(y_true[indices])) < 2:
            continue
        metric = metric_func(y_true[indices], y_pred_or_probs[indices])
        bootstrapped_metrics.append(metric)

    alpha = (1.0 - confidence) / 2.0
    lower = np.percentile(bootstrapped_metrics, alpha * 100)
    upper = np.percentile(bootstrapped_metrics, (1 - alpha) * 100)

    return lower, upper

def find_optimal_cutoff_youden(y_true, y_probs):
    fpr, tpr, thresholds = roc_curve(y_true, y_probs)
    youden_index = tpr - fpr
    optimal_idx = np.argmax(youden_index)
    optimal_cutoff = thresholds[optimal_idx]
    return optimal_cutoff

def calculate_sensitivity_specificity(y_true, y_probs, cutoff):
    y_pred = (y_probs >= cutoff).astype(int)

    tp = np.sum((y_pred == 1) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

    return sensitivity, specificity

def prepare_task_data(df_train, df_val, task_type):
    df_train_task = df_train[df_train['Group3'].notna()].copy()
    df_val_task = df_val[df_val['Group3'].notna()].copy()

    df_train_task['Group3'] = pd.to_numeric(df_train_task['Group3'], errors='coerce')
    df_val_task['Group3'] = pd.to_numeric(df_val_task['Group3'], errors='coerce')

    df_train_task = df_train_task[df_train_task['Group3'].notna()].copy()
    df_val_task = df_val_task[df_val_task['Group3'].notna()].copy()

    df_train_task['Group3'] = df_train_task['Group3'].astype(int)
    df_val_task['Group3'] = df_val_task['Group3'].astype(int)

    if task_type == 'sig_fibrosis':
        y_train = (df_train_task['Group3'] >= 2).astype(int).values
        y_val = (df_val_task['Group3'] >= 2).astype(int).values

    elif task_type == 'adv_fibrosis':
        y_train = (df_train_task['Group3'] >= 3).astype(int).values
        y_val = (df_val_task['Group3'] >= 3).astype(int).values

    elif task_type == 'cirrhosis':
        y_train = (df_train_task['Group3'] == 4).astype(int).values
        y_val = (df_val_task['Group3'] == 4).astype(int).values

    X_train = df_train_task[feature_names].copy()
    X_val = df_val_task[feature_names].copy()

    valid_mask_train = ~X_train.isna().any(axis=1)
    valid_mask_val = ~X_val.isna().any(axis=1)

    X_train_clean = X_train[valid_mask_train]
    y_train_clean = y_train[valid_mask_train]
    X_val_clean = X_val[valid_mask_val]
    y_val_clean = y_val[valid_mask_val]

    return X_train_clean, y_train_clean, X_val_clean, y_val_clean

def train_model_5fold(model_name, X_train, y_train, X_test):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    y_probs = np.zeros(len(X_test))

    for fold, (train_idx, _) in enumerate(kf.split(X_train), 1):
        if model_name == "TabPFN":
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
        elif model_name == "Gradient Boosting":
            model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        elif model_name == "Random Forest":
            model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        elif model_name == "Categorical Boosting":
            model = CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1, random_state=42, verbose=0)
        elif model_name == "Logistic Regression":
            model = LogisticRegression(max_iter=1000, random_state=42)

        model.fit(X_train.iloc[train_idx], y_train[train_idx])
        y_probs += model.predict_proba(X_test)[:, 1]

    y_probs = y_probs / 5
    return y_probs

tasks = {
    'Significant fibrosis (S≥2) vs. S0-S1': 'sig_fibrosis',
    'Advanced fibrosis (S≥3) vs. S0-S2': 'adv_fibrosis',
    'Cirrhosis (S4) vs. S0-S3': 'cirrhosis'
}

models =["TabPFN", "Gradient Boosting", "Random Forest", "Categorical Boosting", "Logistic Regression"]

all_results = {}

for task_name, task_type in tasks.items():
    X_train, y_train, X_val, y_val = prepare_task_data(df_train, df_val, task_type)

    if len(y_val) < 10 or np.sum(y_val==0) < 2 or np.sum(y_val==1) < 2:
        continue

    task_results = {}

    for model_name in models:
        try:
            y_probs_val = train_model_5fold(model_name, X_train, y_train, X_val)

            auroc = roc_auc_score(y_val, y_probs_val)
            auroc_ci_lower, auroc_ci_upper = bootstrap_ci_metric(
                y_val, y_probs_val, roc_auc_score
            )

            optimal_cutoff = find_optimal_cutoff_youden(y_val, y_probs_val)

            sensitivity, specificity = calculate_sensitivity_specificity(y_val, y_probs_val, optimal_cutoff)

            sens_ci_lower, sens_ci_upper = bootstrap_ci_metric(
                y_val, y_probs_val, 
                lambda yt, yp: calculate_sensitivity_specificity(yt, yp, optimal_cutoff)[0]
            )

            spec_ci_lower, spec_ci_upper = bootstrap_ci_metric(
                y_val, y_probs_val,
                lambda yt, yp: calculate_sensitivity_specificity(yt, yp, optimal_cutoff)[1]
            )

            task_results[model_name] = {
                'auroc': auroc,
                'auroc_ci': (auroc_ci_lower, auroc_ci_upper),
                'cutoff': optimal_cutoff,
                'sensitivity': sensitivity,
                'sensitivity_ci': (sens_ci_lower, sens_ci_upper),
                'specificity': specificity,
                'specificity_ci': (spec_ci_lower, spec_ci_upper)
            }

        except Exception:
            continue

    all_results[task_name] = task_results

summary_data =[]
for task_name in tasks.keys():
    if task_name not in all_results:
        continue
    for model_name in models:
        if model_name not in all_results[task_name]:
            continue
        result = all_results[task_name][model_name]
        summary_data.append({
            'Task': task_name,
            'Model': model_name,
            'AUROC': f"{result['auroc']:.3f}",
            'AUROC 95% CI': f"{result['auroc_ci'][0]:.3f}-{result['auroc_ci'][1]:.3f}",
            'Optimal Cutoff': f"{result['cutoff']:.3f}",
            'Sensitivity': f"{result['sensitivity']:.3f}",
            'Sensitivity 95% CI': f"{result['sensitivity_ci'][0]:.3f}-{result['sensitivity_ci'][1]:.3f}",
            'Specificity': f"{result['specificity']:.3f}",
            'Specificity 95% CI': f"{result['specificity_ci'][0]:.3f}-{result['specificity_ci'][1]:.3f}"
        })

df_summary = pd.DataFrame(summary_data)

output_file = f"{data_dir}/HBV_Validation_Performance_Metrics.csv"
df_summary.to_csv(output_file, index=False)

