def test_default_experiment_registry_contains_core_models():
    from src.models.run_nested_cv import build_default_experiment_registry

    registry = build_default_experiment_registry()

    assert set(registry) >= {
        "clinical_slim_logistic",
        "lipid_elastic_net",
        "clinical_full_elastic_net",
        "fusion_elastic_net",
        "fusion_full_elastic_net",
    }


def test_run_experiments_executes_nested_cv_on_toy_cohorts():
    import pandas as pd

    from src.data.build_cohort import AnalysisCohorts
    from src.models.run_nested_cv import run_experiments

    ids = [f"A{i:03d}" for i in range(18)]
    groups = ["noresponse"] * 9 + ["response"] * 9
    clinical_slim = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "age_enroll": [10.0] * 18,
            "bmi_z_enroll": [1.0] * 9 + [3.0] * 9,
            "SFT": [3.0] * 9 + [1.0] * 9,
            "Gender": [0, 1] * 9,
            "BMI": [20.0] * 9 + [28.0] * 9,
        }
    )
    clinical_full = clinical_slim.assign(
        whole_blood_LYMPH_count=[1.0] * 9 + [3.0] * 9,
        serum_CysC=[0.8] * 9 + [1.2] * 9,
    )
    group_lipid = pd.DataFrame(
        {
            "ID": ids,
            "Group": groups,
            "NAME": ids,
            "lipid_signal": [0.1] * 9 + [10.0] * 9,
            "lipid_shadow": [0.11] * 9 + [10.1] * 9,
            "lipid_noise": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        }
    )
    group_fusion = clinical_slim.merge(
        group_lipid.drop(columns=["NAME", "Group"]),
        on="ID",
        how="inner",
    )
    group_fusion_full = clinical_full.merge(
        group_lipid.drop(columns=["NAME", "Group"]),
        on="ID",
        how="inner",
    )
    cohorts = AnalysisCohorts(
        group_lipid=group_lipid,
        group_clinical_slim=clinical_slim,
        group_clinical_full=clinical_full,
        group_fusion=group_fusion,
        group_fusion_full=group_fusion_full,
        summary={"overlap_id_count": 18},
    )

    result = run_experiments(
        cohorts=cohorts,
        requested_experiments=["clinical_slim_logistic", "lipid_elastic_net"],
        dry_run=False,
        cv_config={
            "outer_splits": 3,
            "outer_repeats": 1,
            "inner_splits": 2,
            "random_state": 42,
            "lipid_top_k": 2,
            "clinical_top_k": 5,
            "correlation_threshold": 0.95,
            "clinical_missing_threshold": 0.2,
        },
    )

    assert result["status"] == "completed"
    assert set(result["results"]) == {"clinical_slim_logistic", "lipid_elastic_net"}
    assert result["results"]["clinical_slim_logistic"]["n_outer_folds"] == 3
    assert result["results"]["lipid_elastic_net"]["mean_auc"] >= 0.95
