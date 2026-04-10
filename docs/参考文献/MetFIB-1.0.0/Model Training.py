#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from sklearn.model_selection import cross_val_predict
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
df = pd.read_csv(f"{data_dir}/training.txt", sep="\t", encoding="utf-8", low_memory=False)
headers = df.columns
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

df['Group3_normalized'] = df['Group3'].apply(normalize_group3)

df_control = df[df['Group1'].str.contains("Control", na=False, case=False)]
df_hbv = df[df['Group1'].str.contains("HBV", na=False, case=False)]
df_model1 = pd.concat([df_control, df_hbv], axis=0, ignore_index=True)

df_s0_s1 = df[df["Group3_normalized"].isin(["S0", "S1"])]
df_s2_s3_s4 = df[df["Group3_normalized"].isin(["S2", "S3", "S4"])]
df_model2 = pd.concat([df_s0_s1, df_s2_s3_s4], axis=0, ignore_index=True)

df_s0_s1_s2 = df[df["Group3_normalized"].isin(["S0", "S1", "S2"])]
df_s3_s4 = df[df["Group3_normalized"].isin(["S3", "S4"])]
df_model3 = pd.concat([df_s0_s1_s2, df_s3_s4], axis=0, ignore_index=True)

df_s0_s1_s2_s3 = df[df["Group3_normalized"].isin(["S0", "S1", "S2", "S3"])]
df_s4 = df[df["Group3_normalized"].isin(["S4"])]
df_model4 = pd.concat([df_s0_s1_s2_s3, df_s4], axis=0, ignore_index=True)

def get_cv_predictions(X, y, model):
    y_probs = cross_val_predict(model, X, y, cv=5, method='predict_proba')
    return y_probs[:, 1]

