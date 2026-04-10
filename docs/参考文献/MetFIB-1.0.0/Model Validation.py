#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from tabpfn import TabPFNClassifier
import matplotlib.pyplot as plt
import warnings
import os

warnings.filterwarnings('ignore')
os.environ['TABPFN_ALLOW_CPU_LARGE_DATASET'] = '1'

def bootstrap_ci(y_true, y_scores, metric_func, n_bootstraps=1000, confidence_level=0.95):
    np.random.seed(42)
    bootstrapped_scores =[]

    n_samples = len(y_true)
    for i in range(n_bootstraps):
        indices = np.random.randint(0, n_samples, n_samples)
        if len(np.unique(y_true[indices])) < 2:
            continue

        score = metric_func(y_true[indices], y_scores[indices])
        bootstrapped_scores.append(score)

    sorted_scores = np.array(bootstrapped_scores)
    alpha = 1.0 - confidence_level
    lower = np.percentile(sorted_scores, alpha/2 * 100)
    upper = np.percentile(sorted_scores, (1 - alpha/2) * 100)

    return lower, upper

def compute_roc_ci(y_true, y_scores, n_bootstraps=1000):
    np.random.seed(42)

    base_fpr = np.linspace(0, 1, 100)

    tprs =[]
    n_samples = len(y_true)

    for i in range(n_bootstraps):
        indices = np.random.randint(0, n_samples, n_samples)
        if len(np.unique(y_true[indices])) < 2:
            continue

        fpr, tpr, _ = roc_curve(y_true[indices], y_scores[indices])
        tpr_interp = np.interp(base_fpr, fpr, tpr)
        tpr_interp[0] = 0.0
        tprs.append(tpr_interp)

    tprs = np.array(tprs)
    mean_tpr = tprs.mean(axis=0)

    tpr_lower = np.percentile(tprs, 2.5, axis=0)
    tpr_upper = np.percentile(tprs, 97.5, axis=0)

    return base_fpr, mean_tpr, tpr_lower, tpr_upper

def compute_prc_ci(y_true, y_scores, n_bootstraps=1000):
    np.random.seed(42)

    base_recall = np.linspace(0, 1, 100)

    precisions =[]
    n_samples = len(y_true)

    for i in range(n_bootstraps):
        indices = np.random.randint(0, n_samples, n_samples)
        if len(np.unique(y_true[indices])) < 2:
            continue

        precision, recall, _ = precision_recall_curve(y_true[indices], y_scores[indices])
        precision = precision[::-1]
        recall = recall[::-1]
        precision_interp = np.interp(base_recall, recall, precision)
        precisions.append(precision_interp)

    precisions = np.array(precisions)
    mean_precision = precisions.mean(axis=0)

    precision_lower = np.percentile(precisions, 2.5, axis=0)
    precision_upper = np.percentile(precisions, 97.5, axis=0)

    return base_recall, mean_precision, precision_lower, precision_upper

data_dir = "/Users/weijiaresearchteam/Desktop/Fibrosis"
df_train = pd.read_csv(f"{data_dir}/training.txt", sep="\t", encoding="utf-8", low_memory=False)
df_val = pd.read_csv(f"{data_dir}/HBV_validation.txt", sep="\t", encoding="utf-8", low_memory=False)

headers = df_train.columns
met_names = headers[4:-4]

