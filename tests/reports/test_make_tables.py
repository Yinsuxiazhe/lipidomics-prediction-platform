from pathlib import Path

import pandas as pd


def test_write_experiment_tables_exports_performance_and_feature_frequency(tmp_path):
    from src.reports.make_tables import write_experiment_tables

    results = {
        "status": "completed",
        "results": {
            "fusion_full_elastic_net": {
                "mean_auc": 0.81,
                "std_auc": 0.04,
                "mean_train_auc": 0.86,
                "n_outer_folds": 5,
                "feature_frequency": {"BMI": 5, "lipid_signal": 4},
                "fold_results": [
                    {
                        "fold_index": 1,
                        "auc": 0.72,
                        "train_auc": 0.88,
                        "selected_feature_count": 2,
                        "selected_features": ["BMI", "lipid_signal"],
                    },
                    {
                        "fold_index": 2,
                        "auc": 0.90,
                        "train_auc": 0.84,
                        "selected_feature_count": 1,
                        "selected_features": ["BMI"],
                    },
                ],
            }
        },
    }

    output = write_experiment_tables(results, tmp_path)

    performance_path = Path(output["performance_summary"])
    frequency_path = Path(output["feature_frequency"])
    fold_metrics_path = Path(output["fold_metrics"])
    stability_path = Path(output["feature_stability_summary"])

    assert performance_path.exists()
    assert frequency_path.exists()
    assert fold_metrics_path.exists()
    assert stability_path.exists()

    performance = pd.read_csv(performance_path)
    frequency = pd.read_csv(frequency_path)
    fold_metrics = pd.read_csv(fold_metrics_path)
    stability = pd.read_csv(stability_path)

    assert performance.loc[0, "experiment"] == "fusion_full_elastic_net"
    assert "feature" in frequency.columns
    assert set(["experiment", "fold_index", "auc", "train_auc", "selected_feature_count"]).issubset(
        fold_metrics.columns
    )
    assert fold_metrics["auc"].tolist() == [0.72, 0.90]
    assert set(["experiment", "feature", "frequency", "selection_rate", "rank"]).issubset(stability.columns)
    assert stability.loc[0, "feature"] == "BMI"
    assert stability.loc[0, "selection_rate"] == 1.0