def plot_roc_prc_curves(tasks_data, data_dir, output_filename='Fig_S2_ROC_PRC_Cohort1.pdf'):
    output_path = f"{data_dir}/{output_filename}"
    valid_tasks = {k: v for k, v in tasks_data.items() if v is not None}

    if len(valid_tasks) == 0:
        return

    num_tasks = len(valid_tasks)
    fig, axes = plt.subplots(num_tasks, 2, figsize=(16, 6*num_tasks))

    if num_tasks == 1:
        axes = axes.reshape(1, -1)

    colors =['#3B7097', '#75BDE0', '#A9D09E']

    for idx, (task_name, task_data) in enumerate(valid_tasks.items()):
        row = idx
        y_true = task_data['y_true']
        probs_panel = task_data['probs_panel']
        probs_tyr_tca = task_data['probs_tyr_tca']
        fib4_scores = task_data['fib4_scores']

        ax_roc = axes[row, 0]
        fpr, tpr, _ = roc_curve(y_true, probs_panel)
        roc_auc = auc(fpr, tpr)
        auc_lower, auc_upper = bootstrap_ci(y_true, probs_panel, lambda y, s: auc(*roc_curve(y, s)[:2]), n_bootstraps=1000)
        fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, probs_panel, n_bootstraps=1000)
        ax_roc.plot(fpr, tpr, label=f'Met-FIB (AUC={roc_auc:.3f} [{auc_lower:.3f}-{auc_upper:.3f}])', linewidth=3.5, color=colors[0])
        ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[0], alpha=0.2)

        fpr, tpr, _ = roc_curve(y_true, probs_tyr_tca)
        roc_auc = auc(fpr, tpr)
        auc_lower, auc_upper = bootstrap_ci(y_true, probs_tyr_tca, lambda y, s: auc(*roc_curve(y, s)[:2]), n_bootstraps=1000)
        fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, probs_tyr_tca, n_bootstraps=1000)
        ax_roc.plot(fpr, tpr, label=f'Tyr and TCA (AUC={roc_auc:.3f}[{auc_lower:.3f}-{auc_upper:.3f}])', linewidth=3.5, color=colors[1])
        ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[1], alpha=0.2)

        fpr, tpr, _ = roc_curve(y_true, fib4_scores)
        roc_auc = auc(fpr, tpr)
        auc_lower, auc_upper = bootstrap_ci(y_true, fib4_scores, lambda y, s: auc(*roc_curve(y, s)[:2]), n_bootstraps=1000)
        fpr_interp, tpr_mean, tpr_lower, tpr_upper = compute_roc_ci(y_true, fib4_scores, n_bootstraps=1000)
        ax_roc.plot(fpr, tpr, label=f'FIB-4 (AUC={roc_auc:.3f} [{auc_lower:.3f}-{auc_upper:.3f}])', linewidth=3.5, linestyle='--', color=colors[2])
        ax_roc.fill_between(fpr_interp, tpr_lower, tpr_upper, color=colors[2], alpha=0.15)

        ax_roc.plot([0, 1], [0, 1], 'k--', linewidth=2.5, alpha=0.5)
        ax_roc.set_xlabel('False Positive Rate', fontsize=24)
        ax_roc.set_ylabel('True Positive Rate', fontsize=24)
        ax_roc.legend(loc='lower right', fontsize=15, framealpha=0.9)
        ax_roc.grid(True, alpha=0.3, linestyle=':')
        ax_roc.tick_params(axis='both', which='major', labelsize=20)
        ax_roc.set_xlim([-0.02, 1.02])
        ax_roc.set_ylim([-0.02, 1.02])

        ax_prc = axes[row, 1]
        precision, recall, _ = precision_recall_curve(y_true, probs_panel)
        ap = average_precision_score(y_true, probs_panel)
        ap_lower, ap_upper = bootstrap_ci(y_true, probs_panel, average_precision_score, n_bootstraps=1000)
        recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, probs_panel, n_bootstraps=1000)
        ax_prc.plot(recall, precision, label=f'Met-FIB (AP={ap:.3f}[{ap_lower:.3f}-{ap_upper:.3f}])', linewidth=3.5, color=colors[0])
        ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[0], alpha=0.2)

        precision, recall, _ = precision_recall_curve(y_true, probs_tyr_tca)
        ap = average_precision_score(y_true, probs_tyr_tca)
        ap_lower, ap_upper = bootstrap_ci(y_true, probs_tyr_tca, average_precision_score, n_bootstraps=1000)
        recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, probs_tyr_tca, n_bootstraps=1000)
        ax_prc.plot(recall, precision, label=f'Tyr and TCA (AP={ap:.3f}[{ap_lower:.3f}-{ap_upper:.3f}])', linewidth=3.5, color=colors[1])
        ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[1], alpha=0.2)

        precision, recall, _ = precision_recall_curve(y_true, fib4_scores)
        ap = average_precision_score(y_true, fib4_scores)
        ap_lower, ap_upper = bootstrap_ci(y_true, fib4_scores, average_precision_score, n_bootstraps=1000)
        recall_interp, precision_mean, precision_lower, precision_upper = compute_prc_ci(y_true, fib4_scores, n_bootstraps=1000)
        ax_prc.plot(recall, precision, label=f'FIB-4 (AP={ap:.3f}[{ap_lower:.3f}-{ap_upper:.3f}])', linewidth=3.5, linestyle='--', color=colors[2])
        ax_prc.fill_between(recall_interp, precision_lower, precision_upper, color=colors[2], alpha=0.15)

        baseline = np.sum(y_true) / len(y_true)
        ax_prc.axhline(y=baseline, color='k', linestyle='--', linewidth=2.5, alpha=0.5)
        ax_prc.set_xlabel('Recall', fontsize=24)
        ax_prc.set_ylabel('Precision', fontsize=24)
        ax_prc.legend(loc='lower left', fontsize=15, framealpha=0.9)
        ax_prc.grid(True, alpha=0.3, linestyle=':')
        ax_prc.tick_params(axis='both', which='major', labelsize=20)
        ax_prc.set_xlim([-0.02, 1.02])
        ax_prc.set_ylim([-0.02, 1.02])

    plt.subplots_adjust(top=0.92, bottom=0.05, left=0.08, right=0.98, hspace=0.35, wspace=0.25)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', format='pdf')
    plt.close()

