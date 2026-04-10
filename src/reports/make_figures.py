from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_curve


def write_roc_outputs(results: dict, output_dir: str | Path) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = []
    for experiment, payload in results.get("results", {}).items():
        y_true = []
        y_score = []
        for fold in payload.get("fold_results", []):
            y_true.extend(fold.get("y_true", []))
            y_score.extend(fold.get("y_score", []))
        if not y_true:
            continue
        fpr, tpr, _ = roc_curve(y_true, y_score)
        for x, y in zip(fpr, tpr):
            rows.append({"experiment": experiment, "fpr": x, "tpr": y})

    roc_df = pd.DataFrame(rows)
    roc_file = output_path / "roc_curve_points.csv"
    roc_df.to_csv(roc_file, index=False)
    return {"roc_curve_points": str(roc_file)}
