#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, GridSearchCV
from catboost import CatBoostClassifier
from tabpfn import TabPFNClassifier
import warnings
import os
import json
from datetime import datetime

warnings.filterwarnings('ignore')
os.environ['TABPFN_ALLOW_CPU_LARGE_DATASET'] = '1'

data_dir = "/Users/weijiaresearchteam/Desktop/Fibrosis"

df_train = pd.read_csv(f"{data_dir}/training.txt", sep="\t", encoding="utf-8", low_memory=False)
df_val1 = pd.read_csv(f"{data_dir}/MASLD_validation_149.txt", sep="\t", encoding="utf-8", low_memory=False)
df_val2 = pd.read_csv(f"{data_dir}/Tyr_TCA_Merged_155.txt", sep="\t", encoding="utf-8", low_memory=False)
df_val3 = pd.read_csv(f"{data_dir}/HBV_validation.txt", sep="\t", encoding="utf-8", low_memory=False)

feature_names = ['Age', 'PLT', 'ALT', 'AST', 'Tyrosine', 'Taurocholic acid']

best_params_dict = {}

param_grids = {
    "Gradient Boosting": {
        'n_estimators': [50, 100, 200],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [2, 3, 5],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    },
    "Random Forest": {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 'log2']
    },
    "Categorical Boosting": {
        'iterations': [50, 100, 200],
        'depth': [4, 6, 8],
        'learning_rate': [0.01, 0.05, 0.1],
        'l2_leaf_reg': [1, 3, 5]
    },
    "Logistic Regression": {
        'C': [0.001, 0.01, 0.1, 1, 10],
        'penalty': ['l2'],
        'solver': ['lbfgs', 'liblinear']
    }
}

def bootstrap_ci_auroc(y_true, y_probs, n_iterations=1000, confidence=0.95):
    np.random.seed(42)
    n = len(y_true)
    bootstrapped_aurocs = []

    for _ in range(n_iterations):
        indices = np.random.choice(n, n, replace=True)
        if len(np.unique(y_true[indices])) < 2:
            continue
        auroc = roc_auc_score(y_true[indices], y_probs[indices])
        bootstrapped_aurocs.append(auroc)

    alpha = (1.0 - confidence) / 2.0
    lower = np.percentile(bootstrapped_aurocs, alpha * 100)
    upper = np.percentile(bootstrapped_aurocs, (1 - alpha) * 100)

    return lower, upper

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

def train_model_gridsearch_5fold(model_name, X_train, y_train, X_test, param_grid):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    y_probs = np.zeros(len(X_test))

    if model_name == "Gradient Boosting":
        base_model = GradientBoostingClassifier(random_state=42)
    elif model_name == "Random Forest":
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
    elif model_name == "Categorical Boosting":
        base_model = CatBoostClassifier(random_state=42, verbose=0)
    elif model_name == "Logistic Regression":
        base_model = LogisticRegression(max_iter=1000, random_state=42)

    train_idx, _ = next(iter(kf.split(X_train)))
    grid_search = GridSearchCV(base_model, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=0)
    grid_search.fit(X_train.iloc[train_idx], y_train[train_idx])

    best_params = grid_search.best_params_
    best_score = grid_search.best_score_

    for fold, (fold_train_idx, _) in enumerate(kf.split(X_train), 1):
        if model_name == "Gradient Boosting":
            model = GradientBoostingClassifier(**best_params, random_state=42)
        elif model_name == "Random Forest":
            model = RandomForestClassifier(**best_params, random_state=42, n_jobs=-1)
        elif model_name == "Categorical Boosting":
            model = CatBoostClassifier(**best_params, random_state=42, verbose=0)
        elif model_name == "Logistic Regression":
            model = LogisticRegression(**best_params, max_iter=1000, random_state=42)

        model.fit(X_train.iloc[fold_train_idx], y_train[fold_train_idx])
        y_probs += model.predict_proba(X_test)[:, 1]

    y_probs = y_probs / 5

    return y_probs, best_params, best_score

def train_model_tabpfn_5fold(model_name, X_train, y_train, X_test):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    y_probs = np.zeros(len(X_test))

    for fold, (train_idx, _) in enumerate(kf.split(X_train), 1):
        model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
        model.fit(X_train.iloc[train_idx], y_train[train_idx])
        y_probs += model.predict_proba(X_test)[:, 1]

    y_probs = y_probs / 5
    return y_probs, None, None

tasks = {
    'Significant fibrosis (S≥2) vs. S0-S1': 'sig_fibrosis',
    'Advanced fibrosis (S≥3) vs. S0-S2': 'adv_fibrosis',
    'Cirrhosis (S4) vs. S0-S3': 'cirrhosis'
}

models = ["TabPFN", "Gradient Boosting", "Random Forest", "Categorical Boosting", "Logistic Regression"]

validation_cohorts = {
    'Validation Cohort 1 (MASLD)': df_val1,
    'Validation Cohort 2 (Tyr_TCA)': df_val2,
    'Validation Cohort 3 (HBV)': df_val3
}

