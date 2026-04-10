from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(slots=True)
class ClinicalSelectionResult:
    filtered: pd.DataFrame
    selected_features: list[str]
    missing_summary: pd.DataFrame


BASELINE_EXACT_COLUMNS = {
    "age_enroll",
    "bmi_z_enroll",
    "bmi_p_enroll",
    "BMI",
    "SFT",
    "Gender",
    "HAD",
    "SWE",
    "HRI",
    "HARI",
    "AoD",
    "AV_sub",
}
BASELINE_PREFIXES = ("serum_", "whole_blood_", "Inbody_")
BASELINE_KEYWORDS = (
    "feno",
    "fino",
    "exp.flow",
    "fvc",
    "fev",
    "mmef",
    "mmf",
    "v25",
    "v50",
    "fet",
    "pet",
    "pif",
    "fiv",
    "irv",
    "erv",
    "tv_",
)
EXCLUDE_KEYWORDS = ("control",)


def select_clinical_columns(
    frame: pd.DataFrame,
    missing_threshold: float = 0.2,
    required_columns: Iterable[str] | None = None,
    protected_columns: Iterable[str] | None = None,
) -> ClinicalSelectionResult:
    required = set(required_columns or [])
    protected = list(protected_columns or [])
    feature_columns = [column for column in frame.columns if column not in protected]

    missing_summary = frame[feature_columns].isna().mean().rename("missing_pct").reset_index()
    missing_summary = missing_summary.rename(columns={"index": "feature"})

    selected_features = [
        column
        for column in feature_columns
        if frame[column].isna().mean() <= missing_threshold or column in required
    ]
    filtered = frame.loc[:, protected + selected_features].copy()
    return ClinicalSelectionResult(
        filtered=filtered,
        selected_features=selected_features,
        missing_summary=missing_summary,
    )


def clean_clinical_feature_space(
    frame: pd.DataFrame,
    protected_columns: Iterable[str] | None = None,
) -> ClinicalSelectionResult:
    protected = list(protected_columns or [])
    feature_columns = [column for column in frame.columns if column not in protected]

    selected_features = []
    for column in feature_columns:
        lowered = column.lower()
        if any(keyword in lowered for keyword in EXCLUDE_KEYWORDS):
            continue
        if column in BASELINE_EXACT_COLUMNS:
            selected_features.append(column)
            continue
        if column.startswith(BASELINE_PREFIXES):
            selected_features.append(column)
            continue
        if any(keyword in lowered for keyword in BASELINE_KEYWORDS):
            selected_features.append(column)

    missing_summary = frame[feature_columns].isna().mean().rename("missing_pct").reset_index()
    missing_summary = missing_summary.rename(columns={"index": "feature"})
    filtered = frame.loc[:, protected + selected_features].copy()
    return ClinicalSelectionResult(
        filtered=filtered,
        selected_features=selected_features,
        missing_summary=missing_summary,
    )
