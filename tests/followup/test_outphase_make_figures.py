from pathlib import Path

import pandas as pd


def test_run_followup_figures_exports_outphase_figure_set(tmp_path):
    from src.followup.make_figures import run_followup_figures

    self_validation_summary = tmp_path / "self_validation_summary.csv"
    pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "repeated_random_holdout",
                "n_total_splits": 2,
                "n_completed": 2,
                "n_skipped": 0,
                "mean_auc": 0.55,
                "std_auc": 0.02,
                "mean_train_auc": 0.62,
                "mean_gap": 0.07,
                "mean_selected_feature_count": 5.0,
            }
        ]
    ).to_csv(self_validation_summary, index=False)

    self_validation_fold_metrics = tmp_path / "self_validation_fold_metrics.csv"
    pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "repeated_random_holdout",
                "split_id": "random_1",
                "holdout_group": "",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.55,
                "train_auc": 0.62,
                "selected_feature_count": 5,
                "n_train": 8,
                "n_test": 4,
            }
        ]
    ).to_csv(self_validation_fold_metrics, index=False)

    small_model_followup_comparison = tmp_path / "small_model_followup_comparison.csv"
    pd.DataFrame(
        [
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "strict_mean_auc": 0.53,
                "strict_std_auc": 0.06,
                "strict_mean_train_auc": 0.60,
                "strict_n_outer_folds": 5,
                "repeated_random_holdout_mean_auc": 0.55,
                "repeated_random_holdout_mean_gap": 0.07,
            }
        ]
    ).to_csv(small_model_followup_comparison, index=False)

    baseline_balance_summary = tmp_path / "baseline_balance_summary.csv"
    pd.DataFrame(
        [{"variable": "age_enroll", "response_mean": 10.5, "noresponse_mean": 10.4, "standardized_mean_difference": 0.07}]
    ).to_csv(baseline_balance_summary, index=False)

    group_definition_audit = tmp_path / "group_definition_audit.csv"
    pd.DataFrame(
        [{"record_type": "id_prefix_distribution", "key": "A", "value": 6, "note": "response_n=3, noresponse_n=3, response_rate=0.5000"}]
    ).to_csv(group_definition_audit, index=False)

    outphase_summary = tmp_path / "outphase_validation_summary.csv"
    pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_repeated_random_holdout",
                "train_phase": "baseline",
                "test_phase": "outphase",
                "n_total_splits": 2,
                "n_completed": 2,
                "n_skipped": 0,
                "mean_auc": 0.57,
                "std_auc": 0.03,
                "mean_train_auc": 0.62,
                "mean_gap": 0.05,
                "mean_selected_feature_count": 5.0,
            },
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_leave_one_prefix_out",
                "train_phase": "baseline",
                "test_phase": "outphase",
                "n_total_splits": 3,
                "n_completed": 2,
                "n_skipped": 1,
                "mean_auc": 0.54,
                "std_auc": 0.02,
                "mean_train_auc": 0.61,
                "mean_gap": 0.07,
                "mean_selected_feature_count": 5.0,
            },
        ]
    ).to_csv(outphase_summary, index=False)

    outphase_folds = tmp_path / "outphase_validation_fold_metrics.csv"
    pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_repeated_random_holdout",
                "split_id": "outphase_random_1",
                "holdout_group": "",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.58,
                "train_auc": 0.62,
                "selected_feature_count": 5,
                "n_train": 8,
                "n_test": 4,
                "train_phase": "baseline",
                "test_phase": "outphase",
            },
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_leave_one_prefix_out",
                "split_id": "outphase_prefix_A",
                "holdout_group": "A",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.54,
                "train_auc": 0.61,
                "selected_feature_count": 5,
                "n_train": 8,
                "n_test": 4,
                "train_phase": "baseline",
                "test_phase": "outphase",
            },
        ]
    ).to_csv(outphase_folds, index=False)

    result = run_followup_figures(
        self_validation_summary_path=self_validation_summary,
        self_validation_fold_metrics_path=self_validation_fold_metrics,
        small_model_comparison_path=small_model_followup_comparison,
        baseline_balance_summary_path=baseline_balance_summary,
        group_definition_audit_csv_path=group_definition_audit,
        output_dir=tmp_path,
        outphase_validation_summary_path=outphase_summary,
        outphase_validation_fold_metrics_path=outphase_folds,
    )

    expected_keys = {
        "followup_figure_outphase_model_performance_png",
        "followup_figure_outphase_model_performance_pdf",
        "followup_figure_outphase_distribution_png",
        "followup_figure_outphase_distribution_pdf",
    }
    assert expected_keys.issubset(result)
    for key in expected_keys:
        path = Path(result[key])
        assert path.exists()
        assert path.stat().st_size > 0