def main():
    data_dir = "/Users/weijiaresearchteam/Desktop/Fibrosis"
    tasks_data = {}

    X_panel = df_model1[met_names]
    X_tyr_tca = df_model1[['Tyrosine', 'Taurocholic acid']]
    fib4 = df_model1['FIB4'].values
    y = df_model1['Group1'].map({'Control': 0, 'HBV': 1}).values

    valid_mask = (~X_panel.isna().any(axis=1) & ~X_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4))
    X_panel_clean = X_panel[valid_mask]
    X_tyr_tca_clean = X_tyr_tca[valid_mask]
    fib4_clean = fib4[valid_mask]
    y_clean = y[valid_mask]

    model = TabPFNClassifier(device='cpu', random_state=42, ignore_pretraining_limits=True)

    probs_panel = get_cv_predictions(X_panel_clean, y_clean, model)
    probs_tyr_tca = get_cv_predictions(X_tyr_tca_clean, y_clean, model)

    tasks_data['A-B: CHB vs. controls'] = {
        'y_true': y_clean,
        'probs_panel': probs_panel,
        'probs_tyr_tca': probs_tyr_tca,
        'fib4_scores': fib4_clean
    }

    X_panel = df_model2[met_names]
    X_tyr_tca = df_model2[['Tyrosine', 'Taurocholic acid']]
    y = df_model2['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 1, 'S3': 1, 'S4': 1}).values
    fib4 = df_model2['FIB4'].values

    valid_mask = (~X_panel.isna().any(axis=1) & ~X_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4))
    X_panel_clean = X_panel[valid_mask]
    X_tyr_tca_clean = X_tyr_tca[valid_mask]
    y_clean = y[valid_mask]
    fib4_clean = fib4[valid_mask]

    if len(y_clean) >= 10 and np.sum(y_clean==0) >= 2 and np.sum(y_clean==1) >= 2:
        probs_panel = get_cv_predictions(X_panel_clean, y_clean, model)
        probs_tyr_tca = get_cv_predictions(X_tyr_tca_clean, y_clean, model)
        tasks_data['C-D: Significant fibrosis vs. S0-S1'] = {
            'y_true': y_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_clean
        }

    X_panel = df_model3[met_names]
    X_tyr_tca = df_model3[['Tyrosine', 'Taurocholic acid']]
    y = df_model3['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 1, 'S4': 1}).values
    fib4 = df_model3['FIB4'].values

    valid_mask = (~X_panel.isna().any(axis=1) & ~X_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4))
    X_panel_clean = X_panel[valid_mask]
    X_tyr_tca_clean = X_tyr_tca[valid_mask]
    y_clean = y[valid_mask]
    fib4_clean = fib4[valid_mask]

    if len(y_clean) >= 10 and np.sum(y_clean==0) >= 2 and np.sum(y_clean==1) >= 2:
        probs_panel = get_cv_predictions(X_panel_clean, y_clean, model)
        probs_tyr_tca = get_cv_predictions(X_tyr_tca_clean, y_clean, model)
        tasks_data['E-F: Advanced fibrosis vs. S0-S2'] = {
            'y_true': y_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_clean
        }

    X_panel = df_model4[met_names]
    X_tyr_tca = df_model4[['Tyrosine', 'Taurocholic acid']]
    y = df_model4['Group3_normalized'].map({'S0': 0, 'S1': 0, 'S2': 0, 'S3': 0, 'S4': 1}).values
    fib4 = df_model4['FIB4'].values

    valid_mask = (~X_panel.isna().any(axis=1) & ~X_tyr_tca.isna().any(axis=1) & ~pd.isna(fib4))
    X_panel_clean = X_panel[valid_mask]
    X_tyr_tca_clean = X_tyr_tca[valid_mask]
    y_clean = y[valid_mask]
    fib4_clean = fib4[valid_mask]

    if len(y_clean) >= 10 and np.sum(y_clean==0) >= 2 and np.sum(y_clean==1) >= 2:
        probs_panel = get_cv_predictions(X_panel_clean, y_clean, model)
        probs_tyr_tca = get_cv_predictions(X_tyr_tca_clean, y_clean, model)
        tasks_data['G-H: Cirrhosis vs. S0-S3'] = {
            'y_true': y_clean,
            'probs_panel': probs_panel,
            'probs_tyr_tca': probs_tyr_tca,
            'fib4_scores': fib4_clean
        }

    plot_roc_prc_curves(tasks_data, data_dir)

if __name__ == "__main__":
    main()


# In[ ]:




