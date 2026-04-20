from __future__ import annotations

import json
import pickle
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

DEFAULT_CLINICAL_FEATURES = [
    "age_enroll",
    "Gender",
    "BMI",
    "bmi_z_enroll",
    "SFT",
]

MODEL_COMPLEXITY_ORDER = {
    "LR_L2": 0,
    "EN_LR": 1,
    "RF": 2,
    "XGBoost": 3,
}

PROJECT_DIR = Path(__file__).resolve().parents[2]
PHASE1_DIR = PROJECT_DIR / "outputs" / "20260410_multi_indicator_glm5"
FEATURE_DIR = PHASE1_DIR / "phase2_selected_features"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs" / "20260419_multi_type_glm5"
WEBSITE_TRAINED_MODELS_DIR = PROJECT_DIR / "website" / "trained_models"


@dataclass(frozen=True)
class FeatureSpace:
    model_type: str
    X: pd.DataFrame
    features: list[str]
    clinical_features: list[str]
    lipid_features: list[str]


@dataclass(frozen=True)
class EvaluationResult:
    summary: dict
    fold_metrics: pd.DataFrame
    oof_frame: pd.DataFrame
    roc_frame: pd.DataFrame
    calibration: dict
    dca: dict


def _normalize_id_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def output_dir(base_dir: Path) -> Path:
    return base_dir / "outputs" / "20260419_multi_type_glm5"


def align_multi_type_inputs(
    enroll_df: pd.DataFrame,
    lipid_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    clinical_features: Iterable[str] = DEFAULT_CLINICAL_FEATURES,
) -> pd.DataFrame:
    """Align enroll clinical, lipid, and label data on the lipid-available cohort.

    We intentionally use the lipid intersection so clinical/lipid/fusion comparisons
    share the same evaluation frame.
    """
    clinical_features = [column for column in clinical_features if column in enroll_df.columns]
    label_columns = [column for column in labels_df.columns if column != "ID"]

    enroll = enroll_df[["ID", *clinical_features]].copy()
    enroll["ID"] = _normalize_id_series(enroll["ID"])

    lipids = lipid_df.copy().rename(columns={"NAME": "ID"})
    lipids["ID"] = _normalize_id_series(lipids["ID"])

    labels = labels_df[["ID", *label_columns]].copy()
    labels["ID"] = _normalize_id_series(labels["ID"])

    aligned = enroll.merge(lipids, on="ID", how="inner")
    aligned = aligned.merge(labels, on="ID", how="inner")
    aligned = aligned.sort_values("ID").reset_index(drop=True)
    return aligned


def build_feature_spaces(
    aligned_df: pd.DataFrame,
    lipid_features: Iterable[str],
    clinical_features: Iterable[str] = DEFAULT_CLINICAL_FEATURES,
) -> dict[str, dict]:
    clinical = [column for column in clinical_features if column in aligned_df.columns]
    lipids = [column for column in lipid_features if column in aligned_df.columns]

    spaces = {
        "clinical": FeatureSpace(
            model_type="clinical",
            X=aligned_df.loc[:, clinical].copy(),
            features=clinical,
            clinical_features=clinical,
            lipid_features=[],
        ),
        "lipid": FeatureSpace(
            model_type="lipid",
            X=aligned_df.loc[:, lipids].copy(),
            features=lipids,
            clinical_features=[],
            lipid_features=lipids,
        ),
        "fusion": FeatureSpace(
            model_type="fusion",
            X=aligned_df.loc[:, clinical + lipids].copy(),
            features=clinical + lipids,
            clinical_features=clinical,
            lipid_features=lipids,
        ),
    }
    return {
        key: {
            "model_type": value.model_type,
            "X": value.X,
            "features": value.features,
            "clinical_features": value.clinical_features,
            "lipid_features": value.lipid_features,
        }
        for key, value in spaces.items()
    }


def build_input_schema(
    clinical_features: Iterable[str],
    lipid_features: Iterable[str],
) -> list[dict]:
    schema: list[dict] = []
    for feature in clinical_features:
        schema.append({"name": feature, "section": "clinical", "required": True})
    for feature in lipid_features:
        schema.append({"name": feature, "section": "lipid", "required": True})
    return schema


