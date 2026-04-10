import pandas as pd


def test_select_clinical_columns_respects_missing_threshold_and_required_columns():
    from src.preprocess.clinical_filter import select_clinical_columns

    frame = pd.DataFrame(
        {
            "ID": ["A001", "A002", "A003", "A004"],
            "Group": ["response", "response", "noresponse", "noresponse"],
            "BMI": [21.0, 22.0, 23.0, 24.0],
            "SFT": [1.1, None, None, None],
            "noise_high_missing": [1.0, None, None, None],
        }
    )

    result = select_clinical_columns(
        frame,
        missing_threshold=0.2,
        required_columns=["SFT"],
        protected_columns=["ID", "Group"],
    )

    assert "BMI" in result.selected_features
    assert "SFT" in result.selected_features
    assert "noise_high_missing" not in result.selected_features
    assert list(result.filtered.columns) == ["ID", "Group", "BMI", "SFT"]


def test_clean_clinical_feature_space_keeps_baseline_domains_and_excludes_controls():
    from src.preprocess.clinical_filter import clean_clinical_feature_space

    frame = pd.DataFrame(
        {
            "ID": ["A001", "A002", "A003"],
            "Group": ["response", "noresponse", "response"],
            "BMI": [21.0, 22.0, 23.0],
            "age_enroll": [10.0, 10.5, 11.0],
            "serum_CysC": [0.8, 0.9, 1.0],
            "whole_blood_LYMPH_count": [2.0, 2.1, 2.2],
            "Inbody_39_PBF_.Percent_Body_Fat.": [30.0, 31.0, 32.0],
            "Inbody_125_Weight_Control": [1.0, 1.0, 1.0],
            "random_unrelated_metric": [5.0, 6.0, 7.0],
        }
    )

    result = clean_clinical_feature_space(frame, protected_columns=["ID", "Group"])

    assert "BMI" in result.selected_features
    assert "serum_CysC" in result.selected_features
    assert "whole_blood_LYMPH_count" in result.selected_features
    assert "Inbody_39_PBF_.Percent_Body_Fat." in result.selected_features
    assert "Inbody_125_Weight_Control" not in result.selected_features
    assert "random_unrelated_metric" not in result.selected_features
