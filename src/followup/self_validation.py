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
from src.models.run_nested_cv import (
    _build_estimator,
    _merge_cv_config,
    _prepare_experiment_features,
    build_default_experiment_registry,
)


def _safe_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


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
    }


def _fit_and_score_split(
    *,
    frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    validation_scheme: str,
    split_id: str,
    holdout_group: str | None,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
) -> dict[str, Any]:
    y = (frame["Group"].astype(str) == positive_label).astype(int).to_numpy()
    drop_columns = [column for column in ["ID", "Group", "NAME"] if column in frame.columns]
    X = frame.drop(columns=drop_columns).copy()

    train_frame = X.iloc[train_idx].reset_index(drop=True)
    test_frame = X.iloc[test_idx].reset_index(drop=True)
    y_train = y[train_idx]
    y_test = y[test_idx]

    if len(np.unique(y_train)) < 2:
        return _record_skip(
            experiment=experiment,
            model_label=model_label,
            validation_scheme=validation_scheme,
            split_id=split_id,
            holdout_group=holdout_group,
            status="skipped_single_class_train",
            skip_reason="训练集只有一个类别，无法调参和建模。",
            n_train=len(train_idx),
            n_test=len(test_idx),
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
            n_train=len(train_idx),
            n_test=len(test_idx),
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
            n_train=len(train_idx),
            n_test=len(test_idx),
        )

    train_ready, test_ready, selected_features = _prepare_experiment_features(
        spec=spec,
        train_frame=train_frame,
        test_frame=test_frame,
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
        "n_train": len(train_idx),
        "n_test": len(test_idx),
    }


def _run_repeated_random_holdout(
    *,
    frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    random_holdout_splits: int,
    test_size: float,
    random_state: int,
) -> list[dict[str, Any]]:
    y = (frame["Group"].astype(str) == positive_label).astype(int).to_numpy()
    splitter = StratifiedShuffleSplit(
        n_splits=random_holdout_splits,
        test_size=test_size,
        random_state=random_state,
    )
    return [
        _fit_and_score_split(
            frame=frame,
            spec=spec,
            experiment=experiment,
            model_label=model_label,
            positive_label=positive_label,
            cv_config=cv_config,
            validation_scheme="repeated_random_holdout",
            split_id=f"random_holdout_{idx}",
            holdout_group=None,
            train_idx=train_idx,
            test_idx=test_idx,
        )
        for idx, (train_idx, test_idx) in enumerate(splitter.split(frame, y), start=1)
    ]


