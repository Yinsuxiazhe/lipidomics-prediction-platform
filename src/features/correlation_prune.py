from __future__ import annotations

import pandas as pd


def prune_correlated_features(
    frame: pd.DataFrame,
    ranking: pd.DataFrame,
    threshold: float = 0.95,
) -> list[str]:
    ordered_features = [feature for feature in ranking["feature"].tolist() if feature in frame.columns]
    correlation = frame[ordered_features].corr().abs()
    kept: list[str] = []

    for feature in ordered_features:
        if not kept:
            kept.append(feature)
            continue

        is_redundant = any(correlation.loc[feature, prior] >= threshold for prior in kept)
        if not is_redundant:
            kept.append(feature)

    return kept
