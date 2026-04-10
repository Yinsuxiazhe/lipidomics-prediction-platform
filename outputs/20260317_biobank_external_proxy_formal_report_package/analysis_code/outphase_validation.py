from __future__ import annotations

import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, StratifiedShuffleSplit

from src.data.build_cohort import AnalysisCohorts
from src.followup.school_split import resolve_fixed_group_split, resolve_group_series
from src.io.load_data import _coerce_id_to_string
from src.models.run_nested_cv import (
    _build_estimator,
    _merge_cv_config,
    _prepare_experiment_features,
    build_default_experiment_registry,
)


DEFAULT_CLINICAL_ANCHOR_MAPPING = {
    "age_enroll": "age_out",
    "bmi_z_enroll": "bmi_z_out",
    "SFT": "SFT",
    "Gender": "Gender",
    "BMI": "BMI",
}


def _safe_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


def _format_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "（空）"
    printable = frame.copy()
    for column in printable.columns:
        printable[column] = printable[column].map(
            lambda value: f"{value:.4f}" if isinstance(value, (float, np.floating)) and pd.notna(value) else value
        )
    headers = [str(column) for column in printable.columns]
    rows = printable.astype(object).where(pd.notna(printable), "").values.tolist()
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _load_outphase_tables(
    *,
    out_lipid_path: str | Path,
    out_clinical_full_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    out_lipid = _coerce_id_to_string(pd.read_csv(out_lipid_path), "NAME")
    out_clinical_full = _coerce_id_to_string(pd.read_csv(out_clinical_full_path), "ID")
    return out_lipid, out_clinical_full


def _align_out_clinical_columns(
    out_clinical_full: pd.DataFrame,
    clinical_anchor_mapping: dict[str, str],
) -> tuple[pd.DataFrame, list[str]]:
    aligned = out_clinical_full.copy()
    missing_sources: list[str] = []
    for target_column, source_column in clinical_anchor_mapping.items():
        if target_column in aligned.columns:
            continue
        if source_column in aligned.columns:
            aligned[target_column] = aligned[source_column]
        else:
            missing_sources.append(f"{target_column}<-{source_column}")
    return aligned, missing_sources


def build_outphase_analysis_cohorts(
    *,
    group_frame: pd.DataFrame,
    out_lipid_path: str | Path,
    out_clinical_full_path: str | Path,
    clinical_anchor_mapping: dict[str, str] | None = None,
) -> tuple[AnalysisCohorts, dict[str, Any]]:
    mapping = DEFAULT_CLINICAL_ANCHOR_MAPPING.copy()
    if clinical_anchor_mapping:
        mapping.update(clinical_anchor_mapping)

    group = _coerce_id_to_string(group_frame.copy(), "ID")
    out_lipid, out_clinical_full = _load_outphase_tables(
        out_lipid_path=out_lipid_path,
        out_clinical_full_path=out_clinical_full_path,
    )
    aligned_clinical_full, missing_sources = _align_out_clinical_columns(out_clinical_full, mapping)

    overlap_ids = sorted(set(group["ID"]) & set(out_lipid["NAME"]) & set(aligned_clinical_full["ID"]))
    group_overlap = group[group["ID"].isin(overlap_ids)].sort_values("ID").reset_index(drop=True)
    out_lipid_overlap = (
        out_lipid[out_lipid["NAME"].isin(overlap_ids)]
        .sort_values("NAME")
        .reset_index(drop=True)
    )
    aligned_clinical_overlap = (
        aligned_clinical_full[aligned_clinical_full["ID"].isin(overlap_ids)]
        .sort_values("ID")
        .reset_index(drop=True)
    )

    group_match_rate = float("nan")
    group_match_count = 0
    group_mismatch_count = 0
    if "Group" in out_lipid_overlap.columns:
        label_compare = group_overlap.merge(
            out_lipid_overlap[["NAME", "Group"]],
            left_on="ID",
            right_on="NAME",
            how="inner",
            suffixes=("_master", "_out"),
        )
        if not label_compare.empty:
            match_mask = label_compare["Group_master"].astype(str).eq(label_compare["Group_out"].astype(str))
            group_match_rate = float(match_mask.mean())
            group_match_count = int(match_mask.sum())
            group_mismatch_count = int((~match_mask).sum())

    slim_columns = [column for column in mapping if column in aligned_clinical_overlap.columns]
    out_lipid_without_group = out_lipid_overlap.drop(columns=["Group"], errors="ignore")

    group_lipid = group_overlap.merge(out_lipid_without_group, left_on="ID", right_on="NAME", how="inner")
    group_clinical_slim = group_overlap.merge(
        aligned_clinical_overlap[["ID", *slim_columns]],
        on="ID",
        how="inner",
    )
    group_clinical_full = group_overlap.merge(aligned_clinical_overlap, on="ID", how="inner")
    group_fusion = (
        group_lipid.drop(columns=["NAME"])
        .merge(aligned_clinical_overlap[["ID", *slim_columns]], on="ID", how="inner")
    )
    group_fusion_full = (
        group_lipid.drop(columns=["NAME"])
        .merge(aligned_clinical_overlap, on="ID", how="inner", suffixes=("", "_clinical"))
    )

    summary = {
        "overlap_id_count": len(overlap_ids),
        "group_lipid_shape": group_lipid.shape,
        "group_clinical_slim_shape": group_clinical_slim.shape,
        "group_clinical_full_shape": group_clinical_full.shape,
        "group_fusion_shape": group_fusion.shape,
        "group_fusion_full_shape": group_fusion_full.shape,
    }
    metadata = {
        **summary,
        "out_lipid_group_match_rate": group_match_rate,
        "out_lipid_group_match_count": group_match_count,
        "out_lipid_group_mismatch_count": group_mismatch_count,
        "missing_anchor_sources": missing_sources,
        "clinical_anchor_mapping": mapping,
    }
    return (
        AnalysisCohorts(
            group_lipid=group_lipid,
            group_clinical_slim=group_clinical_slim,
            group_clinical_full=group_clinical_full,
            group_fusion=group_fusion,
            group_fusion_full=group_fusion_full,
            summary=summary,
        ),
        metadata,
    )


def _align_paired_frames(
    baseline_frame: pd.DataFrame,
    outphase_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    overlap_ids = sorted(set(baseline_frame["ID"]) & set(outphase_frame["ID"]))
    if not overlap_ids:
        return baseline_frame.iloc[0:0].copy(), outphase_frame.iloc[0:0].copy()

    order = pd.DataFrame({"ID": overlap_ids})
    baseline_aligned = order.merge(baseline_frame, on="ID", how="left")
    outphase_aligned = order.merge(outphase_frame, on="ID", how="left")
    return baseline_aligned, outphase_aligned


def _record_skip(
    *,
    experiment: str,
    model_label: str,
    validation_scheme: str,
    split_id: str,
    holdout_group: str | None,
    status: str,
    skip_reason: str,
    n_train: int,
    n_test: int,
) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "model_label": model_label,
        "validation_scheme": validation_scheme,
        "split_id": split_id,
        "holdout_group": holdout_group,
        "status": status,
        "skip_reason": skip_reason,
        "auc": np.nan,
        "train_auc": np.nan,
        "selected_feature_count": np.nan,
        "n_train": n_train,
        "n_test": n_test,
        "train_phase": "baseline",
        "test_phase": "outphase",
    }


def _fit_and_score_transfer_split(
    *,
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    validation_scheme: str,
    split_id: str,
    holdout_group: str | None,
) -> dict[str, Any]:
    y_train = (train_frame["Group"].astype(str) == positive_label).astype(int).to_numpy()
    y_test = (test_frame["Group"].astype(str) == positive_label).astype(int).to_numpy()
    drop_columns = [column for column in ["ID", "Group", "NAME"] if column in train_frame.columns]
    train_x = train_frame.drop(columns=drop_columns).copy()
    test_x = test_frame.drop(columns=[column for column in drop_columns if column in test_frame.columns]).copy()

    if len(np.unique(y_train)) < 2:
        return _record_skip(
            experiment=experiment,
            model_label=model_label,
            validation_scheme=validation_scheme,
            split_id=split_id,
            holdout_group=holdout_group,
            status="skipped_single_class_train",
            skip_reason="训练集只有一个类别，无法调参和建模。",
            n_train=len(train_frame),
            n_test=len(test_frame),
        )

    if len(np.unique(y_test)) < 2:
        return _record_skip(
            experiment=experiment,
            model_label=model_label,
            validation_scheme=validation_scheme,
            split_id=split_id,
            holdout_group=holdout_group,
            status="skipped_single_class_test",
            skip_reason="测试集只有一个类别，无法计算 AUC。",
            n_train=len(train_frame),
            n_test=len(test_frame),
        )

    minority_class_count = min(Counter(y_train).values())
    inner_splits = min(int(cv_config["inner_splits"]), int(minority_class_count))
    if inner_splits < 2:
        return _record_skip(
            experiment=experiment,
            model_label=model_label,
            validation_scheme=validation_scheme,
            split_id=split_id,
            holdout_group=holdout_group,
            status="skipped_insufficient_inner_cv",
            skip_reason="训练集中少数类样本不足，无法执行内层交叉验证。",
            n_train=len(train_frame),
            n_test=len(test_frame),
        )

    train_ready, test_ready, selected_features = _prepare_experiment_features(
        spec=spec,
        train_frame=train_x,
        test_frame=test_x,
        y_train=y_train,
        cv_config=cv_config,
    )
    estimator, grid = _build_estimator(spec.model_family)
    inner_cv = StratifiedKFold(
        n_splits=inner_splits,
        shuffle=True,
        random_state=int(cv_config["random_state"]),
    )
    search = GridSearchCV(
        estimator=estimator,
        param_grid=grid,
        scoring="roc_auc",
        cv=inner_cv,
        n_jobs=1,
        refit=True,
        error_score="raise",
    )
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=FutureWarning,
            message=".*'penalty' was deprecated.*",
        )
        search.fit(train_ready, y_train)

    train_score = search.predict_proba(train_ready)[:, 1]
    test_score = search.predict_proba(test_ready)[:, 1]
    return {
        "experiment": experiment,
        "model_label": model_label,
        "validation_scheme": validation_scheme,
        "split_id": split_id,
        "holdout_group": holdout_group,
        "status": "completed",
        "skip_reason": "",
        "auc": _safe_auc(y_test, test_score),
        "train_auc": _safe_auc(y_train, train_score),
        "selected_feature_count": len(selected_features),
        "n_train": len(train_frame),
        "n_test": len(test_frame),
        "train_phase": "baseline",
        "test_phase": "outphase",
    }


