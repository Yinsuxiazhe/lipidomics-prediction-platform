from __future__ import annotations

from pathlib import Path
import sys
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from plot_best_training_model_roc_english import (
    rerun_for_train_and_test_curves,
    mean_roc,
    TITLE_NAME,
    EXPERIMENT,
)

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0


def main() -> None:
    payloads = rerun_for_train_and_test_curves()
    train_summary = mean_roc(payloads, 'train')
    test_summary = mean_roc(payloads, 'test')

    fig, ax = plt.subplots(figsize=(6.4, 5.8), facecolor='white')

    ax.plot(
        train_summary['grid'],
        train_summary['mean_tpr'],
        color='#D94801',
        linewidth=2.8,
        label=f'Training ROC (AUC = {train_summary["mean_auc"]:.3f})',
    )
    ax.plot(
        test_summary['grid'],
        test_summary['mean_tpr'],
        color='#08519C',
        linewidth=2.8,
        label=f'Outer-test ROC (AUC = {test_summary["mean_auc"]:.3f})',
    )
    ax.plot([0, 1], [0, 1], linestyle='--', color='0.65', linewidth=1.2)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC curves of the highest-training-AUC model', fontsize=13, pad=10)

    ax.legend(frameon=False, loc='lower right', fontsize=11)
    ax.grid(False)
    ax.tick_params(labelsize=11)

    # Compact caption-style model note inside the panel
    ax.text(
        0.03,
        0.06,
        f'Model: {TITLE_NAME} ({EXPERIMENT})',
        transform=ax.transAxes,
        fontsize=9.8,
        color='0.25',
    )

    plt.tight_layout()

    png = HERE / '20260311_BestTrainingModel_English_ROC_singlepanel_publication.png'
    pdf = HERE / '20260311_BestTrainingModel_English_ROC_singlepanel_publication.pdf'
    fig.savefig(png, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    readme = HERE / 'README_English_ROC_singlepanel_publication.md'
    readme.write_text(
        '\n'.join([
            '# Publication-style single-panel English ROC figure',
            '',
            'This figure is a simplified single-panel English ROC figure intended for supplementary materials or cleaner presentation slides.',
            '',
            f'- Model: {TITLE_NAME} ({EXPERIMENT})',
            f'- Training AUC: {train_summary["mean_auc"]:.3f}',
            f'- Outer-test AUC: {test_summary["mean_auc"]:.3f}',
            '',
            'The figure intentionally keeps only:',
            '1. Training ROC',
            '2. Outer-test ROC',
            '3. AUC values',
            '',
            'It is suitable when you want a cleaner training-focused figure, but it should still be interpreted together with the outer-test ROC.',
        ]),
        encoding='utf-8'
    )

    print('saved:', png)
    print('saved:', pdf)


if __name__ == '__main__':
    main()
