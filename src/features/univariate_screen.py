from __future__ import annotations

from typing import Iterable

import pandas as pd
from sklearn.metrics import roc_auc_score


def rank_features_by_auc(
    frame: pd.DataFrame,
    y: Iterable[int],
    top_k: int | None = None,
) -> pd.DataFrame:
    target = pd.Series(list(y))
    rows = []

    for column in frame.columns:
        series = pd.to_numeric(frame[column], errors="coerce")
        valid = series.notna()
        x_valid = series.loc[valid]
        y_valid = target.loc[valid]

        if x_valid.nunique(dropna=True) <= 1 or y_valid.nunique(dropna=True) <= 1:
            auc = float("nan")
            direction_free_auc = float("nan")
        else:
            auc = float(roc_auc_score(y_valid, x_valid))
            direction_free_auc = max(auc, 1.0 - auc)

        rows.append(
            {
                "feature": column,
                "auc": auc,
                "direction_free_auc": direction_free_auc,
                "missing_pct": float(series.isna().mean()),
            }
        )

    ranking = pd.DataFrame(rows).sort_values(
        by=["direction_free_auc", "feature"],
        ascending=[False, True],
        na_position="last",
    )
    if top_k is not None:
        ranking = ranking.head(top_k)
    return ranking.reset_index(drop=True)