def _run_outphase_repeated_random_holdout(
    *,
    baseline_frame: pd.DataFrame,
    outphase_frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    random_holdout_splits: int,
    test_size: float,
    random_state: int,
) -> list[dict[str, Any]]:
    baseline_aligned, outphase_aligned = _align_paired_frames(baseline_frame, outphase_frame)
    y = (baseline_aligned["Group"].astype(str) == positive_label).astype(int).to_numpy()
    splitter = StratifiedShuffleSplit(
        n_splits=random_holdout_splits,
        test_size=test_size,
        random_state=random_state,
    )

    rows: list[dict[str, Any]] = []
    for index, (train_idx, test_idx) in enumerate(splitter.split(baseline_aligned, y), start=1):
        rows.append(
            _fit_and_score_transfer_split(
                train_frame=baseline_aligned.iloc[train_idx].reset_index(drop=True),
                test_frame=outphase_aligned.iloc[test_idx].reset_index(drop=True),
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                validation_scheme="outphase_repeated_random_holdout",
                split_id=f"outphase_random_holdout_{index}",
                holdout_group=None,
            )
        )
    return rows


def _run_outphase_leave_one_group_out(
    *,
    baseline_frame: pd.DataFrame,
    outphase_frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    group_values: pd.Series,
    validation_scheme: str,
) -> list[dict[str, Any]]:
    baseline_aligned, outphase_aligned = _align_paired_frames(baseline_frame, outphase_frame)
    group_frame = _coerce_id_to_string(
        pd.DataFrame({"ID": baseline_frame["ID"].astype(str).tolist(), "group_value": group_values.astype(str).tolist()}),
        "ID",
    )
    aligned_groups = (
        baseline_aligned[["ID"]]
        .merge(group_frame, on="ID", how="left")["group_value"]
        .reset_index(drop=True)
    )
    rows: list[dict[str, Any]] = []
    for group_name in sorted(aligned_groups.dropna().astype(str).unique()):
        test_mask = aligned_groups.astype(str).eq(group_name).to_numpy()
        rows.append(
            _fit_and_score_transfer_split(
                train_frame=baseline_aligned.loc[~test_mask].reset_index(drop=True),
                test_frame=outphase_aligned.loc[test_mask].reset_index(drop=True),
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                validation_scheme=validation_scheme,
                split_id=f"{validation_scheme}_{group_name}",
                holdout_group=str(group_name),
            )
        )
    return rows


