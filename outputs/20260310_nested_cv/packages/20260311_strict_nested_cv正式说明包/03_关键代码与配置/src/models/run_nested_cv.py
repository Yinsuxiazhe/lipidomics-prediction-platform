from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

from src.data.build_cohort import AnalysisCohorts
from src.features.correlation_prune import prune_correlated_features
from src.features.univariate_screen import rank_features_by_auc
from src.preprocess.clinical_filter import clean_clinical_feature_space, select_clinical_columns
from src.preprocess.lipid_transform import LipidPreprocessor


@dataclass(slots=True)
class ExperimentSpec:
    name: str
    cohort_key: str
    model_family: str
    description: str


def build_default_experiment_registry() -> dict[str, ExperimentSpec]:
    experiments = [
        ExperimentSpec(
            name="clinical_slim_logistic",
            cohort_key="group_clinical_slim",
            model_family="logistic_regression",
            description="精简临床基线模型",
        ),
        ExperimentSpec(
            name="lipid_elastic_net",
            cohort_key="group_lipid",
            model_family="elastic_net_logistic",
            description="脂质组弹性网模型",
        ),
        ExperimentSpec(
            name="clinical_full_elastic_net",
            cohort_key="group_clinical_full",
            model_family="elastic_net_logistic",
            description="扩展临床弹性网模型",
        ),
        ExperimentSpec(
            name="fusion_elastic_net",
            cohort_key="group_fusion",
            model_family="elastic_net_logistic",
            description="临床+脂质融合模型",
        ),
        ExperimentSpec(
            name="fusion_full_elastic_net",
            cohort_key="group_fusion_full",
            model_family="elastic_net_logistic",
            description="扩展临床+脂质融合模型",
        ),
    ]
    return {experiment.name: experiment for experiment in experiments}


DEFAULT_CV_CONFIG = {
    "outer_splits": 5,
    "outer_repeats": 1,
    "inner_splits": 3,
    "random_state": 42,
    "lipid_top_k": 30,
    "clinical_top_k": 30,
    "correlation_threshold": 0.95,
    "clinical_missing_threshold": 0.2,
}


def _merge_cv_config(cv_config: dict | None) -> dict:
    merged = DEFAULT_CV_CONFIG.copy()
    if cv_config:
        merged.update(cv_config)
    return merged


def _extract_xy(frame: pd.DataFrame, positive_label: str) -> tuple[pd.DataFrame, np.ndarray]:
    y = (frame["Group"].astype(str) == positive_label).astype(int).to_numpy()
    drop_columns = [column for column in ["ID", "Group", "NAME"] if column in frame.columns]
    X = frame.drop(columns=drop_columns).copy()
    return X, y


