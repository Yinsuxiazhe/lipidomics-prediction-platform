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
    assert "Currently deployed lipid-only models" in html
