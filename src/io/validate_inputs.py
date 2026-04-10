from __future__ import annotations

from typing import Iterable

import pandas as pd


def validate_unique_ids(frame: pd.DataFrame, id_column: str, table_name: str) -> None:
    duplicated = frame[id_column].duplicated()
    if duplicated.any():
        duplicates = frame.loc[duplicated, id_column].astype(str).tolist()
        raise ValueError(f"{table_name} contains duplicate IDs: {duplicates}")


def validate_required_columns(frame: pd.DataFrame, required_columns: Iterable[str], table_name: str) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{table_name} is missing required columns: {missing}")
