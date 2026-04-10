from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.io.load_data import RawProjectTables
from src.io.validate_inputs import validate_required_columns, validate_unique_ids


@dataclass(slots=True)
class AnalysisCohorts:
    group_lipid: pd.DataFrame
    group_clinical_slim: pd.DataFrame
    group_clinical_full: pd.DataFrame
    group_fusion: pd.DataFrame
    group_fusion_full: pd.DataFrame
    summary: dict


def build_analysis_cohorts(raw: RawProjectTables) -> AnalysisCohorts:
    validate_required_columns(raw.group, ["ID", "Group"], "group")
    validate_required_columns(raw.lipid, ["NAME"], "lipid")
    validate_required_columns(raw.clinical_full, ["ID"], "clinical_full")
    validate_required_columns(raw.clinical_slim, ["ID"], "clinical_slim")

    validate_unique_ids(raw.group, "ID", "group")
    validate_unique_ids(raw.lipid, "NAME", "lipid")
    validate_unique_ids(raw.clinical_full, "ID", "clinical_full")
    validate_unique_ids(raw.clinical_slim, "ID", "clinical_slim")

    overlap_ids = (
        set(raw.group["ID"])
        & set(raw.lipid["NAME"])
        & set(raw.clinical_full["ID"])
        & set(raw.clinical_slim["ID"])
    )

    group = raw.group[raw.group["ID"].isin(overlap_ids)].copy()
    lipid = raw.lipid[raw.lipid["NAME"].isin(overlap_ids)].copy()
    clinical_full = raw.clinical_full[raw.clinical_full["ID"].isin(overlap_ids)].copy()
    clinical_slim = raw.clinical_slim[raw.clinical_slim["ID"].isin(overlap_ids)].copy()

    group_lipid = group.merge(lipid, left_on="ID", right_on="NAME", how="inner")
    group_clinical_slim = group.merge(clinical_slim, on="ID", how="inner")
    group_clinical_full = group.merge(clinical_full, on="ID", how="inner")
    group_fusion = (
        group_lipid.drop(columns=["NAME"])
        .merge(clinical_slim, on="ID", how="inner", suffixes=("", "_clinical"))
    )
    group_fusion_full = (
        group_lipid.drop(columns=["NAME"])
        .merge(clinical_full, on="ID", how="inner", suffixes=("", "_clinical"))
    )

    summary = {
        "overlap_id_count": len(overlap_ids),
        "group_lipid_shape": group_lipid.shape,
        "group_clinical_slim_shape": group_clinical_slim.shape,
        "group_clinical_full_shape": group_clinical_full.shape,
        "group_fusion_shape": group_fusion.shape,
        "group_fusion_full_shape": group_fusion_full.shape,
    }

    return AnalysisCohorts(
        group_lipid=group_lipid,
        group_clinical_slim=group_clinical_slim,
        group_clinical_full=group_clinical_full,
        group_fusion=group_fusion,
        group_fusion_full=group_fusion_full,
        summary=summary,
    )
