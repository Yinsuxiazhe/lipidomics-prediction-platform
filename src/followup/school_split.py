from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.io.load_data import _coerce_id_to_string


DEFAULT_MAPPING_SHEET_NAME = "运动强度分组_401人"


def load_school_mapping(
    mapping_path: str | Path,
    sheet_name: str = DEFAULT_MAPPING_SHEET_NAME,
) -> pd.DataFrame:
    frame = pd.read_excel(mapping_path, sheet_name=sheet_name, dtype={"ID": str})
    missing = [column for column in ["school", "ID", "intensity"] if column not in frame.columns]
    if missing:
        raise ValueError(f"学校映射缺少列: {missing}")

    normalized = frame.loc[:, ["ID", "school", "intensity"]].copy()
    normalized = _coerce_id_to_string(normalized, "ID")
    normalized["school"] = normalized["school"].astype(str)
    normalized["intensity"] = normalized["intensity"].astype(str)
    normalized = normalized.drop_duplicates(subset=["ID"]).sort_values("ID").reset_index(drop=True)
    return normalized


def attach_school_mapping(
    frame: pd.DataFrame,
    mapping_frame: pd.DataFrame,
) -> pd.DataFrame:
    working = _coerce_id_to_string(frame.copy(), "ID")
    mapping = _coerce_id_to_string(mapping_frame.copy(), "ID")
    return working.merge(mapping, on="ID", how="left")


def resolve_group_series(
    frame: pd.DataFrame,
    *,
    group_by: str,
    mapping_path: str | Path | None = None,
    mapping_sheet_name: str = DEFAULT_MAPPING_SHEET_NAME,
) -> tuple[pd.Series, dict[str, Any]]:
    working = _coerce_id_to_string(frame.copy(), "ID")
    normalized_group_by = str(group_by or "id_prefix")

    if normalized_group_by == "id_prefix":
        return (
            working["ID"].astype(str).str[0],
            {
                "group_by": "id_prefix",
                "group_column": "prefix",
                "validation_scheme": "leave_one_prefix_out",
                "mapping_frame": None,
            },
        )

    if normalized_group_by == "school":
        if not mapping_path:
            raise ValueError("group_by=school 时必须提供 mapping_path")
        mapping_frame = load_school_mapping(mapping_path, sheet_name=mapping_sheet_name)
        merged = attach_school_mapping(working[["ID"]], mapping_frame)
        if merged["school"].isna().any():
            missing_ids = merged.loc[merged["school"].isna(), "ID"].astype(str).tolist()
            raise ValueError(f"以下 ID 缺少学校映射: {missing_ids[:10]}")
        return (
            merged["school"].astype(str),
            {
                "group_by": "school",
                "group_column": "school",
                "validation_scheme": "leave_one_school_out",
                "mapping_frame": mapping_frame,
                "mapping_path": str(mapping_path),
                "mapping_sheet_name": mapping_sheet_name,
            },
        )

    raise ValueError(f"Unsupported pseudo_external group_by: {normalized_group_by}")


def resolve_fixed_group_split(
    group_values: pd.Series,
    *,
    group_meta: dict[str, Any],
    fixed_group_split_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    config = fixed_group_split_config or {}
    if not config.get("enabled", False):
        return None

    requested_groups = [str(item) for item in (config.get("test_groups") or [])]
    if not requested_groups:
        raise ValueError("fixed_group_split.enabled=true 时必须提供 test_groups")

    deduplicated_groups: list[str] = []
    seen: set[str] = set()
    for group_name in requested_groups:
        if group_name not in seen:
            deduplicated_groups.append(group_name)
            seen.add(group_name)

    available_groups = set(group_values.dropna().astype(str).tolist())
    missing_groups = [group_name for group_name in deduplicated_groups if group_name not in available_groups]
    if missing_groups:
        raise ValueError(f"fixed_group_split 中以下 test_groups 不存在于当前分组里: {missing_groups}")

    group_by = str(group_meta.get("group_by") or "group")
    if group_by == "school":
        validation_scheme = "fixed_school_combo_holdout"
    elif group_by == "id_prefix":
        validation_scheme = "fixed_prefix_combo_holdout"
    else:
        validation_scheme = f"fixed_{group_by}_combo_holdout"

    holdout_group_label = " + ".join(deduplicated_groups)
    split_label = str(config.get("split_label") or "__".join(deduplicated_groups))
    return {
        "group_by": group_by,
        "validation_scheme": validation_scheme,
        "test_groups": deduplicated_groups,
        "holdout_group_label": holdout_group_label,
        "split_label": split_label,
    }
