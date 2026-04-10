from pathlib import Path

import pandas as pd


def _build_baseline_cohorts():
    from src.data.build_cohort import AnalysisCohorts

    ids = ["A001", "A002", "A003", "B001", "B002", "C001"]
    groups = ["response", "response", "noresponse", "response", "response", "noresponse"]

    clinical_slim = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "age_enroll": [10, 10, 10, 11, 11, 11],
            "bmi_z_enroll": [3.0, 3.1, 1.0, 2.9, 3.2, 1.1],
            "SFT": [1.0, 1.1, 3.0, 1.1, 1.0, 3.1],
            "Gender": [0, 1, 0, 1, 0, 1],
            "BMI": [28.0, 29.0, 20.0, 27.5, 28.5, 21.0],
        }
    )
    clinical_full = clinical_slim.assign(whole_blood_LYMPH_count=[3.0, 3.1, 1.0, 3.2, 3.0, 1.1])
    group_lipid = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "NAME": ids,
            "lipid_signal": [10.0, 10.2, 0.1, 9.8, 10.1, 0.2],
            "lipid_shadow": [9.9, 10.0, 0.2, 9.7, 10.3, 0.1],
        }
    )
    group_fusion = clinical_slim.merge(group_lipid.drop(columns=["NAME", "Group"]), on="ID", how="inner")
    group_fusion_full = clinical_full.merge(group_lipid.drop(columns=["NAME", "Group"]), on="ID", how="inner")
    cohorts = AnalysisCohorts(
        group_lipid=group_lipid,
        group_clinical_slim=clinical_slim,
        group_clinical_full=clinical_full,
        group_fusion=group_fusion,
        group_fusion_full=group_fusion_full,
        summary={"overlap_id_count": len(ids)},
    )
    group = clinical_slim[["ID", "Group"]].copy()
    return cohorts, group


def _write_outphase_inputs(tmp_path: Path) -> dict[str, Path]:
    ids = ["A001", "A002", "A003", "B001", "B002", "C001"]
    flipped_groups = ["noresponse", "noresponse", "response", "noresponse", "noresponse", "response"]

    out_lipid_path = tmp_path / "out_lipid.csv"
    pd.DataFrame(
        {
            "NAME": ids,
            "Group": flipped_groups,
            "lipid_signal": [9.7, 9.9, 0.3, 9.5, 9.8, 0.4],
            "lipid_shadow": [9.8, 9.9, 0.4, 9.4, 10.0, 0.3],
        }
    ).to_csv(out_lipid_path, index=False)

    out_clinical_path = tmp_path / "out_clinical.csv"
    pd.DataFrame(
        {
            "ID": ids,
            "age_out": [10.2, 10.1, 10.0, 11.2, 11.1, 11.0],
            "bmi_z_out": [2.8, 3.0, 1.1, 2.7, 3.1, 1.0],
            "SFT": [1.2, 1.1, 2.8, 1.2, 1.0, 3.0],
            "Gender": [0, 1, 0, 1, 0, 1],
            "BMI": [27.5, 28.6, 20.2, 27.0, 28.1, 21.1],
            "whole_blood_LYMPH_count": [2.9, 3.0, 1.2, 3.0, 3.1, 1.0],
        }
    ).to_csv(out_clinical_path, index=False)
    return {
        "out_lipid": out_lipid_path,
        "out_clinical": out_clinical_path,
    }


