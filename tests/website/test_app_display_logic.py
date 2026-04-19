import warnings

warnings.filterwarnings(
    "ignore",
    message="Trying to unpickle estimator",
)

import json
import pickle

import pytest

import website.app as app_module


class DummyModel:
    def __init__(self, pred, proba):
        self._pred = pred
        self._proba = proba

    def predict(self, X):
        return [self._pred]

    def predict_proba(self, X):
        return [self._proba]


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def install_dummy_model(
    monkeypatch,
    key,
    *,
    indicator,
    direction,
    pred,
    proba=(0.2, 0.8),
    group="q4",
    model_name="RF",
    model_type="lipid",
    clinical_features=None,
    lipid_features=None,
    is_best_within_type=False,
    is_best_overall=False,
):
    clinical_features = clinical_features or []
    lipid_features = lipid_features or ["LIPID_A"]
    features = clinical_features + lipid_features
    input_schema = [
        {"name": feature, "section": "clinical", "required": True}
        for feature in clinical_features
    ] + [
        {"name": feature, "section": "lipid", "required": True}
        for feature in lipid_features
    ]

    models = dict(app_module._models)
    info = dict(app_module._model_info)
    models[key] = {
        "model": DummyModel(pred=pred, proba=proba),
        "features": features,
        "clinical_features": clinical_features,
        "lipid_features": lipid_features,
        "indicator": indicator,
        "group": group,
        "model_name": model_name,
        "model_type": model_type,
        "direction": direction,
        "input_schema": input_schema,
        "is_best_within_type": is_best_within_type,
        "is_best_overall": is_best_overall,
    }
    info[key] = {
        "indicator": indicator,
        "indicator_cn": indicator,
        "group": group,
        "group_cn": "四分位",
        "model_name": model_name,
        "model_type": model_type,
        "direction": direction,
        "features": features,
        "clinical_features": clinical_features,
        "lipid_features": lipid_features,
        "input_schema": input_schema,
        "is_best_within_type": is_best_within_type,
        "is_best_overall": is_best_overall,
    }
    monkeypatch.setattr(app_module, "_models", models)
    monkeypatch.setattr(app_module, "_model_info", info)


def test_api_models_exposes_delta_indicator_and_explicit_grouping(client):
    response = client.get("/api/models")
    assert response.status_code == 200

    payload = response.get_json()
    bmi_model = payload["models"]["BMI_Q_lipid_RF"]

    assert bmi_model["indicator_display"] == "ΔBMI"
    assert bmi_model["group_code"] == "Q"
    assert bmi_model["group_display_en"] == "Q (Q1 vs Q4)"
    assert bmi_model["group_display_cn"] == "Q（Q1 vs Q4）"
    assert bmi_model["direction"] == "negative"


def test_model_detail_exposes_normalized_display_fields(client):
    response = client.get("/api/model_detail/BMI_Q_lipid_RF")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["indicator_display"] == "ΔBMI"
    assert payload["group_code"] == "Q"
    assert payload["group_display_cn"] == "Q（Q1 vs Q4）"


def test_sample_data_falls_back_to_project_root_training_csv(monkeypatch, client, tmp_path):
    project_root = tmp_path
    website_dir = project_root / "website"
    website_dir.mkdir()
    training_csv = project_root / "281_merge_lipids_enroll.csv"
    training_csv.write_text("LIPID_A\n1.0\n3.0\n", encoding="utf-8")

    models = dict(app_module._models)
    info = dict(app_module._model_info)
    models["TEST_SAMPLE"] = {
        "features": ["LIPID_A"],
        "indicator": "BMI",
        "group": "q4",
        "model_name": "RF",
    }
    info["TEST_SAMPLE"] = {
        "indicator": "BMI",
        "group": "q4",
        "model_name": "RF",
    }

    monkeypatch.setattr(app_module, "_models", models)
    monkeypatch.setattr(app_module, "_model_info", info)
    monkeypatch.setattr(app_module, "APP_DIR", website_dir)
    monkeypatch.setattr(app_module, "BASE_DIR", website_dir)

    response = client.get("/api/sample_data/TEST_SAMPLE")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["sample_values"]["LIPID_A"] == 2.0