def _run_outphase_fixed_group_split(
    *,
    baseline_frame: pd.DataFrame,
    outphase_frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    group_values: pd.Series,
    validation_scheme: str,
    test_groups: list[str],
    holdout_group_label: str,
    split_label: str,
) -> list[dict[str, Any]]:
    baseline_aligned, outphase_aligned = _align_paired_frames(baseline_frame, outphase_frame)
    group_frame = _coerce_id_to_string(
        pd.DataFrame({"ID": baseline_frame["ID"].astype(str).tolist(), "group_value": group_values.astype(str).tolist()}),
        "ID",
    )
    aligned_groups = baseline_aligned[["ID"]].merge(group_frame, on="ID", how="left")["group_value"].reset_index(drop=True)
    test_mask = aligned_groups.astype(str).isin([str(group_name) for group_name in test_groups]).to_numpy()
    return [
        _fit_and_score_transfer_split(
            train_frame=baseline_aligned.loc[~test_mask].reset_index(drop=True),
            test_frame=outphase_aligned.loc[test_mask].reset_index(drop=True),
            spec=spec,
            experiment=experiment,
            model_label=model_label,
            positive_label=positive_label,
            cv_config=cv_config,
            validation_scheme=validation_scheme,
            split_id=f"{validation_scheme}_{split_label}",
            holdout_group=holdout_group_label,
        )
    ]


