import pandas as pd

from src.multi_indicator_glm5 import multi_type_assets as mta


def test_align_multi_type_inputs_uses_lipid_intersection_for_fair_comparison():
    enroll = pd.DataFrame(
        {
            "ID": ["1", "2", "3"],
            "age_enroll": [10, 11, 12],
            "Gender": [0, 1, 0],
            "BMI": [20.1, 21.2, 22.3],
            "bmi_z_enroll": [0.1, 0.2, 0.3],
            "SFT": [5.0, 6.0, 7.0],
        }
    )
    lipid = pd.DataFrame(
        {
            "NAME": ["2", "3", "4"],
            "LIPID_A": [0.2, 0.3, 0.4],
            "LIPID_B": [1.2, 1.3, 1.4],
        }
    )
    labels = pd.DataFrame(
        {
            "ID": ["1", "2", "3", "4"],
            "BMI_Q": [1, 0, 1, 0],
            "BMI_T": [1, 0, 1, 0],
        }
    )

    aligned = mta.align_multi_type_inputs(enroll, lipid, labels)

    assert aligned["ID"].tolist() == ["2", "3"]
    assert "LIPID_A" in aligned.columns
    assert "age_enroll" in aligned.columns
    assert "BMI_Q" in aligned.columns


def test_build_feature_spaces_separates_clinical_lipid_and_fusion_features():
    aligned = pd.DataFrame(
        {
            "ID": ["2", "3"],
            "age_enroll": [11, 12],
            "Gender": [1, 0],
            "BMI": [21.2, 22.3],
            "bmi_z_enroll": [0.2, 0.3],
            "SFT": [6.0, 7.0],
            "LIPID_A": [0.2, 0.3],
            "LIPID_B": [1.2, 1.3],
        }
    )

    spaces = mta.build_feature_spaces(aligned, lipid_features=["LIPID_A", "LIPID_B"])

    assert spaces["clinical"]["features"] == mta.DEFAULT_CLINICAL_FEATURES
    assert spaces["lipid"]["features"] == ["LIPID_A", "LIPID_B"]
    assert spaces["fusion"]["features"] == mta.DEFAULT_CLINICAL_FEATURES + ["LIPID_A", "LIPID_B"]
    assert list(spaces["fusion"]["X"].columns) == mta.DEFAULT_CLINICAL_FEATURES + ["LIPID_A", "LIPID_B"]


def test_select_best_models_marks_one_best_row_per_indicator_cutoff_and_type():
    df = pd.DataFrame(
        [
            {"indicator": "BMI", "cutoff": "Q", "model_type": "clinical", "model": "EN_LR", "mean_auroc": 0.70, "mean_auprc": 0.60, "mean_sensitivity": 0.60, "mean_specificity": 0.60},
            {"indicator": "BMI", "cutoff": "Q", "model_type": "clinical", "model": "RF", "mean_auroc": 0.72, "mean_auprc": 0.58, "mean_sensitivity": 0.61, "mean_specificity": 0.62},
            {"indicator": "BMI", "cutoff": "Q", "model_type": "lipid", "model": "XGBoost", "mean_auroc": 0.80, "mean_auprc": 0.77, "mean_sensitivity": 0.70, "mean_specificity": 0.73},
            {"indicator": "BMI", "cutoff": "Q", "model_type": "lipid", "model": "LR_L2", "mean_auroc": 0.78, "mean_auprc": 0.79, "mean_sensitivity": 0.75, "mean_specificity": 0.70},
        ]
    )

    ranked = mta.select_best_models(df)

    clinical = ranked[(ranked["indicator"] == "BMI") & (ranked["cutoff"] == "Q") & (ranked["model_type"] == "clinical")]
    lipid = ranked[(ranked["indicator"] == "BMI") & (ranked["cutoff"] == "Q") & (ranked["model_type"] == "lipid")]

    assert clinical["is_best_within_type"].sum() == 1
    assert lipid["is_best_within_type"].sum() == 1
    assert clinical.loc[clinical["model"] == "RF", "is_best_within_type"].item() is True
    assert lipid.loc[lipid["model"] == "XGBoost", "is_best_within_type"].item() is True


def test_select_best_models_uses_auprc_then_model_simplicity_as_tiebreakers():
    df = pd.DataFrame(
        [
            {"indicator": "BMI", "cutoff": "Q", "model_type": "fusion", "model": "XGBoost", "mean_auroc": 0.81, "mean_auprc": 0.70, "mean_sensitivity": 0.68, "mean_specificity": 0.69},
            {"indicator": "BMI", "cutoff": "Q", "model_type": "fusion", "model": "EN_LR", "mean_auroc": 0.81, "mean_auprc": 0.74, "mean_sensitivity": 0.66, "mean_specificity": 0.69},
            {"indicator": "BMI", "cutoff": "Q", "model_type": "fusion", "model": "LR_L2", "mean_auroc": 0.81, "mean_auprc": 0.74, "mean_sensitivity": 0.66, "mean_specificity": 0.69},
        ]
    )

    ranked = mta.select_best_models(df)
    best = ranked.loc[ranked["is_best_within_type"], "model"].tolist()

    assert best == ["LR_L2"]