def normalize_group3(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    if value_str in['S0', 'S1', 'S2', 'S3', 'S4']:
        return value_str
    try:
        num = int(float(value_str))
        if 0 <= num <= 4:
            return f'S{num}'
    except:
        pass
    if value_str in['0', '1', '2', '3', '4']:
        return f'S{value_str}'
    return None

df_train['Group3_normalized'] = df_train['Group3'].apply(normalize_group3)
df_val['Group3_normalized'] = df_val['Group3'].apply(normalize_group3)

df_train_control = df_train[df_train['Group1'].str.contains("Control", na=False, case=False)]
df_train_hbv = df_train[df_train['Group1'].str.contains("HBV", na=False, case=False)]
df_train_task1 = pd.concat([df_train_control, df_train_hbv], axis=0, ignore_index=True)

df_train_s0_s1 = df_train[df_train["Group3_normalized"].isin(["S0", "S1"])]
df_train_s2_s3_s4 = df_train[df_train["Group3_normalized"].isin(["S2", "S3", "S4"])]
df_train_task2 = pd.concat([df_train_s0_s1, df_train_s2_s3_s4], axis=0, ignore_index=True)

df_train_s0_s1_s2 = df_train[df_train["Group3_normalized"].isin(["S0", "S1", "S2"])]
df_train_s3_s4 = df_train[df_train["Group3_normalized"].isin(["S3", "S4"])]
df_train_task3 = pd.concat([df_train_s0_s1_s2, df_train_s3_s4], axis=0, ignore_index=True)

df_train_s0_s1_s2_s3 = df_train[df_train["Group3_normalized"].isin(["S0", "S1", "S2", "S3"])]
df_train_s4 = df_train[df_train["Group3_normalized"].isin(["S4"])]
df_train_task4 = pd.concat([df_train_s0_s1_s2_s3, df_train_s4], axis=0, ignore_index=True)

df_val_control = df_val[df_val['Group1'].str.contains("Control", na=False, case=False)]
df_val_hbv = df_val[df_val['Group1'].str.contains("HBV", na=False, case=False)]
df_val_task1 = pd.concat([df_val_control, df_val_hbv], axis=0, ignore_index=True)

df_val_s0_s1 = df_val[df_val["Group3_normalized"].isin(["S0", "S1"])]
df_val_s2_s3_s4 = df_val[df_val["Group3_normalized"].isin(["S2", "S3", "S4"])]
df_val_task2 = pd.concat([df_val_s0_s1, df_val_s2_s3_s4], axis=0, ignore_index=True)

df_val_s0_s1_s2 = df_val[df_val["Group3_normalized"].isin(["S0", "S1", "S2"])]
df_val_s3_s4 = df_val[df_val["Group3_normalized"].isin(["S3", "S4"])]
df_val_task3 = pd.concat([df_val_s0_s1_s2, df_val_s3_s4], axis=0, ignore_index=True)

df_val_s0_s1_s2_s3 = df_val[df_val["Group3_normalized"].isin(["S0", "S1", "S2", "S3"])]
df_val_s4 = df_val[df_val["Group3_normalized"].isin(["S4"])]
df_val_task4 = pd.concat([df_val_s0_s1_s2_s3, df_val_s4], axis=0, ignore_index=True)

def plot_roc_prc_curves(tasks_data, data_dir, output_filename='Fig_S3_ROC_PRC_Validation.pdf'):
    output_path = f"{data_dir}/{output_filename}"

    valid_tasks = {k: v for k, v in tasks_data.items() if v is not None}

    if len(valid_tasks) == 0:
        return

    fig, axes = plt.subplots(4, 2, figsize=(16, 24))

    colors =['#3B7097', '#75BDE0', '#A9D09E']

    task_list = list(valid_tasks.items())

    for idx, (task_name, task_data) in enumerate(task_list):
        roc_row = idx // 2
        roc_col = idx % 2
        prc_row = roc_row + 2
        prc_col = roc_col

        y_true = task_data['y_true']
        probs_panel = task_data['probs_panel']
        probs_tyr_tca = task_data['probs_tyr_tca']
        fib4_scores = task_data['fib4_scores']

        ax_roc = axes[roc_row, roc_col]

        fpr, tpr, _ = roc_curve(y_true, probs_panel)
        roc_auc = auc(fpr, tpr)
        auc_lower, auc_upper = bootstrap_ci(y_true, probs_panel, 
                                             lambda y, s: auc(*roc_curve(y, s)[:2]), 
                                             n_bootstraps=1000)
        fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, probs_panel, n_bootstraps=1000)

        ax_roc.plot(fpr, tpr, label=f'Met-FIB (AUC={roc_auc:.3f}[{auc_lower:.3f}-{auc_upper:.3f}])', 
                   linewidth=3.5, color=colors[0])
        ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[0], alpha=0.2)

        fpr, tpr, _ = roc_curve(y_true, probs_tyr_tca)
        roc_auc = auc(fpr, tpr)
        auc_lower, auc_upper = bootstrap_ci(y_true, probs_tyr_tca, 
                                             lambda y, s: auc(*roc_curve(y, s)[:2]), 
                                             n_bootstraps=1000)
        fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, probs_tyr_tca, n_bootstraps=1000)

        ax_roc.plot(fpr, tpr, label=f'Tyr+TCA (AUC={roc_auc:.3f}[{auc_lower:.3f}-{auc_upper:.3f}])', 
                   linewidth=3.5, color=colors[1])
        ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[1], alpha=0.2)

        if fib4_scores is not None:
            fpr, tpr, _ = roc_curve(y_true, fib4_scores)
            roc_auc = auc(fpr, tpr)
            auc_lower, auc_upper = bootstrap_ci(y_true, fib4_scores, 
                                                 lambda y, s: auc(*roc_curve(y, s)[:2]), 
                                                 n_bootstraps=1000)
            fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, fib4_scores, n_bootstraps=1000)

            ax_roc.plot(fpr, tpr, label=f'FIB-4 (AUC={roc_auc:.3f} [{auc_lower:.3f}-{auc_upper:.3f}])', 
                       linewidth=3.5, linestyle='--', color=colors[2])
            ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[2], alpha=0.15)

        ax_roc.plot([0, 1], [0, 1], 'k--', linewidth=2.5, alpha=0.5)
        ax_roc.set_xlabel('False Positive Rate', fontsize=24)
        ax_roc.set_ylabel('True Positive Rate', fontsize=24)
        ax_roc.legend(loc='lower right', fontsize=16, framealpha=0.9)
        ax_roc.grid(True, alpha=0.3, linestyle=':')
        ax_roc.set_xlim([-0.02, 1.02])
        ax_roc.set_ylim([-0.02, 1.02])
        ax_roc.tick_params(axis='both', which='major', labelsize=20)

        ax_prc = axes[prc_row, prc_col]

        precision, recall, _ = precision_recall_curve(y_true, probs_panel)
        ap = average_precision_score(y_true, probs_panel)
        ap_lower, ap_upper = bootstrap_ci(y_true, probs_panel, 
                                           average_precision_score, 
                                           n_bootstraps=1000)
        recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, probs_panel, n_bootstraps=1000)

        ax_prc.plot(recall, precision, label=f'Met-FIB (AP={ap:.3f}[{ap_lower:.3f}-{ap_upper:.3f}])', 
                   linewidth=3.5, color=colors[0])
        ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[0], alpha=0.2)

        precision, recall, _ = precision_recall_curve(y_true, probs_tyr_tca)
        ap = average_precision_score(y_true, probs_tyr_tca)
        ap_lower, ap_upper = bootstrap_ci(y_true, probs_tyr_tca, 
                                           average_precision_score, 
                                           n_bootstraps=1000)
        recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, probs_tyr_tca, n_bootstraps=1000)

        ax_prc.plot(recall, precision, label=f'Tyr+TCA (AP={ap:.3f}[{ap_lower:.3f}-{ap_upper:.3f}])', 
                   linewidth=3.5, color=colors[1])
        ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[1], alpha=0.2)

        if fib4_scores is not None:
            precision, recall, _ = precision_recall_curve(y_true, fib4_scores)
            ap = average_precision_score(y_true, fib4_scores)
            ap_lower, ap_upper = bootstrap_ci(y_true, fib4_scores, 
                                               average_precision_score, 
                                               n_bootstraps=1000)
            recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, fib4_scores, n_bootstraps=1000)

            ax_prc.plot(recall, precision, label=f'FIB-4 (AP={ap:.3f} [{ap_lower:.3f}-{ap_upper:.3f}])', 
                       linewidth=3.5, linestyle='--', color=colors[2])
            ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[2], alpha=0.15)

        baseline = np.sum(y_true) / len(y_true)
        ax_prc.axhline(y=baseline, color='k', linestyle='--', linewidth=2.5, alpha=0.5)

        ax_prc.set_xlabel('Recall', fontsize=24)
        ax_prc.set_ylabel('Precision', fontsize=24)
        ax_prc.legend(loc='lower left', fontsize=16, framealpha=0.9)
        ax_prc.grid(True, alpha=0.3, linestyle=':')
        ax_prc.set_xlim([-0.02, 1.02])
        ax_prc.set_ylim([-0.02, 1.02])
        ax_prc.tick_params(axis='both', which='major', labelsize=20)

    plt.subplots_adjust(top=0.92, bottom=0.03, left=0.08, right=0.98, hspace=0.35, wspace=0.25)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', format='pdf')
    plt.close()