def _sort_rows(rows: pd.DataFrame) -> pd.DataFrame:
    sortable = rows.copy()
    sortable["metric_balance"] = sortable["mean_sensitivity"].fillna(0) + sortable["mean_specificity"].fillna(0)
    sortable["model_complexity"] = sortable["model"].map(MODEL_COMPLEXITY_ORDER).fillna(99)
    return sortable.sort_values(
        by=["mean_auroc", "mean_auprc", "metric_balance", "model_complexity", "model"],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    )


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return float(value)


def _empty_cross_gender_metrics(prefix: str, n_train: int, n_test: int) -> dict:
    return {
        f"{prefix}_auroc": np.nan,
        f"{prefix}_auprc": np.nan,
        f"{prefix}_sens": np.nan,
        f"{prefix}_spec": np.nan,
        f"{prefix}_accuracy": np.nan,
        f"{prefix}_f1": np.nan,
        f"{prefix}_n_train": int(n_train),
        f"{prefix}_n_test": int(n_test),
    }


def _evaluate_transfer_split(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_template,
) -> dict:
    model = clone(model_template)
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]

    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    youden_idx = int(np.argmax(tpr - fpr))
    youden_threshold = float(thresholds[youden_idx])
    y_pred = (y_prob >= youden_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

    sens = float(tp / (tp + fn)) if (tp + fn) > 0 else np.nan
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else np.nan

    return {
        "auroc": float(roc_auc_score(y_test, y_prob)),
        "auprc": float(average_precision_score(y_test, y_prob)),
        "sens": sens,
        "spec": spec,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
    }


def evaluate_cross_gender_transfer(
    X: pd.DataFrame,
    y: Iterable[int],
    gender: Iterable[int],
    model_template,
    min_group_size: int = 10,
) -> dict:
    X_values = X.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    y_values = np.asarray(list(y), dtype=int)
    gender_values = pd.to_numeric(pd.Series(list(gender)), errors="coerce").to_numpy()

    results: dict[str, float | int] = {}
    directions = (("m2f", 0, 1), ("f2m", 1, 0))

    for prefix, train_gender, test_gender in directions:
        train_mask = gender_values == train_gender
        test_mask = gender_values == test_gender
        n_train = int(train_mask.sum())
        n_test = int(test_mask.sum())

        if (
            n_train < min_group_size
            or n_test < min_group_size
            or len(np.unique(y_values[train_mask])) < 2
            or len(np.unique(y_values[test_mask])) < 2
        ):
            results.update(_empty_cross_gender_metrics(prefix, n_train=n_train, n_test=n_test))
            continue

        metrics = _evaluate_transfer_split(
            X_train=X_values[train_mask],
            y_train=y_values[train_mask],
            X_test=X_values[test_mask],
            y_test=y_values[test_mask],
            model_template=model_template,
        )
        results.update(
            {
                f"{prefix}_auroc": metrics["auroc"],
                f"{prefix}_auprc": metrics["auprc"],
                f"{prefix}_sens": metrics["sens"],
                f"{prefix}_spec": metrics["spec"],
                f"{prefix}_accuracy": metrics["accuracy"],
                f"{prefix}_f1": metrics["f1"],
                f"{prefix}_n_train": n_train,
                f"{prefix}_n_test": n_test,
            }
        )

    valid_aurocs = [
        value
        for value in [results.get("m2f_auroc"), results.get("f2m_auroc")]
        if value is not None and not pd.isna(value)
    ]
    results["cross_avg_auroc"] = float(np.mean(valid_aurocs)) if valid_aurocs else np.nan
    return results


def select_best_models(results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty:
        empty = results_df.copy()
        empty["is_best_within_type"] = pd.Series(dtype=object)
        empty["is_best_overall"] = pd.Series(dtype=object)
        return empty

    ranked = _sort_rows(results_df)
    ranked["is_best_within_type"] = [False] * len(ranked)
    ranked["is_best_overall"] = [False] * len(ranked)

    within_type_indices: list[int] = []
    for _, group in ranked.groupby(["indicator", "cutoff", "model_type"], sort=False):
        within_type_indices.append(group.index[0])
    ranked.loc[within_type_indices, "is_best_within_type"] = True

    overall_indices: list[int] = []
    for _, group in ranked.groupby(["indicator", "cutoff"], sort=False):
        overall_indices.append(group.index[0])
    ranked.loc[overall_indices, "is_best_overall"] = True

    ranked["is_best_within_type"] = ranked["is_best_within_type"].astype(object)
    ranked["is_best_overall"] = ranked["is_best_overall"].astype(object)
    return ranked


def compute_calibration_curve_payload(
    y_true: Iterable[int],
    y_prob: Iterable[float],
    n_bins: int = 10,
) -> dict:
    y_true = np.asarray(list(y_true), dtype=float)
    y_prob = np.asarray(list(y_prob), dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bucket_ids = np.digitize(y_prob, bins[1:-1], right=True)

    points = []
    for bucket in range(n_bins):
        mask = bucket_ids == bucket
        if not mask.any():
            continue
        points.append(
            {
                "bin": int(bucket),
                "mean_pred": float(y_prob[mask].mean()),
                "obs_rate": float(y_true[mask].mean()),
                "count": int(mask.sum()),
            }
        )

    brier = float(np.mean((y_prob - y_true) ** 2)) if len(y_true) else np.nan
    return {"points": points, "brier": brier}


def compute_dca_payload(
    y_true: Iterable[int],
    y_prob: Iterable[float],
    thresholds: Iterable[float] | None = None,
) -> dict:
    y_true = np.asarray(list(y_true), dtype=int)
    y_prob = np.asarray(list(y_prob), dtype=float)
    thresholds = list(thresholds or np.linspace(0.05, 0.95, 19))

    positives = y_true.sum()
    n = len(y_true)
    prevalence = positives / n if n else 0.0

    model_points = []
    treat_all = []
    valid_thresholds = [t for t in thresholds if 0 < t < 1]
    for threshold in valid_thresholds:
        pred = (y_prob >= threshold).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        harm = threshold / (1 - threshold)
        model_nb = (tp / n) - (fp / n) * harm if n else 0.0
        all_nb = prevalence - (1 - prevalence) * harm
        model_points.append({"threshold": float(threshold), "net_benefit": float(model_nb)})
        treat_all.append({"threshold": float(threshold), "net_benefit": float(all_nb)})

    return {
        "model": model_points,
        "treat_all": treat_all,
        "treat_none": [{"threshold": float(t), "net_benefit": 0.0} for t in valid_thresholds],
    }


def build_metadata_entry(
    model_key: str,
    result_row: dict,
    clinical_features: list[str],
    lipid_features: list[str],
    sample_values: dict[str, float],
    calibration: dict,
    dca: dict,
) -> dict:
    combined_features = clinical_features + lipid_features
    performance = {
        "full_auroc": float(result_row.get("mean_auroc", 0) or 0),
        "full_auprc": float(result_row.get("mean_auprc", 0) or 0),
        "full_sens": float(result_row.get("mean_sensitivity", 0) or 0),
        "full_spec": float(result_row.get("mean_specificity", 0) or 0),
        "full_accuracy": float(result_row.get("mean_accuracy", 0) or 0),
        "full_f1": float(result_row.get("mean_f1", 0) or 0),
        "full_brier": float(result_row.get("mean_brier", 0) or 0),
        "std_auroc": float(result_row.get("std_auroc", 0) or 0),
        "m2f_auroc": _optional_float(result_row.get("m2f_auroc")),
        "f2m_auroc": _optional_float(result_row.get("f2m_auroc")),
        "cross_avg_auroc": _optional_float(result_row.get("cross_avg_auroc")),
        "m2f_auprc": _optional_float(result_row.get("m2f_auprc")),
        "f2m_auprc": _optional_float(result_row.get("f2m_auprc")),
        "m2f_sens": _optional_float(result_row.get("m2f_sens")),
        "f2m_sens": _optional_float(result_row.get("f2m_sens")),
        "m2f_spec": _optional_float(result_row.get("m2f_spec")),
        "f2m_spec": _optional_float(result_row.get("f2m_spec")),
        "m2f_accuracy": _optional_float(result_row.get("m2f_accuracy")),
        "f2m_accuracy": _optional_float(result_row.get("f2m_accuracy")),
        "m2f_f1": _optional_float(result_row.get("m2f_f1")),
        "f2m_f1": _optional_float(result_row.get("f2m_f1")),
        "m2f_n_train": int(result_row.get("m2f_n_train", 0) or 0),
        "m2f_n_test": int(result_row.get("m2f_n_test", 0) or 0),
        "f2m_n_train": int(result_row.get("f2m_n_train", 0) or 0),
        "f2m_n_test": int(result_row.get("f2m_n_test", 0) or 0),
    }
    return {
        "key": model_key,
        "indicator": result_row.get("indicator"),
        "cutoff": result_row.get("cutoff"),
        "group": result_row.get("cutoff"),
        "model": result_row.get("model"),
        "model_name": result_row.get("model"),
        "model_type": result_row.get("model_type"),
        "features": combined_features,
        "clinical_features": clinical_features,
        "lipid_features": lipid_features,
        "input_schema": build_input_schema(clinical_features, lipid_features),
        "sample_values": sample_values,
        "performance": performance,
        "full_auc": performance["full_auroc"],
        "m2f_auc": performance["m2f_auroc"],
        "f2m_auc": performance["f2m_auroc"],
        "cross_avg_auc": performance["cross_avg_auroc"],
        "full_auprc": performance["full_auprc"],
        "sens": performance["full_sens"],
        "spec": performance["full_spec"],
        "n_feat": len(combined_features),
        "is_best_within_type": bool(result_row.get("is_best_within_type", False)),
        "is_best_overall": bool(result_row.get("is_best_overall", False)),
        "calibration": calibration,
        "dca": dca,
    }


def get_models(random_state: int = 42) -> dict[str, Pipeline | xgb.XGBClassifier]:
    return {
        "EN_LR": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        penalty="elasticnet",
                        solver="saga",
                        C=0.1,
                        l1_ratio=0.5,
                        max_iter=5000,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "clf",
                    xgb.XGBClassifier(
                        n_estimators=200,
                        max_depth=4,
                        learning_rate=0.05,
                        random_state=random_state,
                        use_label_encoder=False,
                        eval_metric="logloss",
                    ),
                ),
            ]
        ),
        "RF": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=10,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "LR_L2": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        penalty="l2",
                        solver="lbfgs",
                        C=1.0,
                        max_iter=2000,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }


