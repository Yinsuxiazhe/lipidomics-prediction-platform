from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(slots=True)
class RawProjectTables:
    group: pd.DataFrame
    lipid: pd.DataFrame
    clinical_full: pd.DataFrame
    clinical_slim: pd.DataFrame


def _read_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _coerce_id_to_string(frame: pd.DataFrame, id_column: str) -> pd.DataFrame:
    standardized = frame.copy()
    standardized[id_column] = standardized[id_column].map(str).astype(object)
    return standardized


def load_project_tables(
    group_path: str | Path,
    lipid_path: str | Path,
    clinical_full_path: str | Path,
    clinical_slim_path: str | Path,
) -> RawProjectTables:
    group = _coerce_id_to_string(_read_csv(group_path), "ID")
    lipid = _coerce_id_to_string(_read_csv(lipid_path), "NAME")
    clinical_full = _coerce_id_to_string(_read_csv(clinical_full_path), "ID")
    clinical_slim = _coerce_id_to_string(_read_csv(clinical_slim_path), "ID")

    return RawProjectTables(
        group=group,
        lipid=lipid,
        clinical_full=clinical_full,
        clinical_slim=clinical_slim,
    )