def _run_leave_one_group_out(
    *,
    frame: pd.DataFrame,
    spec,
    experiment: str,
    model_label: str,
    positive_label: str,
    cv_config: dict[str, Any],
    group_values: pd.Series,
    validation_scheme: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_name in sorted(group_values.dropna().astype(str).unique()):
        test_mask = group_values.astype(str).eq(group_name).to_numpy()
        train_idx = np.flatnonzero(~test_mask)
        test_idx = np.flatnonzero(test_mask)
        rows.append(
            _fit_and_score_split(
                frame=frame,
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                validation_scheme=validation_scheme,
                split_id=f"{validation_scheme}_{group_name}",
                holdout_group=str(group_name),
                train_idx=train_idx,
                test_idx=test_idx,
            )
        )
    return rows


def _run_fixed_group_split(
    *,
    frame: pd.DataFrame,
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
    normalized_groups = group_values.astype(str)
    test_mask = normalized_groups.isin([str(group_name) for group_name in test_groups]).to_numpy()
    train_idx = np.flatnonzero(~test_mask)
    test_idx = np.flatnonzero(test_mask)
    return [
        _fit_and_score_split(
            frame=frame,
            spec=spec,
            experiment=experiment,
            model_label=model_label,
            positive_label=positive_label,
            cv_config=cv_config,
            validation_scheme=validation_scheme,
            split_id=f"{validation_scheme}_{split_label}",
            holdout_group=holdout_group_label,
            train_idx=train_idx,
            test_idx=test_idx,
        )
    ]


def _summarize_rows(frame: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, Any]] = []
    for (experiment, model_label, validation_scheme), group in frame.groupby(
        ["experiment", "model_label", "validation_scheme"], dropna=False
    ):
        completed = group[group["status"] == "completed"]
        summary_rows.append(
            {
                "experiment": experiment,
                "model_label": model_label,
                "validation_scheme": validation_scheme,
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


def run_self_validation(
    *,
    cohorts: AnalysisCohorts,
    positive_label: str,
    output_dir: str | Path,
    model_configs: list[dict[str, Any]],
    self_validation_config: dict[str, Any],
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    registry = build_default_experiment_registry()
    global_cv_config = _merge_cv_config(self_validation_config.get("cv_config"))

    rows: list[dict[str, Any]] = []
    exported_group_mapping_csv: str | None = None
    for model_config in model_configs:
        experiment = model_config["experiment"]
        model_label = model_config["model_label"]
        spec = registry[experiment]
        frame = getattr(cohorts, spec.cohort_key)
        cv_config = global_cv_config.copy()
        cv_config.update(model_config.get("cv_overrides") or {})

        rows.extend(
            _run_repeated_random_holdout(
                frame=frame,
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                random_holdout_splits=int(self_validation_config.get("random_holdout_splits", 30)),
                test_size=float(self_validation_config.get("test_size", 0.2)),
                random_state=int(self_validation_config.get("random_state", 42)),
            )
        )
        pseudo_external = self_validation_config.get("pseudo_external") or {}
        if pseudo_external.get("enabled", True):
            group_values, group_meta = resolve_group_series(
                frame,
                group_by=str(pseudo_external.get("group_by", "id_prefix")),
                mapping_path=pseudo_external.get("mapping_path"),
                mapping_sheet_name=str(pseudo_external.get("mapping_sheet_name") or "运动强度分组_401人"),
            )
            mapping_frame = group_meta.get("mapping_frame")
            if mapping_frame is not None and exported_group_mapping_csv is None:
                mapping_path = output_path / "id_school_intensity_mapping.csv"
                mapping_frame.to_csv(mapping_path, index=False)
                exported_group_mapping_csv = str(mapping_path)
            rows.extend(
                _run_leave_one_group_out(
                    frame=frame,
                    spec=spec,
                    experiment=experiment,
                    model_label=model_label,
                    positive_label=positive_label,
                    cv_config=cv_config,
                    group_values=group_values,
                    validation_scheme=str(group_meta["validation_scheme"]),
                )
            )
            fixed_group_split = resolve_fixed_group_split(
                group_values,
                group_meta=group_meta,
                fixed_group_split_config=pseudo_external.get("fixed_group_split"),
            )
            if fixed_group_split is not None:
                rows.extend(
                    _run_fixed_group_split(
                        frame=frame,
                        spec=spec,
                        experiment=experiment,
                        model_label=model_label,
                        positive_label=positive_label,
                        cv_config=cv_config,
                        group_values=group_values,
                        validation_scheme=str(fixed_group_split["validation_scheme"]),
                        test_groups=list(fixed_group_split["test_groups"]),
                        holdout_group_label=str(fixed_group_split["holdout_group_label"]),
                        split_label=str(fixed_group_split["split_label"]),
                    )
                )

    folds = pd.DataFrame(rows)
    summary = _summarize_rows(folds)

    fold_path = output_path / "self_validation_fold_metrics.csv"
    summary_path = output_path / "self_validation_summary.csv"
    folds.to_csv(fold_path, index=False)
    summary.to_csv(summary_path, index=False)

    result = {
        "self_validation_fold_metrics_csv": str(fold_path),
        "self_validation_summary_csv": str(summary_path),
    }
    if exported_group_mapping_csv:
        result["group_mapping_csv"] = exported_group_mapping_csv
    return result