def main():
    tasks_data = {}

    X_train_panel = df_train_task1[met_names]
    X_train_tyr_tca = df_train_task1[['Tyrosine', 'Taurocholic acid']]
    y_train = df_train_task1['Group1'].map(lambda x: 0 if 'Control' in str(x) else 1).values
    fib4_train = df_train_task1['FIB4'].values

    X_val_panel = df_val_task1[met_names]
    X_val_tyr_tca = df_val_task1[['Tyrosine', 'Taurocholic acid']]
    y_val = df_val_task1['Group1'].map(lambda x: 0 if 'Control' in str(x) else 1).values
    fib4_val = df_val_task1['FIB4'].values

    valid_mask_train = (~X_train_panel.isna().any(axis=1) & ~X_train_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_train))
    valid_mask_val = (~X_val_panel.isna().any(axis=1) & ~X_val_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_val))

    X_train_panel_clean = X_train_panel[valid_mask_train]
    X_train_tyr_tca_clean = X_train_tyr_tca[valid_mask_train]
    y_train_clean = y_train[valid_mask_train]
    fib4_train_clean = fib4_train[valid_mask_train]

    X_val_panel_clean = X_val_panel[valid_mask_val]
    X_val_tyr_tca_clean = X_val_tyr_tca[valid_mask_val]
    y_val_clean = y_val[valid_mask_val]
    fib4_val_clean = fib4_val[valid_mask_val]

    if len(y_val_clean) < 10 or np.sum(y_val_clean==0) < 2 or np.sum(y_val_clean==1) < 2:
        tasks_data['Task 1: CHB vs. controls'] = None
    else:
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        probs_panel_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_panel_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_panel_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_panel_val += model.predict_proba(X_val_panel_clean)[:, 1]
        probs_panel = probs_panel_val / 5

        probs_tyr_tca_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_tyr_tca_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_tyr_tca_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_tyr_tca_val += model.predict_proba(X_val_tyr_tca_clean)[:, 1]
        probs_tyr_tca = probs_tyr_tca_val / 5

        tasks_data['Task 1: CHB vs. controls'] = {
            'y_true': y_val_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_val_clean
        }

    X_train_panel = df_train_task2[met_names]
    X_train_tyr_tca = df_train_task2[['Tyrosine', 'Taurocholic acid']]
    y_train = df_train_task2['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 1, 'S3': 1, 'S4': 1}).values
    fib4_train = df_train_task2['FIB4'].values

    X_val_panel = df_val_task2[met_names]
    X_val_tyr_tca = df_val_task2[['Tyrosine', 'Taurocholic acid']]
    y_val = df_val_task2['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 1, 'S3': 1, 'S4': 1}).values
    fib4_val = df_val_task2['FIB4'].values

    valid_mask_train = (~X_train_panel.isna().any(axis=1) & ~X_train_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_train))
    valid_mask_val = (~X_val_panel.isna().any(axis=1) & ~X_val_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_val))

    X_train_panel_clean = X_train_panel[valid_mask_train]
    X_train_tyr_tca_clean = X_train_tyr_tca[valid_mask_train]
    y_train_clean = y_train[valid_mask_train]

    X_val_panel_clean = X_val_panel[valid_mask_val]
    X_val_tyr_tca_clean = X_val_tyr_tca[valid_mask_val]
    y_val_clean = y_val[valid_mask_val]
    fib4_val_clean = fib4_val[valid_mask_val]

    if len(y_val_clean) < 10 or np.sum(y_val_clean==0) < 2 or np.sum(y_val_clean==1) < 2:
        tasks_data['Task 2: Significant fibrosis vs. S0-S1'] = None
    else:
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        probs_panel_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_panel_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_panel_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_panel_val += model.predict_proba(X_val_panel_clean)[:, 1]
        probs_panel = probs_panel_val / 5

        probs_tyr_tca_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_tyr_tca_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_tyr_tca_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_tyr_tca_val += model.predict_proba(X_val_tyr_tca_clean)[:, 1]
        probs_tyr_tca = probs_tyr_tca_val / 5

        tasks_data['Task 2: Significant fibrosis vs. S0-S1'] = {
            'y_true': y_val_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_val_clean
        }

    X_train_panel = df_train_task3[met_names]
    X_train_tyr_tca = df_train_task3[['Tyrosine', 'Taurocholic acid']]
    y_train = df_train_task3['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 1, 'S4': 1}).values
    fib4_train = df_train_task3['FIB4'].values

    X_val_panel = df_val_task3[met_names]
    X_val_tyr_tca = df_val_task3[['Tyrosine', 'Taurocholic acid']]
    y_val = df_val_task3['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 1, 'S4': 1}).values
    fib4_val = df_val_task3['FIB4'].values

    valid_mask_train = (~X_train_panel.isna().any(axis=1) & ~X_train_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_train))
    valid_mask_val = (~X_val_panel.isna().any(axis=1) & ~X_val_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_val))

    X_train_panel_clean = X_train_panel[valid_mask_train]
    X_train_tyr_tca_clean = X_train_tyr_tca[valid_mask_train]
    y_train_clean = y_train[valid_mask_train]

    X_val_panel_clean = X_val_panel[valid_mask_val]
    X_val_tyr_tca_clean = X_val_tyr_tca[valid_mask_val]
    y_val_clean = y_val[valid_mask_val]
    fib4_val_clean = fib4_val[valid_mask_val]

    if len(y_val_clean) < 10 or np.sum(y_val_clean==0) < 2 or np.sum(y_val_clean==1) < 2:
        tasks_data['Task 3: Advanced fibrosis vs. S0-S2'] = None
    else:
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        probs_panel_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_panel_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_panel_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_panel_val += model.predict_proba(X_val_panel_clean)[:, 1]
        probs_panel = probs_panel_val / 5

        probs_tyr_tca_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_tyr_tca_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_tyr_tca_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_tyr_tca_val += model.predict_proba(X_val_tyr_tca_clean)[:, 1]
        probs_tyr_tca = probs_tyr_tca_val / 5

        tasks_data['Task 3: Advanced fibrosis vs. S0-S2'] = {
            'y_true': y_val_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_val_clean
        }

    X_train_panel = df_train_task4[met_names]
    X_train_tyr_tca = df_train_task4[['Tyrosine', 'Taurocholic acid']]
    y_train = df_train_task4['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 0, 'S4': 1}).values
    fib4_train = df_train_task4['FIB4'].values

    X_val_panel = df_val_task4[met_names]
    X_val_tyr_tca = df_val_task4[['Tyrosine', 'Taurocholic acid']]
    y_val = df_val_task4['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 0, 'S4': 1}).values
    fib4_val = df_val_task4['FIB4'].values

    valid_mask_train = (~X_train_panel.isna().any(axis=1) & ~X_train_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_train))
    valid_mask_val = (~X_val_panel.isna().any(axis=1) & ~X_val_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4_val))

    X_train_panel_clean = X_train_panel[valid_mask_train]
    X_train_tyr_tca_clean = X_train_tyr_tca[valid_mask_train]
    y_train_clean = y_train[valid_mask_train]

    X_val_panel_clean = X_val_panel[valid_mask_val]
    X_val_tyr_tca_clean = X_val_tyr_tca[valid_mask_val]
    y_val_clean = y_val[valid_mask_val]
    fib4_val_clean = fib4_val[valid_mask_val]

    if len(y_val_clean) < 10 or np.sum(y_val_clean==0) < 2 or np.sum(y_val_clean==1) < 2:
        tasks_data['Task 4: Cirrhosis vs. S0-S3'] = None
    else:
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        probs_panel_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_panel_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_panel_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_panel_val += model.predict_proba(X_val_panel_clean)[:, 1]
        probs_panel = probs_panel_val / 5

        probs_tyr_tca_val = np.zeros(len(y_val_clean))
        for fold, (train_idx, _) in enumerate(kf.split(X_train_tyr_tca_clean), 1):
            model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)
            model.fit(X_train_tyr_tca_clean.iloc[train_idx], y_train_clean[train_idx])
            probs_tyr_tca_val += model.predict_proba(X_val_tyr_tca_clean)[:, 1]
        probs_tyr_tca = probs_tyr_tca_val / 5

        tasks_data['Task 4: Cirrhosis vs. S0-S3'] = {
            'y_true': y_val_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_val_clean
        }

    plot_roc_prc_curves(tasks_data, data_dir)

if __name__ == "__main__":
    main()