def test_outphase_distribution_labels_use_compact_scheme_names():
    from src.followup.make_figures import _format_distribution_tick_label

    label = _format_distribution_tick_label(
        "clinical_baseline_main",
        "outphase_leave_one_prefix_out",
    )

    assert label == "Clinical baseline\nOut-phase prefix proxy"
    assert "exploratory temporal proxy" not in label
    assert "(" not in label


def test_outphase_distribution_labels_use_compact_temporal_holdout_name():
    from src.followup.make_figures import _format_distribution_tick_label

    label = _format_distribution_tick_label(
        "clinical_baseline_main",
        "outphase_repeated_random_holdout",
    )

    assert label == "Clinical baseline\nOut-phase hold-out"
    assert "internal temporal" not in label


def test_outphase_distribution_plot_uses_compact_tick_labels(tmp_path, monkeypatch):
    from src.followup import make_figures

    outphase_folds = pd.DataFrame(
        [
            {
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_repeated_random_holdout",
                "status": "completed",
                "auc": 0.58,
                "train_auc": 0.62,
            },
            {
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_leave_one_prefix_out",
                "status": "completed",
                "auc": 0.54,
                "train_auc": 0.61,
            },
        ]
    )

    captured = {}

    def _fake_save(fig, output_dir, stem):
        captured["labels"] = [tick.get_text() for tick in fig.axes[0].get_xticklabels()]
        return {"png": str(tmp_path / f"{stem}.png"), "pdf": str(tmp_path / f"{stem}.pdf")}

    monkeypatch.setattr(make_figures, "_save_figure", _fake_save)

    make_figures._plot_outphase_distribution(outphase_folds, tmp_path)

    assert captured["labels"] == [
        "Clinical baseline\nOut-phase hold-out",
        "Clinical baseline\nOut-phase prefix proxy",
    ]



def test_outphase_distribution_labels_use_compact_school_holdout_name():
    from src.followup.make_figures import _format_distribution_tick_label

    label = _format_distribution_tick_label(
        "clinical_baseline_main",
        "outphase_leave_one_school_out",
    )

    assert label == "Clinical baseline\nOut-phase school hold-out"
    assert "(" not in label


def test_plot_outphase_model_performance_uses_school_columns_when_prefix_columns_absent(tmp_path, monkeypatch):
    from src.followup import make_figures

    summary = pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_repeated_random_holdout",
                "train_phase": "baseline",
                "test_phase": "outphase",
                "mean_auc": 0.57,
            },
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "outphase_leave_one_school_out",
                "train_phase": "baseline",
                "test_phase": "outphase",
                "mean_auc": 0.54,
            },
        ]
    )

    captured = {}

    def _fake_save(fig, output_dir, stem):
        legend = fig.axes[0].get_legend()
        captured["legend_labels"] = [text.get_text() for text in legend.get_texts()] if legend else []
        return {"png": str(tmp_path / f"{stem}.png"), "pdf": str(tmp_path / f"{stem}.pdf")}

    monkeypatch.setattr(make_figures, "_save_figure", _fake_save)

    make_figures._plot_outphase_model_performance(summary, tmp_path)

    assert captured["legend_labels"] == [
        "Out-phase hold-out\n(internal temporal)",
        "Out-phase school hold-out\n(internal temporal grouped)",
    ]
