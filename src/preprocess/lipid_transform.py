from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass(slots=True)
class LipidPreprocessor:
    pseudo_count_strategy: str = "half_min_positive"
    selected_columns_: list[str] = field(default_factory=list)
    pseudo_counts_: dict[str, float] = field(default_factory=dict)
    means_: dict[str, float] = field(default_factory=dict)
    stds_: dict[str, float] = field(default_factory=dict)

    def fit(self, frame: pd.DataFrame) -> "LipidPreprocessor":
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        self.selected_columns_ = [
            column
            for column in numeric.columns
            if numeric[column].nunique(dropna=True) > 1
        ]
        if not self.selected_columns_:
            raise ValueError("No non-constant lipid features available after filtering.")

        transformed = {}
        for column in self.selected_columns_:
            series = numeric[column]
            positive = series[series > 0].dropna()
            pseudo = float(positive.min() / 2.0) if not positive.empty else 1e-9
            self.pseudo_counts_[column] = pseudo
            adjusted = series.fillna(0.0).clip(lower=0.0).replace(0.0, pseudo)
            logged = adjusted.map(np.log1p)
            transformed[column] = logged

        transformed_frame = pd.DataFrame(transformed, index=frame.index)
        self.means_ = transformed_frame.mean().to_dict()
        self.stds_ = transformed_frame.std(ddof=0).replace(0, 1.0).to_dict()
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not self.selected_columns_:
            raise ValueError("LipidPreprocessor must be fitted before transform().")

        numeric = frame.apply(pd.to_numeric, errors="coerce")
        transformed = {}
        for column in self.selected_columns_:
            series = numeric[column]
            pseudo = self.pseudo_counts_[column]
            adjusted = series.fillna(0.0).clip(lower=0.0).replace(0.0, pseudo)
            logged = adjusted.map(np.log1p)
            transformed[column] = (logged - self.means_[column]) / self.stds_[column]

        return pd.DataFrame(transformed, index=frame.index)

    def fit_transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return self.fit(frame).transform(frame)
