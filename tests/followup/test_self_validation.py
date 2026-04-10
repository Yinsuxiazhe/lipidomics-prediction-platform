from pathlib import Path

import warnings

import numpy as np
import pandas as pd


def test_run_self_validation_exports_unified_schema_and_skip_reason(tmp_path):
    from src.data.build_cohort import AnalysisCohorts
    from src.followup.self_validation import run_self_validation

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

    result = run_self_validation(
        cohorts=cohorts,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        self_validation_config={
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

    folds = pd.read_csv(result["self_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["self_validation_summary_csv"])

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
    }.issubset(folds.columns)
    assert set(summary["validation_scheme"]) == {"repeated_random_holdout", "leave_one_prefix_out"}
    assert "skipped_single_class_test" in set(folds["status"])
    skipped_row = folds.loc[folds["status"] == "skipped_single_class_test"].iloc[0]
    assert skipped_row["skip_reason"]


def test_fit_and_score_split_suppresses_penalty_futurewarning(monkeypatch):
    from src.followup import self_validation as module

    frame = pd.DataFrame(
        {
            "ID": ["A001", "A002", "A003", "B001", "B002", "B003"],
            "Group": ["response", "response", "noresponse", "response", "noresponse", "noresponse"],
            "age_enroll": [10, 11, 12, 10, 11, 12],
            "BMI": [28.1, 29.0, 20.2, 27.9, 20.4, 21.1],
        }
    )

    class DummySpec:
        model_family = "clinical_slim_logistic"

    monkeypatch.setattr(
        module,
        "_prepare_experiment_features",
        lambda **kwargs: (
            kwargs["train_frame"].to_numpy(),
            kwargs["test_frame"].to_numpy(),
            ["age_enroll", "BMI"],
        ),
    )
    monkeypatch.setattr(module, "_build_estimator", lambda model_family: (object(), {}))

    class FakeGridSearchCV:
        def __init__(self, *args, **kwargs):
            self.best_params_ = {}

        def fit(self, X, y):
            warnings.warn(
                "'penalty' was deprecated in version 1.5 and will be removed in 1.7.",
                FutureWarning,
            )
            return self

        def predict_proba(self, X):
            return np.tile(np.array([[0.4, 0.6]]), (len(X), 1))

    monkeypatch.setattr(module, "GridSearchCV", FakeGridSearchCV)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        row = module._fit_and_score_split(
            frame=frame,
            spec=DummySpec(),
            experiment="clinical_slim_logistic",
            model_label="clinical_baseline_main",
            positive_label="response",
            cv_config={
                "inner_splits": 2,
                "random_state": 42,
                "lipid_top_k": 2,
                "clinical_top_k": 5,
                "correlation_threshold": 0.95,
                "clinical_missing_threshold": 0.2,
            },
            validation_scheme="repeated_random_holdout",
            split_id="random_holdout_1",
            holdout_group=None,
            train_idx=np.array([0, 1, 4, 5]),
            test_idx=np.array([2, 3]),
        )

    penalty_warnings = [
        item
        for item in caught
        if issubclass(item.category, FutureWarning) and "'penalty' was deprecated" in str(item.message)
    ]

    assert row["status"] == "completed"
    assert not penalty_warnings



def test_run_self_validation_supports_leave_one_school_out_and_exports_mapping(tmp_path):
    from src.data.build_cohort import AnalysisCohorts
    from src.followup.self_validation import run_self_validation

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
    clinical_full = clinical_slim.assign(whole_blood_LYMPH_count=[3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1])
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

    result = run_self_validation(
        cohorts=cohorts,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        self_validation_config={
            "random_holdout_splits": 2,
            "test_size": 0.25,
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

    folds = pd.read_csv(result["self_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["self_validation_summary_csv"])
    mapping_csv = Path(result["group_mapping_csv"])

    assert set(summary["validation_scheme"]) == {"repeated_random_holdout", "leave_one_school_out"}
    school_rows = folds.loc[folds["validation_scheme"] == "leave_one_school_out"]
    assert set(school_rows["holdout_group"]) == {"百旺", "本部", "华清校区"}
    assert mapping_csv.exists()
    assert mapping_csv.name == "id_school_intensity_mapping.csv"
    mapping_export = pd.read_csv(mapping_csv)
    assert set(mapping_export.columns) == {"ID", "school", "intensity"}


def test_run_self_validation_supports_fixed_school_combo_holdout(tmp_path):
    from src.data.build_cohort import AnalysisCohorts
    from src.followup.self_validation import run_self_validation

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
    clinical_full = clinical_slim.assign(whole_blood_LYMPH_count=[3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1, 3.0, 3.1, 1.0, 1.1])
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

    result = run_self_validation(
        cohorts=cohorts,
        positive_label="response",
        output_dir=tmp_path,
        model_configs=[
            {
                "model_label": "clinical_baseline_main",
                "experiment": "clinical_slim_logistic",
                "cv_overrides": {},
            }
        ],
        self_validation_config={
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

    folds = pd.read_csv(result["self_validation_fold_metrics_csv"])
    summary = pd.read_csv(result["self_validation_summary_csv"])

    assert set(summary["validation_scheme"]) == {
        "repeated_random_holdout",
        "leave_one_school_out",
        "fixed_school_combo_holdout",
    }
    fixed_rows = folds.loc[folds["validation_scheme"] == "fixed_school_combo_holdout"]
    assert len(fixed_rows) == 1
    fixed_row = fixed_rows.iloc[0]
    assert fixed_row["holdout_group"] == "百旺 + 本部"
    assert fixed_row["n_train"] == 4
    assert fixed_row["n_test"] == 8