def test_build_outphase_analysis_cohorts_uses_master_group_labels(tmp_path):
    from src.followup.outphase_validation import build_outphase_analysis_cohorts

    cohorts, group = _build_baseline_cohorts()
    out_inputs = _write_outphase_inputs(tmp_path)

    outphase_cohorts, metadata = build_outphase_analysis_cohorts(
        group_frame=group,
        out_lipid_path=out_inputs["out_lipid"],
        out_clinical_full_path=out_inputs["out_clinical"],
        clinical_anchor_mapping={
            "age_enroll": "age_out",
            "bmi_z_enroll": "bmi_z_out",
            "SFT": "SFT",
            "Gender": "Gender",
            "BMI": "BMI",
        },
    )

    _ = cohorts
    aligned = outphase_cohorts.group_lipid.sort_values("ID").reset_index(drop=True)
    master = group.sort_values("ID").reset_index(drop=True)

    assert list(aligned["Group"]) == list(master["Group"])
    assert {"age_enroll", "bmi_z_enroll", "SFT", "Gender", "BMI"}.issubset(
        outphase_cohorts.group_clinical_slim.columns
    )
    assert metadata["overlap_id_count"] == 6
    assert metadata["out_lipid_group_match_rate"] == 0.0


def test_run_outphase_validation_exports_unified_schema_and_skip_reason(tmp_path):
    from src.followup.outphase_validation import run_outphase_validation

    cohorts, group = _build_baseline_cohorts()
    out_inputs = _write_outphase_inputs(tmp_path)

    result = run_outphase_validation(
        cohorts=cohorts,
        group_frame=group,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        outphase_config={
            "enabled": True,
            "out_lipid_path": str(out_inputs["out_lipid"]),
            "out_clinical_full_path": str(out_inputs["out_clinical"]),
            "clinical_anchor_mapping": {
                "age_enroll": "age_out",
                "bmi_z_enroll": "bmi_z_out",
                "SFT": "SFT",
                "Gender": "Gender",
                "BMI": "BMI",
            },
            "random_holdout_splits": 2,
            "test_size": 0.33,
            "random_state": 7,
            "pseudo_external": {"enabled": True, "group_by": "id_prefix"},
            "cv_config": {
                "outer_splits": 3,
                "outer_repeats": 1,
                "inner_splits": 2,
                "random_state": 42,
                "lipid_top_k": 2,
                "clinical_top_k": 5,
                "correlation_threshold": 0.95,
                "clinical_missing_threshold": 0.2,
            },
        },
    )

    folds = pd.read_csv(result["outphase_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["outphase_validation_summary_csv"])
    report_text = Path(result["outphase_validation_markdown"]).read_text(encoding="utf-8")

    assert {
        "experiment",
        "model_label",
        "validation_scheme",
        "split_id",
        "status",
        "auc",
        "train_auc",
        "selected_feature_count",
        "skip_reason",
        "train_phase",
        "test_phase",
    }.issubset(folds.columns)
    assert set(summary["validation_scheme"]) == {
        "outphase_leave_one_prefix_out",
        "outphase_repeated_random_holdout",
    }
    assert set(summary["test_phase"]) == {"outphase"}
    assert "skipped_single_class_test" in set(folds["status"])
    skipped_row = folds.loc[folds["status"] == "skipped_single_class_test"].iloc[0]
    assert skipped_row["skip_reason"]
    assert "内部时相验证" in report_text
    assert "不是外部验证" in report_text



def test_run_outphase_validation_supports_leave_one_school_out(tmp_path):
    from src.followup.outphase_validation import run_outphase_validation

    cohorts, group = _build_baseline_cohorts()
    out_inputs = _write_outphase_inputs(tmp_path)

    mapping_path = tmp_path / "mapping.xlsx"
    mapping = pd.DataFrame(
        {
            "school": ["百旺", "百旺", "本部", "本部", "华清校区", "华清校区"],
            "ID": ["A001", "A002", "A003", "B001", "B002", "C001"],
            "intensity": [
                "Intermittent vigorous",
                "Intermittent vigorous",
                "Low-intensity",
                "Low-intensity",
                "Intermittent vigorous",
                "Intermittent vigorous",
            ],
        }
    )
    with pd.ExcelWriter(mapping_path, engine="openpyxl") as writer:
        mapping.to_excel(writer, sheet_name="运动强度分组_401人", index=False)

    result = run_outphase_validation(
        cohorts=cohorts,
        group_frame=group,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        outphase_config={
            "enabled": True,
            "out_lipid_path": str(out_inputs["out_lipid"]),
            "out_clinical_full_path": str(out_inputs["out_clinical"]),
            "clinical_anchor_mapping": {
                "age_enroll": "age_out",
                "bmi_z_enroll": "bmi_z_out",
                "SFT": "SFT",
                "Gender": "Gender",
                "BMI": "BMI",
            },
            "random_holdout_splits": 2,
            "test_size": 0.33,
            "random_state": 7,
            "pseudo_external": {
                "enabled": True,
                "group_by": "school",
                "mapping_path": str(mapping_path),
                "mapping_sheet_name": "运动强度分组_401人",
            },
            "cv_config": {
                "outer_splits": 3,
                "outer_repeats": 1,
                "inner_splits": 2,
                "random_state": 42,
                "lipid_top_k": 2,
                "clinical_top_k": 5,
                "correlation_threshold": 0.95,
                "clinical_missing_threshold": 0.2,
            },
        },
    )

    folds = pd.read_csv(result["outphase_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["outphase_validation_summary_csv"])
    report_text = Path(result["outphase_validation_markdown"]).read_text(encoding="utf-8")

    assert set(summary["validation_scheme"]) == {
        "outphase_leave_one_school_out",
        "outphase_repeated_random_holdout",
    }
    school_rows = folds.loc[folds["validation_scheme"] == "outphase_leave_one_school_out"]
    assert set(school_rows["holdout_group"]) == {"百旺", "本部", "华清校区"}
    assert "school grouped split" in report_text
    assert "不是外部验证" in report_text


def test_run_outphase_validation_supports_fixed_school_combo_holdout(tmp_path):
    from src.data.build_cohort import AnalysisCohorts
    from src.followup.outphase_validation import run_outphase_validation

    ids = [
        "A001", "A002", "A003", "A004",
        "B001", "B002", "B003", "B004",
        "C001", "C002", "C003", "C004",
    ]
    groups = [
        "response", "response", "noresponse", "noresponse",
        "response", "response", "noresponse", "noresponse",
        "response", "response", "noresponse", "noresponse",
    ]
    clinical_slim = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "age_enroll": [10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11],
            "bmi_z_enroll": [3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1],
            "SFT": [1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1],
            "Gender": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            "BMI": [28.0, 29.0, 20.0, 21.0, 28.0, 29.0, 20.0, 21.0, 28.0, 29.0, 20.0, 21.0],
        }
    )
    clinical_full = clinical_slim.assign(
        whole_blood_LYMPH_count=[3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1]
    )
    group_lipid = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "NAME": ids,
            "lipid_signal": [10.0, 10.1, 0.1, 0.2, 10.0, 10.1, 0.1, 0.2, 10.0, 10.1, 0.1, 0.2],
            "lipid_shadow": [9.9, 10.0, 0.2, 0.1, 9.9, 10.0, 0.2, 0.1, 9.9, 10.0, 0.2, 0.1],
        }
    )
    group_fusion = clinical_slim.merge(group_lipid.drop(columns=["NAME", "Group"]), on="ID", how="inner")
    group_fusion_full = clinical_full.merge(group_lipid.drop(columns=["NAME", "Group"]), on="ID", how="inner")
    cohorts = AnalysisCohorts(
        group_lipid=group_lipid,
        group_clinical_slim=clinical_slim,
        group_clinical_full=clinical_full,
        group_fusion=group_fusion,
        group_fusion_full=group_fusion_full,
        summary={"overlap_id_count": len(ids)},
    )
    group = clinical_slim[["ID", "Group"]].copy()

    out_lipid_path = tmp_path / "out_lipid.csv"
    pd.DataFrame(
        {
            "NAME": ids,
            "Group": groups,
            "lipid_signal": [9.7, 9.8, 0.4, 0.5, 9.6, 9.7, 0.3, 0.4, 9.7, 9.8, 0.4, 0.5],
            "lipid_shadow": [9.8, 9.9, 0.3, 0.4, 9.7, 9.8, 0.2, 0.3, 9.8, 9.9, 0.3, 0.4],
        }
    ).to_csv(out_lipid_path, index=False)

    out_clinical_path = tmp_path / "out_clinical.csv"
    pd.DataFrame(
        {
            "ID": ids,
            "age_out": [10.1, 11.1, 10.0, 11.0, 10.1, 11.1, 10.0, 11.0, 10.1, 11.1, 10.0, 11.0],
            "bmi_z_out": [2.9, 3.0, 1.1, 1.2, 2.9, 3.0, 1.1, 1.2, 2.9, 3.0, 1.1, 1.2],
            "SFT": [1.1, 1.2, 2.9, 3.0, 1.1, 1.2, 2.9, 3.0, 1.1, 1.2, 2.9, 3.0],
            "Gender": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            "BMI": [27.7, 28.7, 20.1, 21.1, 27.7, 28.7, 20.1, 21.1, 27.7, 28.7, 20.1, 21.1],
            "whole_blood_LYMPH_count": [2.9, 3.0, 1.2, 1.3, 2.9, 3.0, 1.2, 1.3, 2.9, 3.0, 1.2, 1.3],
        }
    ).to_csv(out_clinical_path, index=False)

    mapping_path = tmp_path / "mapping.xlsx"
    mapping = pd.DataFrame(
        {
            "school": ["百旺"] * 4 + ["本部"] * 4 + ["华清校区"] * 4,
            "ID": ids,
            "intensity": ["Intermittent vigorous"] * 4 + ["Low-intensity"] * 4 + ["Intermittent vigorous"] * 4,
        }
    )
    with pd.ExcelWriter(mapping_path, engine="openpyxl") as writer:
        mapping.to_excel(writer, sheet_name="运动强度分组_401人", index=False)

    result = run_outphase_validation(
        cohorts=cohorts,
        group_frame=group,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        outphase_config={
            "enabled": True,
            "out_lipid_path": str(out_lipid_path),
            "out_clinical_full_path": str(out_clinical_path),
            "clinical_anchor_mapping": {
                "age_enroll": "age_out",
                "bmi_z_enroll": "bmi_z_out",
                "SFT": "SFT",
                "Gender": "Gender",
                "BMI": "BMI",
            },
            "random_holdout_splits": 2,
            "test_size": 0.25,
            "random_state": 7,
            "pseudo_external": {
                "enabled": True,
                "group_by": "school",
                "mapping_path": str(mapping_path),
                "mapping_sheet_name": "运动强度分组_401人",
                "fixed_group_split": {
                    "enabled": True,
                    "test_groups": ["百旺", "本部"],
                },
            },
            "cv_config": {
                "outer_splits": 3,
                "outer_repeats": 1,
                "inner_splits": 2,
                "random_state": 42,
                "lipid_top_k": 2,
                "clinical_top_k": 5,
                "correlation_threshold": 0.95,
                "clinical_missing_threshold": 0.2,
            },
        },
    )

    folds = pd.read_csv(result["outphase_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["outphase_validation_summary_csv"])
    report_text = Path(result["outphase_validation_markdown"]).read_text(encoding="utf-8")

    assert set(summary["validation_scheme"]) == {
        "outphase_leave_one_school_out",
        "outphase_repeated_random_holdout",
        "outphase_fixed_school_combo_holdout",
    }
    fixed_rows = folds.loc[folds["validation_scheme"] == "outphase_fixed_school_combo_holdout"]
    assert len(fixed_rows) == 1
    fixed_row = fixed_rows.iloc[0]
    assert fixed_row["holdout_group"] == "百旺 + 本部"
    assert fixed_row["n_train"] == 4
    assert fixed_row["n_test"] == 8
    assert "不是外部验证" in report_text