def load_selected_lipid_features(feature_dir: Path, indicator: str, cutoff: str) -> list[str]:
    feature_path = feature_dir / f"features_{indicator}_{cutoff}.csv"
    if not feature_path.exists():
        return []
    feature_df = pd.read_csv(feature_path)
    if "feature" not in feature_df.columns:
        return []
    return feature_df["feature"].dropna().astype(str).tolist()


def load_training_sources(project_dir: Path = PROJECT_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    enroll = pd.read_csv(project_dir / "287_enroll_data_clean.csv")
    lipid = pd.read_csv(project_dir / "281_merge_lipids_enroll.csv")
    labels = pd.read_csv(PHASE1_DIR / "phase1_labels.csv")
    return enroll, lipid, labels


def prepare_aligned_dataset(
    project_dir: Path = PROJECT_DIR,
    clinical_features: Iterable[str] = DEFAULT_CLINICAL_FEATURES,
) -> pd.DataFrame:
    enroll, lipid, labels = load_training_sources(project_dir)
    return align_multi_type_inputs(enroll, lipid, labels, clinical_features=clinical_features)


def evaluate_model_cv(
    X: pd.DataFrame,
    y: np.ndarray,
    model_template,
    outer_splits: int = 5,
    random_state: int = 42,
) -> EvaluationResult:
    X_values = X.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    y_values = np.asarray(y, dtype=int)
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=random_state)

    fold_rows: list[dict] = []
    oof_prob = np.zeros(len(y_values), dtype=float)
    oof_true = np.zeros(len(y_values), dtype=int)

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X_values, y_values), start=1):
        model = clone(model_template)
        X_train, X_test = X_values[train_idx], X_values[test_idx]
        y_train, y_test = y_values[train_idx], y_values[test_idx]
        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        fpr, tpr, thresholds = roc_curve(y_test, y_prob)
        youden_idx = int(np.argmax(tpr - fpr))
        youden_threshold = float(thresholds[youden_idx])
        youden_pred = (y_prob >= youden_threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, youden_pred).ravel()
        sens = float(tp / (tp + fn)) if (tp + fn) > 0 else np.nan
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else np.nan

        fold_rows.append(
            {
                "fold": fold_idx,
                "mean_auroc": float(roc_auc_score(y_test, y_prob)),
                "mean_auprc": float(average_precision_score(y_test, y_prob)),
                "mean_sensitivity": sens,
                "mean_specificity": spec,
                "mean_accuracy": float(accuracy_score(y_test, y_pred)),
                "mean_f1": float(f1_score(y_test, y_pred, zero_division=0)),
                "mean_brier": float(brier_score_loss(y_test, y_prob)),
                "youden_threshold": youden_threshold,
            }
        )

        oof_prob[test_idx] = y_prob
        oof_true[test_idx] = y_test

    fold_df = pd.DataFrame(fold_rows)
    summary = {
        "mean_auroc": float(fold_df["mean_auroc"].mean()),
        "std_auroc": float(fold_df["mean_auroc"].std(ddof=1)),
        "mean_auprc": float(fold_df["mean_auprc"].mean()),
        "mean_sensitivity": float(fold_df["mean_sensitivity"].mean()),
        "mean_specificity": float(fold_df["mean_specificity"].mean()),
        "mean_accuracy": float(fold_df["mean_accuracy"].mean()),
        "mean_f1": float(fold_df["mean_f1"].mean()),
        "mean_brier": float(fold_df["mean_brier"].mean()),
    }
    oof_frame = pd.DataFrame({"y_true": oof_true, "y_prob": oof_prob})
    roc_fpr, roc_tpr, _ = roc_curve(oof_true, oof_prob)
    roc_frame = pd.DataFrame({"fpr": roc_fpr, "tpr": roc_tpr})
    calibration = compute_calibration_curve_payload(oof_true, oof_prob)
    dca = compute_dca_payload(oof_true, oof_prob)
    return EvaluationResult(
        summary=summary,
        fold_metrics=fold_df,
        oof_frame=oof_frame,
        roc_frame=roc_frame,
        calibration=calibration,
        dca=dca,
    )


