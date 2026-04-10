from pathlib import Path

import pandas as pd


def _write_followup_inputs(tmp_path: Path) -> dict[str, Path]:
    self_validation_summary = tmp_path / "self_validation_summary.csv"
    pd.DataFrame(
        [
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "leave_one_prefix_out",
                "n_total_splits": 3,
                "n_completed": 3,
                "n_skipped": 0,
                "mean_auc": 0.52,
                "std_auc": 0.08,
                "mean_train_auc": 0.61,
                "mean_gap": 0.09,
                "mean_selected_feature_count": 5.0,
            },
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "repeated_random_holdout",
                "n_total_splits": 5,
                "n_completed": 5,
                "n_skipped": 0,
                "mean_auc": 0.55,
                "std_auc": 0.07,
                "mean_train_auc": 0.61,
                "mean_gap": 0.06,
                "mean_selected_feature_count": 5.0,
            },
            {
                "experiment": "lipid_elastic_net",
                "model_label": "ultra_sparse_lipid",
                "validation_scheme": "leave_one_prefix_out",
                "n_total_splits": 3,
                "n_completed": 3,
                "n_skipped": 0,
                "mean_auc": 0.53,
                "std_auc": 0.09,
                "mean_train_auc": 0.70,
                "mean_gap": 0.17,
                "mean_selected_feature_count": 5.0,
            },
            {
                "experiment": "lipid_elastic_net",
                "model_label": "ultra_sparse_lipid",
                "validation_scheme": "repeated_random_holdout",
                "n_total_splits": 5,
                "n_completed": 5,
                "n_skipped": 0,
                "mean_auc": 0.54,
                "std_auc": 0.06,
                "mean_train_auc": 0.68,
                "mean_gap": 0.14,
                "mean_selected_feature_count": 5.0,
            },
            {
                "experiment": "fusion_elastic_net",
                "model_label": "compact_fusion",
                "validation_scheme": "leave_one_prefix_out",
                "n_total_splits": 3,
                "n_completed": 3,
                "n_skipped": 0,
                "mean_auc": 0.51,
                "std_auc": 0.10,
                "mean_train_auc": 0.76,
                "mean_gap": 0.25,
                "mean_selected_feature_count": 20.0,
            },
            {
                "experiment": "fusion_elastic_net",
                "model_label": "compact_fusion",
                "validation_scheme": "repeated_random_holdout",
                "n_total_splits": 5,
                "n_completed": 5,
                "n_skipped": 0,
                "mean_auc": 0.57,
                "std_auc": 0.06,
                "mean_train_auc": 0.77,
                "mean_gap": 0.19,
                "mean_selected_feature_count": 20.0,
            },
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
                "auc": 0.51,
                "train_auc": 0.60,
                "selected_feature_count": 5,
                "n_train": 100,
                "n_test": 30,
            },
            {
                "experiment": "clinical_slim_logistic",
                "model_label": "clinical_baseline_main",
                "validation_scheme": "leave_one_prefix_out",
                "split_id": "prefix_A",
                "holdout_group": "A",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.54,
                "train_auc": 0.61,
                "selected_feature_count": 5,
                "n_train": 100,
                "n_test": 30,
            },
            {
                "experiment": "lipid_elastic_net",
                "model_label": "ultra_sparse_lipid",
                "validation_scheme": "repeated_random_holdout",
                "split_id": "random_1",
                "holdout_group": "",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.55,
                "train_auc": 0.69,
                "selected_feature_count": 5,
                "n_train": 100,
                "n_test": 30,
            },
            {
                "experiment": "lipid_elastic_net",
                "model_label": "ultra_sparse_lipid",
                "validation_scheme": "leave_one_prefix_out",
                "split_id": "prefix_A",
                "holdout_group": "A",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.52,
                "train_auc": 0.70,
                "selected_feature_count": 4,
                "n_train": 100,
                "n_test": 30,
            },
            {
                "experiment": "fusion_elastic_net",
                "model_label": "compact_fusion",
                "validation_scheme": "repeated_random_holdout",
                "split_id": "random_1",
                "holdout_group": "",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.58,
                "train_auc": 0.78,
                "selected_feature_count": 20,
                "n_train": 100,
                "n_test": 30,
            },
            {
                "experiment": "fusion_elastic_net",
                "model_label": "compact_fusion",
                "validation_scheme": "leave_one_prefix_out",
                "split_id": "prefix_A",
                "holdout_group": "A",
                "status": "completed",
                "skip_reason": "",
                "auc": 0.50,
                "train_auc": 0.75,
                "selected_feature_count": 19,
                "n_train": 100,
                "n_test": 30,
            },
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
                "strict_mean_train_auc": 0.61,
                "strict_n_outer_folds": 5,
                "leave_one_prefix_out_mean_auc": 0.52,
                "repeated_random_holdout_mean_auc": 0.55,
                "leave_one_prefix_out_mean_gap": 0.08,
                "repeated_random_holdout_mean_gap": 0.05,
            },
            {
                "model_label": "ultra_sparse_lipid",
                "experiment": "lipid_elastic_net",
                "strict_mean_auc": 0.53,
                "strict_std_auc": 0.07,
                "strict_mean_train_auc": 0.79,
                "strict_n_outer_folds": 5,
                "leave_one_prefix_out_mean_auc": 0.53,
                "repeated_random_holdout_mean_auc": 0.54,
                "leave_one_prefix_out_mean_gap": 0.17,
                "repeated_random_holdout_mean_gap": 0.14,
            },
            {
                "model_label": "compact_fusion",
                "experiment": "fusion_elastic_net",
                "strict_mean_auc": 0.54,
                "strict_std_auc": 0.05,
                "strict_mean_train_auc": 0.81,
                "strict_n_outer_folds": 5,
                "leave_one_prefix_out_mean_auc": 0.52,
                "repeated_random_holdout_mean_auc": 0.57,
                "leave_one_prefix_out_mean_gap": 0.24,
                "repeated_random_holdout_mean_gap": 0.19,
            },
        ]
    ).to_csv(small_model_followup_comparison, index=False)

    baseline_balance_summary = tmp_path / "baseline_balance_summary.csv"
    pd.DataFrame(
        [
            {"variable": "age_enroll", "response_mean": 10.5, "noresponse_mean": 10.4, "standardized_mean_difference": 0.07},
            {"variable": "bmi_z_enroll", "response_mean": 2.5, "noresponse_mean": 2.4, "standardized_mean_difference": 0.15},
            {"variable": "SFT", "response_mean": 1.7, "noresponse_mean": 1.8, "standardized_mean_difference": -0.24},
        ]
    ).to_csv(baseline_balance_summary, index=False)

    group_definition_audit = tmp_path / "group_definition_audit.csv"
    pd.DataFrame(
        [
            {"record_type": "id_prefix_distribution", "key": "A", "value": 12, "note": "response_n=7, noresponse_n=5, response_rate=0.5833"},
            {"record_type": "id_prefix_distribution", "key": "B", "value": 10, "note": "response_n=4, noresponse_n=6, response_rate=0.4000"},
            {"record_type": "blocker", "key": "blocker_1", "value": "缺少 endpoint_source", "note": "当前只完成可接入化，不生成伪敏感性结果。"},
        ]
    ).to_csv(group_definition_audit, index=False)

    discussion = tmp_path / "discussion.txt"
    discussion.write_text(
        "\n".join(
            [
                "先把 responder / non-responder 的定义和差异审清楚。",
                "模型优化更支持小模型、稀疏模型、稳定特征路线。",
                "可以先做 pseudo-external validation。",
                "out 的数据是不是也可以做验证。",
                "机制部分加一点心血管相关的表型。",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "self_validation_summary": self_validation_summary,
        "self_validation_fold_metrics": self_validation_fold_metrics,
        "small_model_followup_comparison": small_model_followup_comparison,
        "baseline_balance_summary": baseline_balance_summary,
        "group_definition_audit": group_definition_audit,
        "discussion": discussion,
    }


def test_run_followup_figures_exports_expected_files(tmp_path):
    from src.followup.make_figures import run_followup_figures

    inputs = _write_followup_inputs(tmp_path)
    result = run_followup_figures(
        self_validation_summary_path=inputs["self_validation_summary"],
        self_validation_fold_metrics_path=inputs["self_validation_fold_metrics"],
        small_model_comparison_path=inputs["small_model_followup_comparison"],
        baseline_balance_summary_path=inputs["baseline_balance_summary"],
        group_definition_audit_csv_path=inputs["group_definition_audit"],
        output_dir=tmp_path,
    )

    expected_keys = {
        "followup_figure_model_performance_png",
        "followup_figure_model_performance_pdf",
        "followup_figure_generalization_gap_png",
        "followup_figure_self_validation_distribution_png",
        "followup_figure_group_audit_png",
    }
    assert expected_keys.issubset(result)
    for key in expected_keys:
        path = Path(result[key])
        assert path.exists()
        assert path.stat().st_size > 0


def test_write_followup_alignment_note_maps_discussion_items(tmp_path):
    from src.followup.make_figures import write_followup_alignment_note

    inputs = _write_followup_inputs(tmp_path)
    output_path = write_followup_alignment_note(
        discussion_note_path=inputs["discussion"],
        output_dir=tmp_path,
    )

    text = Path(output_path).read_text(encoding="utf-8")
    assert "分组定义/差异先审清楚" in text
    assert "小模型、稀疏模型、稳定特征" in text
    assert "pseudo-external validation" in text
    assert "out 的数据做验证" in text
    assert "心血管相关表型" in text
    assert "已完成" in text
    assert "部分完成" in text
    assert "当前阻塞" in text



def test_distribution_labels_use_compact_school_holdout_name():
    from src.followup.make_figures import _format_distribution_tick_label

    label = _format_distribution_tick_label(
        "clinical_baseline_main",
        "leave_one_school_out",
    )

    assert label == "Clinical baseline\nSchool hold-out"
    assert "(" not in label


def test_plot_model_performance_uses_school_columns_when_prefix_columns_absent(tmp_path, monkeypatch):
    from src.followup import make_figures

    comparison = pd.DataFrame(
        [
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "strict_mean_auc": 0.53,
                "strict_mean_train_auc": 0.60,
                "repeated_random_holdout_mean_auc": 0.55,
                "leave_one_school_out_mean_auc": 0.52,
            }
        ]
    )

    captured = {}

    def _fake_save(fig, output_dir, stem):
        legend = fig.axes[0].get_legend()
        captured["legend_labels"] = [text.get_text() for text in legend.get_texts()] if legend else []
        return {"png": str(tmp_path / f"{stem}.png"), "pdf": str(tmp_path / f"{stem}.pdf")}

    monkeypatch.setattr(make_figures, "_save_figure", _fake_save)

    make_figures._plot_model_performance(comparison, tmp_path)

    assert captured["legend_labels"] == [
        "Strict nested CV",
        "Repeated hold-out",
        "School hold-out",
    ]
