from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold

# Use the original project root so we can import the full pipeline modules.
PROJECT_ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.io.load_data import load_project_tables
from src.data.build_cohort import build_analysis_cohorts
from src.models.run_nested_cv import (
    build_default_experiment_registry,
    _merge_cv_config,
    _extract_xy,
    _prepare_experiment_features,
    _build_estimator,
)

plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

EXPERIMENT = 'fusion_full_elastic_net'  # highest mean train AUC in current results
TITLE_NAME = 'Expanded fusion model'


def load_config() -> dict:
    return yaml.safe_load((PROJECT_ROOT / 'config/analysis.yaml').read_text(encoding='utf-8'))


def build_data(config: dict):
    paths = config['paths']
    raw_tables = load_project_tables(
        group_path=paths['group'],
        lipid_path=paths['lipid'],
        clinical_full_path=paths['clinical_full'],
        clinical_slim_path=paths['clinical_slim'],
    )
    return build_analysis_cohorts(raw_tables)


def rerun_for_train_and_test_curves():
    config = load_config()
    cohorts = build_data(config)
    registry = build_default_experiment_registry()
    spec = registry[EXPERIMENT]
    frame = getattr(cohorts, spec.cohort_key)
    cv_config = _merge_cv_config(config.get('experiments', {}).get('cv_config'))
    positive_label = config.get('target', {}).get('positive_label', 'response')

    X, y = _extract_xy(frame, positive_label=positive_label)
    outer_cv = RepeatedStratifiedKFold(
        n_splits=cv_config['outer_splits'],
        n_repeats=cv_config['outer_repeats'],
        random_state=cv_config['random_state'],
    )

    fold_payloads = []
    for fold_index, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        train_frame = X.iloc[train_idx].reset_index(drop=True)
        test_frame = X.iloc[test_idx].reset_index(drop=True)
        y_train = y[train_idx]
        y_test = y[test_idx]

        train_ready, test_ready, selected_features = _prepare_experiment_features(
            spec=spec,
            train_frame=train_frame,
            test_frame=test_frame,
            y_train=y_train,
            cv_config=cv_config,
        )

        estimator, grid = _build_estimator(spec.model_family)
        inner_cv = StratifiedKFold(
            n_splits=cv_config['inner_splits'],
            shuffle=True,
            random_state=cv_config['random_state'] + fold_index,
        )
        search = GridSearchCV(
            estimator=estimator,
            param_grid=grid,
            scoring='roc_auc',
            cv=inner_cv,
            n_jobs=1,
            refit=True,
            error_score='raise',
        )
        search.fit(train_ready, y_train)
        train_score = search.predict_proba(train_ready)[:, 1]
        test_score = search.predict_proba(test_ready)[:, 1]

        train_fpr, train_tpr, _ = roc_curve(y_train, train_score)
        test_fpr, test_tpr, _ = roc_curve(y_test, test_score)

        fold_payloads.append({
            'fold_index': fold_index,
            'train_fpr': train_fpr,
            'train_tpr': train_tpr,
            'test_fpr': test_fpr,
            'test_tpr': test_tpr,
            'train_auc': roc_auc_score(y_train, train_score),
            'test_auc': roc_auc_score(y_test, test_score),
            'n_features': len(selected_features),
        })
    return fold_payloads


def mean_roc(payloads, key_prefix: str, grid=None):
    if grid is None:
        grid = np.linspace(0, 1, 201)
    curves = []
    aucs = []
    for item in payloads:
        fpr = item[f'{key_prefix}_fpr']
        tpr = item[f'{key_prefix}_tpr']
        interp_tpr = np.interp(grid, fpr, tpr)
        interp_tpr[0] = 0.0
        interp_tpr[-1] = 1.0
        curves.append(interp_tpr)
        aucs.append(item[f'{key_prefix}_auc'])
    curves = np.vstack(curves)
    return {
        'grid': grid,
        'mean_tpr': curves.mean(axis=0),
        'std_tpr': curves.std(axis=0),
        'mean_auc': float(np.mean(aucs)),
        'std_auc': float(np.std(aucs, ddof=0)),
    }