def _summarize_rows(frame: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, Any]] = []
    for (
        experiment,
        model_label,
        validation_scheme,
        train_phase,
        test_phase,
    ), group in frame.groupby(
        ["experiment", "model_label", "validation_scheme", "train_phase", "test_phase"],
        dropna=False,
    ):
        completed = group[group["status"] == "completed"]
        summary_rows.append(
            {
                "experiment": experiment,
                "model_label": model_label,
                "validation_scheme": validation_scheme,
                "train_phase": train_phase,
                "test_phase": test_phase,
                "n_total_splits": int(len(group)),
                "n_completed": int(len(completed)),
                "n_skipped": int(len(group) - len(completed)),
                "mean_auc": float(completed["auc"].mean()) if not completed.empty else np.nan,
                "std_auc": float(completed["auc"].std(ddof=0)) if not completed.empty else np.nan,
                "mean_train_auc": float(completed["train_auc"].mean()) if not completed.empty else np.nan,
                "mean_gap": float((completed["train_auc"] - completed["auc"]).mean()) if not completed.empty else np.nan,
                "mean_selected_feature_count": float(completed["selected_feature_count"].mean()) if not completed.empty else np.nan,
            }
        )
    return pd.DataFrame(summary_rows).sort_values(["model_label", "validation_scheme"]).reset_index(drop=True)