def _scale_dataframe(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_numeric = train_frame.apply(pd.to_numeric, errors="coerce")
    test_numeric = test_frame.apply(pd.to_numeric, errors="coerce")

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_imputed = pd.DataFrame(
        imputer.fit_transform(train_numeric),
        columns=train_numeric.columns,
        index=train_numeric.index,
    )
    test_imputed = pd.DataFrame(
        imputer.transform(test_numeric),
        columns=test_numeric.columns,
        index=test_numeric.index,
    )

    train_scaled = pd.DataFrame(
        scaler.fit_transform(train_imputed),
        columns=train_imputed.columns,
        index=train_imputed.index,
    )
    test_scaled = pd.DataFrame(
        scaler.transform(test_imputed),
        columns=test_imputed.columns,
        index=test_imputed.index,
    )
    return train_scaled, test_scaled


def _prepare_clinical_slim_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    train_scaled, test_scaled = _scale_dataframe(train_frame, test_frame)
    return train_scaled, test_scaled, train_scaled.columns.tolist()


def _prepare_lipid_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    y_train: np.ndarray,
    cv_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    preprocessor = LipidPreprocessor()
    train_processed = preprocessor.fit_transform(train_frame)
    test_processed = preprocessor.transform(test_frame)

    ranking = rank_features_by_auc(train_processed, y_train, top_k=cv_config["lipid_top_k"])
    kept = prune_correlated_features(
        train_processed[ranking["feature"].tolist()],
        ranking,
        threshold=cv_config["correlation_threshold"],
    )
    return train_processed[kept], test_processed[kept], kept


def _prepare_clinical_full_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    y_train: np.ndarray,
    cv_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    domain_clean = clean_clinical_feature_space(train_frame, protected_columns=[])
    domain_selected_train = domain_clean.filtered
    domain_selected_test = test_frame.loc[:, domain_clean.selected_features].copy()
    selection = select_clinical_columns(
        domain_selected_train,
        missing_threshold=cv_config["clinical_missing_threshold"],
        required_columns=[],
        protected_columns=[],
    )
    selected_train = selection.filtered
    selected_test = domain_selected_test.loc[:, selection.selected_features].copy()
    ranking = rank_features_by_auc(selected_train, y_train, top_k=cv_config["clinical_top_k"])
    kept = prune_correlated_features(
        selected_train[ranking["feature"].tolist()],
        ranking,
        threshold=cv_config["correlation_threshold"],
    )
    return _scale_dataframe(selected_train[kept], selected_test[kept]) + (kept,)


def _prepare_fusion_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    y_train: np.ndarray,
    cv_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    clinical_candidates = [
        column
        for column in ["age_enroll", "bmi_z_enroll", "SFT", "Gender", "BMI"]
        if column in train_frame.columns
    ]
    lipid_candidates = [column for column in train_frame.columns if column not in clinical_candidates]

    train_clinical, test_clinical = _scale_dataframe(
        train_frame[clinical_candidates],
        test_frame[clinical_candidates],
    )
    train_lipid, test_lipid, lipid_kept = _prepare_lipid_features(
        train_frame[lipid_candidates],
        test_frame[lipid_candidates],
        y_train=y_train,
        cv_config=cv_config,
    )

    train_final = pd.concat([train_clinical, train_lipid], axis=1)
    test_final = pd.concat([test_clinical, test_lipid], axis=1)
    return train_final, test_final, clinical_candidates + lipid_kept


def _prepare_fusion_full_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    y_train: np.ndarray,
    cv_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    domain_clean = clean_clinical_feature_space(train_frame, protected_columns=[])
    clinical_candidates = [column for column in domain_clean.selected_features if column in train_frame.columns]
    lipid_candidates = [column for column in train_frame.columns if column not in clinical_candidates]

    clinical_selection = select_clinical_columns(
        train_frame[clinical_candidates],
        missing_threshold=cv_config["clinical_missing_threshold"],
        required_columns=[column for column in ["age_enroll", "BMI", "bmi_z_enroll", "SFT", "Gender"] if column in clinical_candidates],
        protected_columns=[],
    )
    selected_clinical = clinical_selection.selected_features
    ranked_clinical = rank_features_by_auc(
        train_frame[selected_clinical],
        y_train,
        top_k=min(cv_config["clinical_top_k"], max(1, len(selected_clinical))),
    )
    kept_clinical = prune_correlated_features(
        train_frame[ranked_clinical["feature"].tolist()],
        ranked_clinical,
        threshold=cv_config["correlation_threshold"],
    )

    train_clinical, test_clinical = _scale_dataframe(
        train_frame[kept_clinical],
        test_frame[kept_clinical],
    )
    train_lipid, test_lipid, lipid_kept = _prepare_lipid_features(
        train_frame[lipid_candidates],
        test_frame[lipid_candidates],
        y_train=y_train,
        cv_config=cv_config,
    )
    train_final = pd.concat([train_clinical, train_lipid], axis=1)
    test_final = pd.concat([test_clinical, test_lipid], axis=1)
    return train_final, test_final, kept_clinical + lipid_kept


def _build_estimator(model_family: str) -> tuple[LogisticRegression, dict]:
    if model_family == "logistic_regression":
        estimator = LogisticRegression(
            solver="liblinear",
            class_weight="balanced",
            max_iter=2000,
        )
        grid = {"C": [0.1, 1.0, 10.0]}
        return estimator, grid

    if model_family == "elastic_net_logistic":
        estimator = LogisticRegression(
            solver="saga",
            penalty="elasticnet",
            class_weight="balanced",
            max_iter=5000,
        )
        grid = {"C": [0.1, 1.0, 10.0], "l1_ratio": [0.1, 0.5, 0.9]}
        return estimator, grid

    raise ValueError(f"Unsupported model family: {model_family}")


def _prepare_experiment_features(
    spec: ExperimentSpec,
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    y_train: np.ndarray,
    cv_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    if spec.cohort_key == "group_clinical_slim":
        return _prepare_clinical_slim_features(train_frame, test_frame)
    if spec.cohort_key == "group_lipid":
        return _prepare_lipid_features(train_frame, test_frame, y_train=y_train, cv_config=cv_config)
    if spec.cohort_key == "group_clinical_full":
        return _prepare_clinical_full_features(train_frame, test_frame, y_train=y_train, cv_config=cv_config)
    if spec.cohort_key == "group_fusion":
        return _prepare_fusion_features(train_frame, test_frame, y_train=y_train, cv_config=cv_config)
    if spec.cohort_key == "group_fusion_full":
        return _prepare_fusion_full_features(train_frame, test_frame, y_train=y_train, cv_config=cv_config)

    raise ValueError(f"Unsupported cohort key: {spec.cohort_key}")


def _run_single_experiment(
    frame: pd.DataFrame,
    spec: ExperimentSpec,
    positive_label: str,
    cv_config: dict,
) -> dict:
    X, y = _extract_xy(frame, positive_label=positive_label)
    outer_cv = RepeatedStratifiedKFold(
        n_splits=cv_config["outer_splits"],
        n_repeats=cv_config["outer_repeats"],
        random_state=cv_config["random_state"],
    )

    fold_results = []
    feature_counter: Counter[str] = Counter()

    for fold_index, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        train_frame = X.iloc[train_idx].reset_index(drop=True)
        test_frame = X.iloc[test_idx].reset_index(drop=True)
        y_train = y[train_idx]
        y_test = y[test_idx]

        train_ready, test_ready, selected_features = _prepare_experiment_features(
            spec=spec,
            train_frame=train_frame,
            test_frame=test_frame,
            y_train=y_train,
            cv_config=cv_config,
        )

        estimator, grid = _build_estimator(spec.model_family)
        inner_cv = StratifiedKFold(
            n_splits=cv_config["inner_splits"],
            shuffle=True,
            random_state=cv_config["random_state"] + fold_index,
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

        feature_counter.update(selected_features)
        fold_results.append(
            {
                "fold_index": fold_index,
                "auc": float(roc_auc_score(y_test, test_score)),
                "train_auc": float(roc_auc_score(y_train, train_score)),
                "selected_feature_count": len(selected_features),
                "selected_features": selected_features,
                "best_params": search.best_params_,
                "y_true": y_test.astype(int).tolist(),
                "y_score": test_score.tolist(),
            }
        )

    aucs = [row["auc"] for row in fold_results]
    train_aucs = [row["train_auc"] for row in fold_results]

    return {
        "mean_auc": float(np.mean(aucs)),
        "std_auc": float(np.std(aucs, ddof=0)),
        "mean_train_auc": float(np.mean(train_aucs)),
        "n_outer_folds": len(fold_results),
        "fold_results": fold_results,
        "feature_frequency": dict(feature_counter),
    }


def run_experiments(
    cohorts: AnalysisCohorts | None = None,
    requested_experiments: Iterable[str] | None = None,
    dry_run: bool = True,
    cv_config: dict | None = None,
    positive_label: str = "response",
) -> dict:
    registry = build_default_experiment_registry()
    experiment_names = list(requested_experiments or registry.keys())

    missing = [name for name in experiment_names if name not in registry]
    if missing:
        raise ValueError(f"Unknown experiments requested: {missing}")

    if dry_run:
        return {
            "status": "dry_run",
            "experiments": [asdict(registry[name]) for name in experiment_names],
        }

    if cohorts is None:
        raise ValueError("Non-dry-run experiments require AnalysisCohorts input.")

    config = _merge_cv_config(cv_config)
    results = {}
    for experiment_name in experiment_names:
        spec = registry[experiment_name]
        cohort_frame = getattr(cohorts, spec.cohort_key)
        results[experiment_name] = _run_single_experiment(
            frame=cohort_frame,
            spec=spec,
            positive_label=positive_label,
            cv_config=config,
        )

    return {
        "status": "completed",
        "cv_config": config,
        "results": results,
    }
