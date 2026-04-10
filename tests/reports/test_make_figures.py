from pathlib import Path

import pandas as pd


def test_write_roc_outputs_exports_curve_points(tmp_path):
    from src.reports.make_figures import write_roc_outputs

    results = {
        "status": "completed",
        "results": {
            "fusion_full_elastic_net": {
                "fold_results": [
                    {
                        "fold_index": 1,
                        "y_true": [0, 0, 1, 1],
                        "y_score": [0.1, 0.2, 0.8, 0.9],
                    }
                ]
            }
        },
    }

    output = write_roc_outputs(results, tmp_path)
    roc_path = Path(output["roc_curve_points"])

    assert roc_path.exists()

    roc_points = pd.read_csv(roc_path)
    assert set(["experiment", "fpr", "tpr"]).issubset(roc_points.columns)
    assert roc_points["experiment"].iloc[0] == "fusion_full_elastic_net"
