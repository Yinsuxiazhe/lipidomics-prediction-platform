from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_experiment_tables(results: dict, output_dir: str | Path) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    performance_rows = []
    feature_rows = []
    fold_rows = []
    stability_rows = []
    for experiment, payload in results.get("results", {}).items():
        performance_rows.append(
            {
                "experiment": experiment,
                "mean_auc": payload.get("mean_auc"),
                "std_auc": payload.get("std_auc"),
                "mean_train_auc": payload.get("mean_train_auc"),
                "n_outer_folds": payload.get("n_outer_folds"),
            }
        )
        for feature, frequency in payload.get("feature_frequency", {}).items():
            feature_rows.append(
                {
                    "experiment": experiment,
                    "feature": feature,
                    "frequency": frequency,
                }
            )
        fold_results = payload.get("fold_results", [])
        total_folds = payload.get("n_outer_folds") or len(fold_results) or 1
        for fold in fold_results:
            fold_rows.append(
                {
                    "experiment": experiment,
                    "fold_index": fold.get("fold_index"),
                    "auc": fold.get("auc"),
                    "train_auc": fold.get("train_auc"),
                    "selected_feature_count": fold.get("selected_feature_count"),
                }
            )
        ranked_features = sorted(
            payload.get("feature_frequency", {}).items(),
            key=lambda item: (-item[1], item[0]),
        )
        for rank, (feature, frequency) in enumerate(ranked_features, start=1):
            stability_rows.append(
                {
                    "experiment": experiment,
                    "feature": feature,
                    "frequency": frequency,
                    "selection_rate": frequency / total_folds,
                    "rank": rank,
                }
            )

    performance_df = pd.DataFrame(performance_rows)
    feature_df = pd.DataFrame(feature_rows)
    fold_df = pd.DataFrame(fold_rows)
    stability_df = pd.DataFrame(stability_rows)

    performance_file = output_path / "performance_summary.csv"
    feature_file = output_path / "feature_frequency.csv"
    fold_file = output_path / "fold_metrics.csv"
    stability_file = output_path / "feature_stability_summary.csv"
    performance_df.to_csv(performance_file, index=False)
    feature_df.to_csv(feature_file, index=False)
    fold_df.to_csv(fold_file, index=False)
    stability_df.to_csv(stability_file, index=False)

    return {
        "performance_summary": str(performance_file),
        "feature_frequency": str(feature_file),
        "fold_metrics": str(fold_file),
        "feature_stability_summary": str(stability_file),
    }