def _safe_feature_means(frame: pd.DataFrame, features: list[str]) -> dict[str, float]:
    means: dict[str, float] = {}
    for feature in features:
        if feature not in frame.columns:
            means[feature] = 0.0
            continue
        values = pd.to_numeric(frame[feature], errors="coerce").dropna()
        if feature == "Gender":
            if len(values):
                binary_values = (values > 0.5).astype(int)
                modes = binary_values.mode(dropna=True)
                means[feature] = int(modes.iloc[0]) if len(modes) else 0
            else:
                means[feature] = 0
            continue
        means[feature] = float(values.mean()) if len(values) else 0.0
    return means


def sync_website_assets(export_model_dir: Path, metadata_path: Path, website_dir: Path = WEBSITE_TRAINED_MODELS_DIR) -> None:
    if website_dir.exists():
        shutil.rmtree(website_dir)
    website_dir.mkdir(parents=True, exist_ok=True)
    for pkl_path in export_model_dir.glob("*.pkl"):
        shutil.copy2(pkl_path, website_dir / pkl_path.name)
    shutil.copy2(metadata_path, website_dir / metadata_path.name)


def run_export_pipeline(
    project_dir: Path = PROJECT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    clinical_features: Iterable[str] = DEFAULT_CLINICAL_FEATURES,
    sync_website: bool = True,
    indicators: Iterable[str] | None = None,
    cutoffs: Iterable[str] = ("Q", "T"),
) -> dict[str, Path]:
    aligned = prepare_aligned_dataset(project_dir=project_dir, clinical_features=clinical_features)
    indicators = list(indicators or sorted({column.rsplit("_", 1)[0] for column in aligned.columns if column.endswith(("_Q", "_T"))}))
    cutoffs = list(cutoffs)

    trained_dir = output_dir / "trained_models"
    calibration_dir = output_dir / "calibration"
    dca_dir = output_dir / "dca"
    roc_dir = output_dir / "roc"
    for folder in [output_dir, trained_dir, calibration_dir, dca_dir, roc_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    models = get_models()
    result_rows: list[dict] = []
    fold_rows: list[pd.DataFrame] = []
    artifacts: dict[str, dict] = {}

    for indicator in indicators:
        for cutoff in cutoffs:
            label_column = f"{indicator}_{cutoff}"
            if label_column not in aligned.columns:
                continue
            valid = aligned[label_column].notna()
            subset = aligned.loc[valid].reset_index(drop=True)
            if subset.empty or subset[label_column].nunique() < 2:
                continue

            lipid_features = load_selected_lipid_features(FEATURE_DIR, indicator, cutoff)
            spaces = build_feature_spaces(subset, lipid_features=lipid_features, clinical_features=clinical_features)
            y = subset[label_column].astype(int).to_numpy()

            for model_type, space in spaces.items():
                X = space["X"]
                if X.empty or not space["features"]:
                    continue
                sample_values = _safe_feature_means(subset, space["features"])

                for model_name, model_template in models.items():
                    model_key = f"{indicator}_{cutoff}_{model_type}_{model_name}"
                    evaluation = evaluate_model_cv(X, y, model_template)
                    cross_gender = evaluate_cross_gender_transfer(
                        X=X,
                        y=y,
                        gender=subset["Gender"] if "Gender" in subset.columns else pd.Series([np.nan] * len(subset)),
                        model_template=model_template,
                    )

                    fitted_model = clone(model_template)
                    fitted_model.fit(X.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float), y)
                    with open(trained_dir / f"{model_key}.pkl", "wb") as fh:
                        pickle.dump(fitted_model, fh)

                    evaluation.roc_frame.to_csv(roc_dir / f"{model_key}.csv", index=False)
                    (calibration_dir / f"{model_key}.json").write_text(
                        json.dumps(evaluation.calibration, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    (dca_dir / f"{model_key}.json").write_text(
                        json.dumps(evaluation.dca, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

                    row = {
                        "key": model_key,
                        "indicator": indicator,
                        "cutoff": cutoff,
                        "model_type": model_type,
                        "model": model_name,
                        "n_features": len(space["features"]),
                        "n_class0": int((y == 0).sum()),
                        "n_class1": int((y == 1).sum()),
                        **evaluation.summary,
                        **cross_gender,
                    }
                    result_rows.append(row)
                    fold_df = evaluation.fold_metrics.copy()
                    fold_df["key"] = model_key
                    fold_df["indicator"] = indicator
                    fold_df["cutoff"] = cutoff
                    fold_df["model_type"] = model_type
                    fold_df["model"] = model_name
                    fold_rows.append(fold_df)
                    artifacts[model_key] = {
                        "clinical_features": space["clinical_features"],
                        "lipid_features": space["lipid_features"],
                        "sample_values": sample_values,
                        "calibration": evaluation.calibration,
                        "dca": evaluation.dca,
                    }

    results_df = pd.DataFrame(result_rows)
    ranked_df = select_best_models(results_df)
    ranked_df.to_csv(output_dir / "performance_summary.csv", index=False)
    ranked_df.to_csv(output_dir / "algorithm_comparison.csv", index=False)
    if fold_rows:
        pd.concat(fold_rows, ignore_index=True).to_csv(output_dir / "fold_metrics.csv", index=False)

    metadata: dict[str, dict] = {}
    best_models: dict[str, str] = {}
    comparison_index: dict[str, dict] = {}

    for _, row in ranked_df.iterrows():
        key = row["key"]
        entry = build_metadata_entry(
            model_key=key,
            result_row=row.to_dict(),
            clinical_features=artifacts[key]["clinical_features"],
            lipid_features=artifacts[key]["lipid_features"],
            sample_values=artifacts[key]["sample_values"],
            calibration=artifacts[key]["calibration"],
            dca=artifacts[key]["dca"],
        )
        metadata[key] = entry
        if row["is_best_within_type"]:
            best_models[f"{row['indicator']}|{row['cutoff']}|{row['model_type']}"] = key
        comp_key = f"{row['indicator']}|{row['cutoff']}"
        comparison_index.setdefault(comp_key, {})
        if row["is_best_within_type"]:
            comparison_index[comp_key][row["model_type"]] = key
        if row["is_best_overall"]:
            comparison_index[comp_key]["overall"] = key

    metadata_path = trained_dir / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "best_models.json").write_text(json.dumps(best_models, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "comparison_index.json").write_text(json.dumps(comparison_index, ensure_ascii=False, indent=2), encoding="utf-8")

    if sync_website:
        sync_website_assets(trained_dir, metadata_path)

    return {
        "output_dir": output_dir,
        "trained_dir": trained_dir,
        "metadata_path": metadata_path,
        "performance_summary": output_dir / "performance_summary.csv",
        "algorithm_comparison": output_dir / "algorithm_comparison.csv",
        "fold_metrics": output_dir / "fold_metrics.csv",
    }


def main() -> None:
    paths = run_export_pipeline()
    print("=" * 60)
    print("Multi-type asset export complete")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