def test_load_all_models_prefers_glm5_assets_over_legacy_models(monkeypatch, tmp_path):
    website_dir = tmp_path / "website"
    models_dir = website_dir / "models"
    data_dir = website_dir / "data"
    trained_dir = website_dir / "trained_models"

    models_dir.mkdir(parents=True)
    data_dir.mkdir()
    trained_dir.mkdir()

    with open(models_dir / "BMI_q4_RF.pkl", "wb") as f:
        pickle.dump({"model": DummyModel(pred=1, proba=(0.2, 0.8)), "features": ["LEGACY_LIPID"]}, f)

    with open(trained_dir / "BMI_Q_lipid_RF.pkl", "wb") as f:
        pickle.dump(DummyModel(pred=1, proba=(0.2, 0.8)), f)

    with open(trained_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "BMI_Q_lipid_RF": {
                    "indicator": "BMI",
                    "cutoff": "Q",
                    "model": "RF",
                    "model_type": "lipid",
                    "features": ["LIPID_A"],
                    "lipid_features": ["LIPID_A"],
                    "performance": {
                        "full_auroc": 0.8,
                        "full_auprc": 0.75,
                        "full_sens": 0.72,
                        "full_spec": 0.68,
                    },
                }
            },
            f,
            ensure_ascii=False,
        )

    monkeypatch.setattr(app_module, "BASE_DIR", website_dir)
    monkeypatch.setattr(app_module, "APP_DIR", website_dir)
    monkeypatch.setattr(app_module, "MODELS_DIR", models_dir)
    monkeypatch.setattr(app_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(app_module, "_models", {})
    monkeypatch.setattr(app_module, "_model_info", {})

    app_module.load_all_models()

    assert sorted(app_module._models) == ["BMI_Q_lipid_RF"]
    assert sorted(app_module._model_info) == ["BMI_Q_lipid_RF"]


def test_load_all_models_uses_glm5_metadata_for_indicator_group_and_model(monkeypatch, tmp_path):
    website_dir = tmp_path / "website"
    models_dir = website_dir / "models"
    data_dir = website_dir / "data"
    trained_dir = website_dir / "trained_models"

    models_dir.mkdir(parents=True)
    data_dir.mkdir()
    trained_dir.mkdir()

    with open(trained_dir / "BMI_Q_EN_LR.pkl", "wb") as f:
        pickle.dump(DummyModel(pred=1, proba=(0.2, 0.8)), f)

    with open(trained_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "BMI_Q_EN_LR": {
                    "indicator": "BMI",
                    "indicator_cn": "BMI",
                    "cutoff": "Q",
                    "model": "EN_LR",
                    "features": ["LIPID_A"],
                    "performance": {
                        "full_auroc": 0.8,
                        "m2f_auroc": 0.6,
                        "f2m_auroc": 0.58,
                        "full_sens": 0.72,
                        "full_spec": 0.68,
                    },
                }
            },
            f,
            ensure_ascii=False,
        )

    monkeypatch.setattr(app_module, "BASE_DIR", website_dir)
    monkeypatch.setattr(app_module, "APP_DIR", website_dir)
    monkeypatch.setattr(app_module, "MODELS_DIR", models_dir)
    monkeypatch.setattr(app_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(app_module, "_models", {})
    monkeypatch.setattr(app_module, "_model_info", {})

    app_module.load_all_models()
    info = app_module.get_model_metadata("BMI_Q_EN_LR")

    assert info["indicator"] == "BMI"
    assert info["indicator_display"] == "ΔBMI"
    assert info["group_code"] == "Q"
    assert info["group_display_en"] == "Q (Q1 vs Q4)"
    assert info["model_name"] == "EN_LR"


@pytest.mark.parametrize(
    ("indicator", "direction", "pred", "expected_en", "expected_cn"),
    [
        ("BMI", "negative", 1, "decrease more", "下降更多"),
        ("BMI", "negative", 0, "decrease less", "下降较少"),
        ("PSM", "positive", 1, "increase more", "上升更多"),
        ("PSM", "positive", 0, "increase less", "上升较少"),
    ],
)
def test_predict_single_uses_direction_specific_response_wording(
    monkeypatch, indicator, direction, pred, expected_en, expected_cn
):
    model_key = f"TEST_{indicator}_{direction}_{pred}"
    install_dummy_model(
        monkeypatch,
        model_key,
        indicator=indicator,
        direction=direction,
        pred=pred,
    )

    result = app_module.predict_single(model_key, {"LIPID_A": 1.23})

    assert result["label_en"] in {"High Response", "Low Response"}
    assert expected_en in result["label_detail_en"]
    assert expected_cn in result["label_detail_cn"]
    assert f"Δ{indicator}" in result["label_detail_en"]


def test_api_models_exposes_model_type_and_input_schema(monkeypatch, client):
    install_dummy_model(
        monkeypatch,
        "FUSION_BMI_Q_EN_LR",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="EN_LR",
        model_type="fusion",
        clinical_features=["age_enroll", "BMI"],
        lipid_features=["LIPID_A"],
        is_best_within_type=True,
    )

    response = client.get("/api/models")
    assert response.status_code == 200

    payload = response.get_json()
    model = payload["models"]["FUSION_BMI_Q_EN_LR"]
    assert model["model_type"] == "fusion"
    assert model["input_schema"][0]["section"] == "clinical"
    assert model["input_schema"][-1]["section"] == "lipid"
    assert model["is_best_within_type"] is True


def test_api_predict_accepts_nested_inputs_payload_for_fusion_model(monkeypatch, client):
    install_dummy_model(
        monkeypatch,
        "FUSION_BMI_Q_RF",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_type="fusion",
        clinical_features=["age_enroll"],
        lipid_features=["LIPID_A"],
    )

    response = client.post(
        "/api/predict",
        json={
            "model_key": "FUSION_BMI_Q_RF",
            "inputs": {
                "age_enroll": 11,
                "LIPID_A": 1.23,
            },
        },
    )
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["missing_features"] == []
    assert payload["model_info"]["model_type"] == "fusion"


def test_api_comparison_returns_best_clinical_lipid_and_fusion_models(monkeypatch, client):
    monkeypatch.setattr(app_module, "_models", {})
    monkeypatch.setattr(app_module, "_model_info", {})

    install_dummy_model(
        monkeypatch,
        "BMI_Q_clinical_LR_L2",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="LR_L2",
        model_type="clinical",
        clinical_features=["age_enroll", "BMI"],
        lipid_features=[],
        is_best_within_type=True,
    )
    install_dummy_model(
        monkeypatch,
        "BMI_Q_lipid_RF",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="RF",
        model_type="lipid",
        clinical_features=[],
        lipid_features=["LIPID_A"],
        is_best_within_type=True,
    )
    install_dummy_model(
        monkeypatch,
        "BMI_Q_fusion_EN_LR",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="EN_LR",
        model_type="fusion",
        clinical_features=["age_enroll", "BMI"],
        lipid_features=["LIPID_A"],
        is_best_within_type=True,
        is_best_overall=True,
    )

    response = client.get("/api/comparison?indicator=BMI&group=Q")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["models"]["clinical"]["key"] == "BMI_Q_clinical_LR_L2"
    assert payload["models"]["lipid"]["key"] == "BMI_Q_lipid_RF"
    assert payload["models"]["fusion"]["key"] == "BMI_Q_fusion_EN_LR"


def test_api_model_family_summary_filters_indicator_group_and_model_type(monkeypatch, client):
    monkeypatch.setattr(app_module, "_models", {})
    monkeypatch.setattr(app_module, "_model_info", {})

    install_dummy_model(
        monkeypatch,
        "BMI_Q_fusion_EN_LR",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="EN_LR",
        model_type="fusion",
        clinical_features=["age_enroll"],
        lipid_features=["LIPID_A"],
        is_best_within_type=True,
    )
    install_dummy_model(
        monkeypatch,
        "BMI_Q_fusion_RF",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="Q",
        model_name="RF",
        model_type="fusion",
        clinical_features=["age_enroll"],
        lipid_features=["LIPID_A"],
    )
    install_dummy_model(
        monkeypatch,
        "BMI_T_fusion_RF",
        indicator="BMI",
        direction="negative",
        pred=1,
        group="T",
        model_name="RF",
        model_type="fusion",
        clinical_features=["age_enroll"],
        lipid_features=["LIPID_A"],
    )

    response = client.get("/api/model_family_summary?indicator=BMI&group=Q&model_type=fusion")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["count"] == 2
    assert [row["key"] for row in payload["models"]] == ["BMI_Q_fusion_EN_LR", "BMI_Q_fusion_RF"]


def test_predict_single_recovers_logistic_regression_missing_multi_class(client):
    key = "BMI_Q_clinical_LR_L2"
    clf = app_module._models[key]["model"].named_steps["clf"]
    assert not hasattr(clf, "multi_class")

    sample_payload = client.get(f"/api/sample_data/{key}").get_json()
    sample_inputs = sample_payload.get("sample_inputs") or sample_payload.get("sample_values")
    assert sample_inputs

    result = app_module.predict_single(key, sample_inputs)

    assert result["prediction"] in {0, 1}
    assert result["confidence"] > 0
    assert app_module._models[key]["model"].named_steps["clf"].multi_class == "auto"