def make_plot(payloads):
    train_summary = mean_roc(payloads, 'train')
    test_summary = mean_roc(payloads, 'test')

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)

    # Panel A: fold-specific training ROC
    ax = axes[0]
    for item in payloads:
        ax.plot(item['train_fpr'], item['train_tpr'], color='#F6A57A', alpha=0.35, linewidth=1.2)
    ax.plot(train_summary['grid'], train_summary['mean_tpr'], color='#D94801', linewidth=2.8,
            label=f"Mean training ROC (AUC = {train_summary['mean_auc']:.3f} ± {train_summary['std_auc']:.3f})")
    ax.fill_between(
        train_summary['grid'],
        np.clip(train_summary['mean_tpr'] - train_summary['std_tpr'], 0, 1),
        np.clip(train_summary['mean_tpr'] + train_summary['std_tpr'], 0, 1),
        color='#FDD0A2', alpha=0.35, label='±1 SD'
    )
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', linewidth=1)
    ax.set_title('A. Training ROC curves', fontweight='bold')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(frameon=False, loc='lower right')
    ax.grid(alpha=0.25)

    # Panel B: mean training vs outer-test ROC
    ax = axes[1]
    for item in payloads:
        ax.plot(item['test_fpr'], item['test_tpr'], color='#9ECAE1', alpha=0.35, linewidth=1.1)
    ax.plot(train_summary['grid'], train_summary['mean_tpr'], color='#D94801', linewidth=2.6,
            label=f"Training mean ROC (AUC = {train_summary['mean_auc']:.3f})")
    ax.plot(test_summary['grid'], test_summary['mean_tpr'], color='#08519C', linewidth=2.6,
            label=f"Outer-test mean ROC (AUC = {test_summary['mean_auc']:.3f})")
    ax.fill_between(
        test_summary['grid'],
        np.clip(test_summary['mean_tpr'] - test_summary['std_tpr'], 0, 1),
        np.clip(test_summary['mean_tpr'] + test_summary['std_tpr'], 0, 1),
        color='#BDD7E7', alpha=0.30
    )
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', linewidth=1)
    ax.set_title('B. Training vs outer-test ROC', fontweight='bold')
    ax.set_xlabel('False Positive Rate')
    ax.legend(frameon=False, loc='lower right')
    ax.grid(alpha=0.25)

    fig.suptitle(
        f'English ROC figure for the model with the highest mean training AUC\n{TITLE_NAME} ({EXPERIMENT})',
        fontsize=14,
        fontweight='bold',
        y=1.02,
    )
    plt.tight_layout()

    png = PACKAGE_ROOT / '20260311_BestTrainingModel_English_ROC.png'
    pdf = PACKAGE_ROOT / '20260311_BestTrainingModel_English_ROC.pdf'
    fig.savefig(png, bbox_inches='tight')
    fig.savefig(pdf, bbox_inches='tight')
    plt.close(fig)

    # Also save a compact single-panel overlay for direct use
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ax.plot(train_summary['grid'], train_summary['mean_tpr'], color='#D94801', linewidth=2.8,
            label=f"Training mean ROC (AUC = {train_summary['mean_auc']:.3f})")
    ax.plot(test_summary['grid'], test_summary['mean_tpr'], color='#08519C', linewidth=2.8,
            label=f"Outer-test mean ROC (AUC = {test_summary['mean_auc']:.3f})")
    ax.fill_between(
        train_summary['grid'],
        np.clip(train_summary['mean_tpr'] - train_summary['std_tpr'], 0, 1),
        np.clip(train_summary['mean_tpr'] + train_summary['std_tpr'], 0, 1),
        color='#FDD0A2', alpha=0.25
    )
    ax.fill_between(
        test_summary['grid'],
        np.clip(test_summary['mean_tpr'] - test_summary['std_tpr'], 0, 1),
        np.clip(test_summary['mean_tpr'] + test_summary['std_tpr'], 0, 1),
        color='#BDD7E7', alpha=0.25
    )
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', linewidth=1)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('Training-focused ROC figure (English)', fontweight='bold')
    ax.legend(frameon=False, loc='lower right')
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(PACKAGE_ROOT / '20260311_BestTrainingModel_English_ROC_overlay.png', bbox_inches='tight')
    fig.savefig(PACKAGE_ROOT / '20260311_BestTrainingModel_English_ROC_overlay.pdf', bbox_inches='tight')
    plt.close(fig)

    summary = PACKAGE_ROOT / 'README_English_ROC_training_focus.md'
    summary.write_text(
        '\n'.join([
            '# English ROC figures focused on the best training result',
            '',
            'These figures were generated for the model with the highest mean training AUC in the current strict nested CV results.',
            '',
            f'- Model: {TITLE_NAME} ({EXPERIMENT})',
            f'- Mean training AUC: {train_summary["mean_auc"]:.3f} ± {train_summary["std_auc"]:.3f}',
            f'- Mean outer-test AUC: {test_summary["mean_auc"]:.3f} ± {test_summary["std_auc"]:.3f}',
            '',
            'Recommended use:',
            '1. Use `20260311_BestTrainingModel_English_ROC.png` when you want an English two-panel ROC figure.',
            '2. Use `20260311_BestTrainingModel_English_ROC_overlay.png` when you want a compact English figure showing how much better the training ROC looks than the outer-test ROC.',
            '',
            'Important note:',
            'The training ROC is visually stronger because it reflects model fit on training folds. It should be presented together with the outer-test ROC, not as a standalone formal performance claim.',
        ]),
        encoding='utf-8'
    )

    return train_summary, test_summary


if __name__ == '__main__':
    payloads = rerun_for_train_and_test_curves()
    train_summary, test_summary = make_plot(payloads)
    print('model:', TITLE_NAME)
    print('mean training auc:', round(train_summary['mean_auc'], 4))
    print('mean outer-test auc:', round(test_summary['mean_auc'], 4))
