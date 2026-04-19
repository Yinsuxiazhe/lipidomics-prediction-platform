import warnings

warnings.filterwarnings(
    "ignore",
    message="Trying to unpickle estimator",
)

import pytest

import website.app as app_module


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_index_template_uses_clean_title_and_inline_favicon(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Lipidomics Prediction Platform · EXerCise on Obesity AdolescENTS in pekING (EXCITING) Study (NCT04984005)" in html
    assert '<link rel="icon" href="data:,"/>' in html


def test_index_template_includes_current_model_mappings_and_mobile_polish(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert 'LR: { abbrev: "LR", fullEn: "Logistic Regression", fullCn:' in html
    assert 'SVM: { abbrev: "SVM", fullEn: "Support Vector Machine", fullCn:' in html
    assert 'KNN: { abbrev: "KNN", fullEn: "K-Nearest Neighbors", fullCn:' in html
    assert 'function shouldShowModelFullName' in html
    assert 'fullName && fullName !== modelName' in html
    assert '.tab-bar { overflow-x: auto;' in html
    assert '.model-grid { grid-template-columns: 1fr; }' in html
    assert "trained models across clinical-only / lipid-only / fusion" in html


def test_index_template_includes_model_type_switch_and_dynamic_input_sections(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert 'data-model-type="clinical"' in html
    assert 'data-model-type="lipid"' in html
    assert 'data-model-type="fusion"' in html
    assert 'id="clinical-input-section"' in html
    assert 'id="lipid-input-section"' in html
    assert 'function renderDynamicInputs' in html


def test_index_template_includes_comparison_calibration_and_dca_modules(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert 'id="comparison-panel"' in html
    assert 'Algorithm Comparison' in html
    assert 'Calibration Curve' in html
    assert 'Decision Curve Analysis' in html
    assert 'function loadComparisonPanel' in html
    assert 'function loadModelFamilySummary' in html


def test_index_template_avoids_stale_lipid_only_and_hardcoded_14_model_copy(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Currently deployed lipid-only models" not in html
    assert "14 selected models" not in html
    assert "14 ML models" not in html
    assert "Input Selected Model Data" in html
    assert "Features used by the model (Top 10)" in html
    assert 'function updateSummaryStats' in html
    assert 'function getFeatureCountLabel' in html
