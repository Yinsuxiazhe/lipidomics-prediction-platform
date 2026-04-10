import pandas as pd


def test_build_analysis_cohorts_keeps_overlap_only():
    from src.data.build_cohort import build_analysis_cohorts
    from src.io.load_data import RawProjectTables

    raw = RawProjectTables(
        group=pd.DataFrame(
            {
                "ID": ["A001", "A002", "A003"],
                "Group": ["response", "noresponse", "response"],
            }
        ),
        lipid=pd.DataFrame(
            {
                "NAME": ["A001", "A002", "A004"],
                "L1": [1.0, 2.0, 3.0],
            }
        ),
        clinical_full=pd.DataFrame(
            {
                "ID": ["A001", "A002", "A005"],
                "age_enroll": [10, 11, 12],
                "BMI": [20.0, 21.0, 22.0],
                "Gender": [0, 1, 0],
                "bmi_z_enroll": [1.2, 1.3, 1.4],
                "SFT": [1.1, 1.2, 1.3],
                "whole_blood_LYMPH_count": [2.1, 2.2, 2.3],
            }
        ),
        clinical_slim=pd.DataFrame(
            {
                "ID": ["A001", "A002", "A005"],
                "age_enroll": [10, 11, 12],
                "BMI": [20.0, 21.0, 22.0],
                "Gender": [0, 1, 0],
                "bmi_z_enroll": [1.2, 1.3, 1.4],
                "SFT": [1.1, 1.2, 1.3],
            }
        ),
    )

    cohorts = build_analysis_cohorts(raw)

    assert cohorts.group_lipid.shape[0] == 2
    assert cohorts.group_clinical_slim.shape[0] == 2
    assert cohorts.group_clinical_full.shape[0] == 2
    assert cohorts.group_fusion.shape[0] == 2
    assert cohorts.group_fusion_full.shape[0] == 2
    assert "whole_blood_LYMPH_count" in cohorts.group_fusion_full.columns
    assert cohorts.summary["overlap_id_count"] == 2
