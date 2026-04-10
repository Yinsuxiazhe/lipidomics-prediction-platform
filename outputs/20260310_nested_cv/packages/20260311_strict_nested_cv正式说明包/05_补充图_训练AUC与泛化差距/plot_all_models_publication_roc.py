from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold

PROJECT_ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
OUT_DIR = Path(__file__).resolve().parent
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

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

MODEL_META = {
    'clinical_slim_logistic': {
        'title': 'ROC curves for the clinical baseline model',
        'short': 'clinical_baseline',
    },
    'clinical_full_elastic_net': {
        'title': 'ROC curves for the expanded clinical model',
        'short': 'expanded_clinical',
    },
    'lipid_elastic_net': {
        'title': 'ROC curves for the lipid-only model',
        'short': 'lipid_only',
    },
    'fusion_elastic_net': {
        'title': 'ROC curves for the clinical–lipid fusion model',
        'short': 'clinical_lipid_fusion',
    },
    'fusion_full_elastic_net': {
        'title': 'ROC curves for the expanded fusion model',
        'short': 'expanded_fusion',
    },
}

TRAIN_COLOR = '#D94801'
TEST_COLOR = '#08519C'
REF_COLOR = '0.70'


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


def rerun_experiment(experiment_name: str):
    config = load_config()
    cohorts = build_data(config)
    registry = build_default_experiment_registry()
    spec = registry[experiment_name]
    frame = getattr(cohorts, spec.cohort_key)
    cv_config = _merge_cv_config(config.get('experiments', {}).get('cv_config'))
    positive_label = config.get('target', {}).get('positive_label', 'response')

    X, y = _extract_xy(frame, positive_label=positive_label)
    outer_cv = RepeatedStratifiedKFold(
        n_splits=cv_config['outer_splits'],
        n_repeats=cv_config['outer_repeats'],
        random_state=cv_config['random_state'],
    )

    payloads = []
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
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=FutureWarning)
            search.fit(train_ready, y_train)

        train_score = search.predict_proba(train_ready)[:, 1]
        test_score = search.predict_proba(test_ready)[:, 1]

        train_fpr, train_tpr, _ = roc_curve(y_train, train_score)
        test_fpr, test_tpr, _ = roc_curve(y_test, test_score)

        payloads.append({
            'fold_index': fold_index,
            'train_fpr': train_fpr,
            'train_tpr': train_tpr,
            'test_fpr': test_fpr,
            'test_tpr': test_tpr,
            'train_auc': roc_auc_score(y_train, train_score),
            'test_auc': roc_auc_score(y_test, test_score),
            'n_features': len(selected_features),
        })
    return payloads


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


def make_single_panel(experiment_name: str):
    meta = MODEL_META[experiment_name]
    payloads = rerun_experiment(experiment_name)
    train_summary = mean_roc(payloads, 'train')
    test_summary = mean_roc(payloads, 'test')

    fig, ax = plt.subplots(figsize=(6.4, 5.4), facecolor='white')

    ax.plot(
        train_summary['grid'], train_summary['mean_tpr'],
        color=TRAIN_COLOR, linewidth=2.7,
        label=f'Training ROC (AUC = {train_summary["mean_auc"]:.3f})'
    )
    ax.plot(
        test_summary['grid'], test_summary['mean_tpr'],
        color=TEST_COLOR, linewidth=2.7,
        label=f'Outer-test ROC (AUC = {test_summary["mean_auc"]:.3f})'
    )
    ax.plot([0, 1], [0, 1], linestyle='--', color=REF_COLOR, linewidth=1.2)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title(meta['title'], fontsize=13, pad=10)
    ax.tick_params(labelsize=11)
    ax.grid(False)

    # put legend below to avoid overlap with curves
    ax.legend(
        frameon=False,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.16),
        ncol=1,
        fontsize=11,
        handlelength=2.6,
    )

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.23)

    png = OUT_DIR / f"20260311_ROC_{meta['short']}_publication.png"
    pdf = OUT_DIR / f"20260311_ROC_{meta['short']}_publication.pdf"
    fig.savefig(png, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return png, pdf, train_summary, test_summary


def make_contact_sheet(png_paths):
    import matplotlib.image as mpimg

    fig, axes = plt.subplots(3, 2, figsize=(12, 16), facecolor='white')
    axes = axes.flatten()
    for ax in axes:
        ax.axis('off')
    for ax, path in zip(axes, png_paths):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.axis('off')
    fig.suptitle('Visual inspection sheet for publication-style ROC figures', fontsize=14, y=0.995)
    plt.tight_layout()
    out = OUT_DIR / '20260311_ROC_publication_contact_sheet.png'
    fig.savefig(out, bbox_inches='tight', facecolor='white', dpi=220)
    plt.close(fig)
    return out


def main():
    pngs = []
    lines = ['# Publication-style ROC figures for all main models', '']
    for exp in MODEL_META:
        png, pdf, train_summary, test_summary = make_single_panel(exp)
        pngs.append(png)
        lines.extend([
            f"## {MODEL_META[exp]['title']}",
            f"- Training AUC: {train_summary['mean_auc']:.3f}",
            f"- Outer-test AUC: {test_summary['mean_auc']:.3f}",
            f"- PNG: `{png.name}`",
            f"- PDF: `{pdf.name}`",
            ''
        ])
    contact = make_contact_sheet(pngs)
    lines.extend([
        '## Visual inspection sheet',
        f"- Contact sheet: `{contact.name}`",
        '',
        'All legends are placed below the plotting area to minimize text overlap with the ROC curves.',
    ])
    (OUT_DIR / 'README_All_publication_ROC_figures.md').write_text('\n'.join(lines), encoding='utf-8')
    print('generated', len(pngs), 'figures')
    print('contact_sheet', contact)


if __name__ == '__main__':
    main()