def _write_outphase_report(
    *,
    output_dir: Path,
    summary: pd.DataFrame,
    metadata: dict[str, Any],
    grouped_validation_note: str | None = None,
) -> str:
    path = output_dir / "outphase_validation.md"
    lines = [
        "# 出组 / 干预后 out-phase 验证",
        "",
        "## 方法定位",
        "",
        "- 本模块是**内部时相验证**：训练数据来自基线时点，测试数据来自同一批受试者的 out / 干预后时点。",
        "- 这里**不是外部验证**，也不应写成 external validation。",
        "- 为避免同一受试者在训练与测试同时出现，所有 split 都采用“基线训练 ID 集 / out-phase 测试 ID 集”配对评估。",
        "",
    ]
    if grouped_validation_note:
        lines.extend(
            [
                "## grouped split 说明",
                "",
                f"- {grouped_validation_note}",
                "",
            ]
        )
    lines.extend(
        [
            "## 数据接入概况",
            "",
            f"- overlap_id_count: {metadata.get('overlap_id_count', 0)}",
            f"- out_lipid 内置 Group 与主标签一致率: {metadata.get('out_lipid_group_match_rate', float('nan')):.4f}"
            if pd.notna(metadata.get("out_lipid_group_match_rate"))
            else "- out_lipid 内置 Group：未提供或无法计算一致率。",
            f"- out_lipid Group mismatch count: {metadata.get('out_lipid_group_mismatch_count', 0)}",
            f"- clinical anchor mapping: {metadata.get('clinical_anchor_mapping', {})}",
        ]
    )
    missing_sources = metadata.get("missing_anchor_sources") or []
    if missing_sources:
        lines.extend(
            [
                "",
                "## 缺失的 out-phase anchor 映射",
                "",
                *(f"- {item}" for item in missing_sources),
            ]
        )

    lines.extend(
        [
            "",
            "## 结果汇总",
            "",
            _format_markdown_table(summary),
            "",
            "> 解读边界：如果 out-phase 下仍保留一定区分趋势，只能支持“差异可能具有一定时相稳定性/个体异质性延续”，不能等同于外部人群复现。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def run_outphase_validation(
    *,
    cohorts: AnalysisCohorts,
    group_frame: pd.DataFrame,
    positive_label: str,
    output_dir: str | Path,
    model_configs: list[dict[str, Any]],
    outphase_config: dict[str, Any],
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not outphase_config.get("enabled", False):
        return {
            "status": "blocked",
            "blockers": ["outphase_validation 未启用"],
        }

    required_paths = {
        "out_lipid_path": outphase_config.get("out_lipid_path"),
        "out_clinical_full_path": outphase_config.get("out_clinical_full_path"),
    }
    blockers = [
        f"缺少 {name}"
        for name, value in required_paths.items()
        if not value
    ]
    blockers.extend(
        f"{name} 不存在：{value}"
        for name, value in required_paths.items()
        if value and not Path(value).exists()
    )
    if blockers:
        return {
            "status": "blocked",
            "blockers": blockers,
        }

    outphase_cohorts, metadata = build_outphase_analysis_cohorts(
        group_frame=group_frame,
        out_lipid_path=required_paths["out_lipid_path"],
        out_clinical_full_path=required_paths["out_clinical_full_path"],
        clinical_anchor_mapping=outphase_config.get("clinical_anchor_mapping"),
    )
    registry = build_default_experiment_registry()
    global_cv_config = _merge_cv_config(outphase_config.get("cv_config"))

    rows: list[dict[str, Any]] = []
    exported_group_mapping_csv: str | None = None
    grouped_validation_note: str | None = None
    for model_config in model_configs:
        experiment = model_config["experiment"]
        model_label = model_config["model_label"]
        spec = registry[experiment]
        baseline_frame = getattr(cohorts, spec.cohort_key)
        outphase_frame = getattr(outphase_cohorts, spec.cohort_key)
        cv_config = global_cv_config.copy()
        cv_config.update(model_config.get("cv_overrides") or {})

        baseline_aligned, outphase_aligned = _align_paired_frames(baseline_frame, outphase_frame)
        if baseline_aligned.empty or outphase_aligned.empty:
            rows.append(
                _record_skip(
                    experiment=experiment,
                    model_label=model_label,
                    validation_scheme="outphase_repeated_random_holdout",
                    split_id="outphase_random_holdout_1",
                    holdout_group=None,
                    status="skipped_no_overlap",
                    skip_reason="基线队列与 out-phase 队列没有可用重叠 ID。",
                    n_train=0,
                    n_test=0,
                )
            )
            continue

        rows.extend(
            _run_outphase_repeated_random_holdout(
                baseline_frame=baseline_frame,
                outphase_frame=outphase_frame,
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                random_holdout_splits=int(outphase_config.get("random_holdout_splits", 30)),
                test_size=float(outphase_config.get("test_size", 0.2)),
                random_state=int(outphase_config.get("random_state", 42)),
            )
        )
        pseudo_external = outphase_config.get("pseudo_external") or {}
        if pseudo_external.get("enabled", True):
            group_values, group_meta = resolve_group_series(
                baseline_frame,
                group_by=str(pseudo_external.get("group_by", "id_prefix")),
                mapping_path=pseudo_external.get("mapping_path"),
                mapping_sheet_name=str(pseudo_external.get("mapping_sheet_name") or "运动强度分组_401人"),
            )
            mapping_frame = group_meta.get("mapping_frame")
            if mapping_frame is not None and exported_group_mapping_csv is None:
                mapping_path = output_path / "id_school_intensity_mapping.csv"
                mapping_frame.to_csv(mapping_path, index=False)
                exported_group_mapping_csv = str(mapping_path)
            if grouped_validation_note is None:
                if group_meta.get("group_by") == "school":
                    grouped_validation_note = (
                        "本轮已接入真实 school grouped split（leave-one-school-out / outphase leave-one-school-out）；"
                        "这仍属于内部 grouped validation / internal temporal validation，不是 external validation。"
                    )
                else:
                    grouped_validation_note = (
                        "本轮 grouped split 仍基于 ID prefix，只能作为弱 proxy，不是 external validation。"
                    )
            rows.extend(
                _run_outphase_leave_one_group_out(
                    baseline_frame=baseline_frame,
                    outphase_frame=outphase_frame,
                    spec=spec,
                    experiment=experiment,
                    model_label=model_label,
                    positive_label=positive_label,
                    cv_config=cv_config,
                    group_values=group_values,
                    validation_scheme=f"outphase_{group_meta['validation_scheme']}",
                )
            )
            fixed_group_split = resolve_fixed_group_split(
                group_values,
                group_meta=group_meta,
                fixed_group_split_config=pseudo_external.get("fixed_group_split"),
            )
            if fixed_group_split is not None:
                rows.extend(
                    _run_outphase_fixed_group_split(
                        baseline_frame=baseline_frame,
                        outphase_frame=outphase_frame,
                        spec=spec,
                        experiment=experiment,
                        model_label=model_label,
                        positive_label=positive_label,
                        cv_config=cv_config,
                        group_values=group_values,
                        validation_scheme=f"outphase_{fixed_group_split['validation_scheme']}",
                        test_groups=list(fixed_group_split["test_groups"]),
                        holdout_group_label=str(fixed_group_split["holdout_group_label"]),
                        split_label=str(fixed_group_split["split_label"]),
                    )
                )

    folds = pd.DataFrame(rows)
    summary = _summarize_rows(folds)

    fold_path = output_path / "outphase_validation_fold_metrics.csv"
    summary_path = output_path / "outphase_validation_summary.csv"
    folds.to_csv(fold_path, index=False)
    summary.to_csv(summary_path, index=False)
    report_path = _write_outphase_report(
        output_dir=output_path,
        summary=summary,
        metadata=metadata,
        grouped_validation_note=grouped_validation_note,
    )

    result = {
        "status": "completed",
        "outphase_validation_fold_metrics_csv": str(fold_path),
        "outphase_validation_summary_csv": str(summary_path),
        "outphase_validation_markdown": report_path,
        "metadata": metadata,
        "blockers": [],
    }
    if exported_group_mapping_csv:
        result["group_mapping_csv"] = exported_group_mapping_csv
    return result