all_results = {}

for task_name, task_type in tasks.items():
    task_results = {}

    for cohort_name, df_val in validation_cohorts.items():
        X_train, y_train, X_val, y_val = prepare_task_data(df_train, df_val, task_type)

        if len(y_val) < 10 or np.sum(y_val==0) < 2 or np.sum(y_val==1) < 2:
            continue

        cohort_results = {}

        for model_name in models:
            try:
                if model_name == "TabPFN":
                    y_probs_val, best_params, best_score = train_model_tabpfn_5fold(model_name, X_train, y_train, X_val)
                else:
                    y_probs_val, best_params, best_score = train_model_gridsearch_5fold(
                        model_name, X_train, y_train, X_val, param_grids[model_name]
                    )

                auroc = roc_auc_score(y_val, y_probs_val)
                ci_lower, ci_upper = bootstrap_ci_auroc(y_val, y_probs_val)

                cohort_results[model_name] = {
                    'auroc': auroc,
                    'ci': (ci_lower, ci_upper),
                    'best_params': best_params,
                    'best_cv_score': best_score
                }

                if model_name not in best_params_dict and best_params is not None:
                    best_params_dict[model_name] = best_params

            except Exception as e:
                continue

        task_results[cohort_name] = cohort_results

    all_results[task_name] = task_results

val1_data = []
for task_name in tasks.keys():
    if task_name not in all_results:
        continue
    if 'Validation Cohort 1 (MASLD)' not in all_results[task_name]:
        continue
    for model_name in models:
        if model_name not in all_results[task_name]['Validation Cohort 1 (MASLD)']:
            continue
        result = all_results[task_name]['Validation Cohort 1 (MASLD)'][model_name]
        val1_data.append({
            'Task': task_name,
            'Model': model_name,
            'AUROC': f"{result['auroc']:.3f}",
            '95% CI': f"{result['ci'][0]:.3f}-{result['ci'][1]:.3f}"
        })

df_val1_results = pd.DataFrame(val1_data)
df_val1_results.to_csv(f"{data_dir}/Table_ValidationCohort1_MASLD_GridSearch_AUROC.csv", index=False)

val2_data = []
for task_name in tasks.keys():
    if task_name not in all_results:
        continue
    if 'Validation Cohort 2 (Tyr_TCA)' not in all_results[task_name]:
        continue
    for model_name in models:
        if model_name not in all_results[task_name]['Validation Cohort 2 (Tyr_TCA)']:
            continue
        result = all_results[task_name]['Validation Cohort 2 (Tyr_TCA)'][model_name]
        val2_data.append({
            'Task': task_name,
            'Model': model_name,
            'AUROC': f"{result['auroc']:.3f}",
            '95% CI': f"{result['ci'][0]:.3f}-{result['ci'][1]:.3f}"
        })

df_val2_results = pd.DataFrame(val2_data)
df_val2_results.to_csv(f"{data_dir}/Table_ValidationCohort2_TyrTCA_GridSearch_AUROC.csv", index=False)

val3_data = []
for task_name in tasks.keys():
    if task_name not in all_results:
        continue
    if 'Validation Cohort 3 (HBV)' not in all_results[task_name]:
        continue
    for model_name in models:
        if model_name not in all_results[task_name]['Validation Cohort 3 (HBV)']:
            continue
        result = all_results[task_name]['Validation Cohort 3 (HBV)'][model_name]
        val3_data.append({
            'Task': task_name,
            'Model': model_name,
            'AUROC': f"{result['auroc']:.3f}",
            '95% CI': f"{result['ci'][0]:.3f}-{result['ci'][1]:.3f}"
        })

df_val3_results = pd.DataFrame(val3_data)
df_val3_results.to_csv(f"{data_dir}/Table_ValidationCohort3_HBV_GridSearch_AUROC.csv", index=False)

config_info = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "environment": {
        "python_version": "3.x",
        "main_libraries": {
            "scikit-learn": "latest",
            "pandas": "latest",
            "numpy": "latest",
            "catboost": "latest",
            "tabpfn": "latest"
        },
        "hardware": "CPU-based (TabPFN explicitly set to CPU)",
        "gridsearch_cv_folds": 5,
        "ensemble_folds": 5
    },
    "models": {}
}

for model_name in ["Gradient Boosting", "Random Forest", "Categorical Boosting", "Logistic Regression"]:
    if model_name in best_params_dict:
        params = best_params_dict[model_name]
        config_info["models"][model_name] = {
            "hyperparameters": params,
            "search_space": param_grids[model_name],
            "optimization_method": "GridSearchCV (5-fold CV)",
            "note": "Parameters selected from grid search on first task"
        }

config_info["models"]["TabPFN"] = {
    "parameters": {
        "device": "cpu",
        "random_state": 42,
        "ignore_pretraining_limits": True
    },
    "note": "TabPFN not optimized via GridSearchCV"
}

config_file = f"{data_dir}/Model_GridSearchCV_Configuration_Report.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config_info, f, indent=2, ensure_ascii=False)

