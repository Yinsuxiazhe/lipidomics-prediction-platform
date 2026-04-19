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


def install_dummy_model(monkeypatch, key, *, indicator, direction, pred, proba=(0.2, 0.8)):
    models = dict(app_module._models)
    info = dict(app_module._model_info)
    models[key] = {
        "model": DummyModel(pred=pred, proba=proba),
        "features": ["LIPID_A"],
        "indicator": indicator,
        "group": "q4",
        "model_name": "RF",
        "direction": direction,
    }
    info[key] = {
        "indicator": indicator,
        "indicator_cn": indicator,
        "group": "q4",
        "group_cn": "四分位",
        "model_name": "RF",
        "direction": direction,
        "features": ["LIPID_A"],
    }
    monkeypatch.setattr(app_module, "_models", models)
    monkeypatch.setattr(app_module, "_model_info", info)


def test_api_models_exposes_delta_indicator_and_explicit_grouping(client):
    response = client.get("/api/models")
    assert response.status_code == 200

    payload = response.get_json()
    bmi_model = payload["models"]["BMI_q4_RF"]

    assert bmi_model["indicator_display"] == "ΔBMI"
    assert bmi_model["group_code"] == "Q"
    assert bmi_model["group_display_en"] == "Q (Q1 vs Q4)"
    assert bmi_model["group_display_cn"] == "Q（Q1 vs Q4）"
    assert bmi_model["direction"] == "negative"


def test_model_detail_exposes_normalized_display_fields(client):
    response = client.get("/api/model_detail/BMI_q4_RF")
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