def test_build_input_schema_tags_clinical_and_lipid_fields():
    schema = mta.build_input_schema(
        clinical_features=["age_enroll", "BMI"],
        lipid_features=["LIPID_A"],
    )

    assert schema == [
        {"name": "age_enroll", "section": "clinical", "required": True},
        {"name": "BMI", "section": "clinical", "required": True},
        {"name": "LIPID_A", "section": "lipid", "required": True},
    ]


def test_compute_calibration_curve_payload_reports_brier_and_points():
    payload = mta.compute_calibration_curve_payload([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], n_bins=2)

    assert payload["brier"] >= 0
    assert len(payload["points"]) == 2
    assert set(payload["points"][0]) == {"bin", "mean_pred", "obs_rate", "count"}


def test_evaluate_cross_gender_transfer_returns_directional_metrics_for_both_splits():
    X = pd.DataFrame(
        {
            "feature_a": [
                -3.0, -2.5, -2.0, -1.5, -1.0, -0.5,
                 0.5,  1.0,  1.5,  2.0,  2.5,  3.0,
                -3.2, -2.7, -2.2, -1.7, -1.2, -0.7,
                 0.7,  1.2,  1.7,  2.2,  2.7,  3.2,
            ],
            "feature_b": [
                -2.4, -2.0, -1.6, -1.2, -0.8, -0.4,
                 0.4,  0.8,  1.2,  1.6,  2.0,  2.4,
                -2.6, -2.1, -1.7, -1.3, -0.9, -0.5,
                 0.5,  0.9,  1.3,  1.7,  2.1,  2.6,
            ],
        }
    )
    y = pd.Series(
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1] * 2,
        dtype=int,
    )
    gender = pd.Series([0] * 12 + [1] * 12, dtype=int)

    metrics = mta.evaluate_cross_gender_transfer(
        X=X,
        y=y,
        gender=gender,
        model_template=mta.get_models()["LR_L2"],
        min_group_size=10,
    )

    assert metrics["m2f_auroc"] > 0.95
    assert metrics["f2m_auroc"] > 0.95
    assert metrics["cross_avg_auroc"] > 0.95
    assert metrics["m2f_n_train"] == 12
    assert metrics["f2m_n_test"] == 12


def test_build_metadata_entry_includes_schema_sample_values_and_curves():
    row = {
        "indicator": "BMI",
        "cutoff": "Q",
        "model_type": "fusion",
        "model": "EN_LR",
        "mean_auroc": 0.81,
        "mean_auprc": 0.75,
        "mean_sensitivity": 0.70,
        "mean_specificity": 0.72,
        "m2f_auroc": 0.66,
        "f2m_auroc": 0.64,
        "cross_avg_auroc": 0.65,
        "is_best_within_type": True,
        "is_best_overall": True,
    }
    entry = mta.build_metadata_entry(
        model_key="BMI_Q_fusion_EN_LR",
        result_row=row,
        clinical_features=["age_enroll", "BMI"],
        lipid_features=["LIPID_A"],
        sample_values={"age_enroll": 11.2, "BMI": 23.4, "LIPID_A": 0.56},
        calibration={"points": [{"bin": 0, "mean_pred": 0.2, "obs_rate": 0.1, "count": 5}], "brier": 0.12},
        dca={"model": [{"threshold": 0.2, "net_benefit": 0.1}], "treat_all": [], "treat_none": []},
    )

    assert entry["model_type"] == "fusion"
    assert entry["clinical_features"] == ["age_enroll", "BMI"]
    assert entry["lipid_features"] == ["LIPID_A"]
    assert entry["input_schema"][0]["section"] == "clinical"
    assert entry["input_schema"][-1]["section"] == "lipid"
    assert entry["sample_values"]["LIPID_A"] == 0.56
    assert entry["calibration"]["brier"] == 0.12
    assert entry["dca"]["model"][0]["threshold"] == 0.2
    assert entry["performance"]["m2f_auroc"] == 0.66
    assert entry["performance"]["f2m_auroc"] == 0.64
    assert entry["performance"]["cross_avg_auroc"] == 0.65


def test_safe_feature_means_uses_discrete_mode_for_gender():
    frame = pd.DataFrame(
        {
            "Gender": [0, 1, 0, 0, 1],
            "BMI": [20.0, 21.0, 22.0, 23.0, 24.0],
        }
    )

    sample_values = mta._safe_feature_means(frame, ["Gender", "BMI"])

    assert sample_values["Gender"] == 0
    assert sample_values["BMI"] == 22.0
