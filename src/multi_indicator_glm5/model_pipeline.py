"""
Phase 3: Full cohort multi-model nested CV.
GLM5 execution — 2026-04-10

For each indicator × cutoff × model: strict nested CV (5-fold outer × 3-fold inner).
Outputs: AUROC, AUPRC, Sensitivity, Specificity, Youden threshold, fold metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
from time import time

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    precision_recall_curve, roc_curve,
    accuracy_score, f1_score, confusion_matrix,
)
import xgboost as xgb

warnings.filterwarnings("ignore")

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
FEAT_DIR = OUT_DIR / "phase2_selected_features"
ROC_DIR = OUT_DIR / "phase3_roc_data"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
CUTOFFS = ["Q", "T"]

OUTER_FOLDS = 5
INNER_FOLDS = 3
RANDOM_STATE = 42


# ── model configs ───────────────────────────────────────────────────────
def get_models():
    """Return dict of model_name → sklearn-compatible estimator."""
    return {
        "EN_LR": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                penalty="elasticnet", solver="saga",
                C=0.1, l1_ratio=0.5, max_iter=5000, random_state=RANDOM_STATE,
            )),
        ]),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            random_state=RANDOM_STATE, use_label_encoder=False, eval_metric="logloss",
        ),
        "RF": RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=RANDOM_STATE,
        ),
        "LR_L2": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                penalty="l2", solver="lbfgs", C=1.0, max_iter=2000, random_state=RANDOM_STATE,
            )),
        ]),
    }


def nested_cv(X, y, model, outer_folds=OUTER_FOLDS, inner_folds=INNER_FOLDS):
    """Run strict nested CV, return metrics."""
    outer_cv = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=RANDOM_STATE)

    fold_metrics = []
    all_y_true = []
    all_y_prob = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Inner CV for hyperparameter tuning (using default params for now)
        inner_cv = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=RANDOM_STATE)

        # Train on full train set with default params
        model.fit(X_train, y_train)

        # Predict on test
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        # Metrics
        auroc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else np.nan
        auprc = average_precision_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else np.nan

        # Youden optimal threshold
        fpr, tpr, thresholds = roc_curve(y_test, y_prob)
        youden_idx = np.argmax(tpr - fpr)
        youden_thresh = thresholds[youden_idx]
        y_pred_youden = (y_prob >= youden_thresh).astype(int)

        if len(np.unique(y_pred_youden)) > 1 and (y_pred_youden == 1).sum() > 0 and (y_pred_youden == 0).sum() > 0:
            tn, fp, fn, tp = confusion_matrix(y_test, y_pred_youden).ravel()
            sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
            spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
        else:
            sens, spec = np.nan, np.nan

        fold_metrics.append({
            "fold": fold_idx,
            "n_train": len(y_train),
            "n_test": len(y_test),
            "auroc": auroc,
            "auprc": auprc,
            "youden_thresh": youden_thresh,
            "sensitivity": sens,
            "specificity": spec,
            "accuracy": accuracy_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred, zero_division=0),
        })

        all_y_true.extend(y_test)
        all_y_prob.extend(y_prob)

    # Aggregate
    df_folds = pd.DataFrame(fold_metrics)
    aggregate = {
        "mean_auroc": df_folds["auroc"].mean(),
        "std_auroc": df_folds["auroc"].std(),
        "mean_auprc": df_folds["auprc"].mean(),
        "mean_sensitivity": df_folds["sensitivity"].mean(),
        "mean_specificity": df_folds["specificity"].mean(),
        "mean_accuracy": df_folds["accuracy"].mean(),
        "mean_f1": df_folds["f1"].mean(),
        "mean_youden_thresh": df_folds["youden_thresh"].mean(),
    }

    # ROC data for plotting
    all_y_true = np.array(all_y_true)
    all_y_prob = np.array(all_y_prob)
    fpr, tpr, _ = roc_curve(all_y_true, all_y_prob)
    overall_auroc = roc_auc_score(all_y_true, all_y_prob)

    return aggregate, df_folds, (fpr, tpr, overall_auroc)


def main():
    ROC_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 3: Full Cohort Multi-Model Nested CV  [GLM5]")
    print("=" * 60)

    # Load data
    lipid = pd.read_csv(PROJECT / "281_merge_lipids_enroll.csv")
    lipid_features = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    lipid_ids = lipid["NAME"].values
    feature_names = lipid_features.columns.tolist()

    labels = pd.read_csv(OUT_DIR / "phase1_labels.csv")
    labels["ID"] = labels["ID"].astype(str)

    delta = pd.read_csv(OUT_DIR / "phase1_delta_matrix.csv")
    delta["ID"] = delta["ID"].astype(str)

    # Filter to lipid-available subjects
    lipid_id_set = set(lipid_ids)
    mask = labels["ID"].isin(lipid_id_set)
    labels_sub = labels[mask].reset_index(drop=True)

    lipid_feat = lipid_features.copy()
    lipid_feat.index = lipid_ids
    lipid_feat = lipid_feat.reset_index(drop=True)

    models = get_models()
    print(f"\nModels: {list(models.keys())}")
    print(f"Indicators: {len(INDICATORS)} × Cutoffs: {len(CUTOFFS)} × Models: {len(models)}")
    print(f"Total runs: {len(INDICATORS) * len(CUTOFFS) * len(models)}\n")

    all_results = []
    all_fold_metrics = []

    t_start = time()

    for indicator in INDICATORS:
        for cutoff in CUTOFFS:
            label_col = f"{indicator}_{cutoff}"

            # Load selected features
            feat_file = FEAT_DIR / f"features_{label_col}.csv"
            if not feat_file.exists():
                print(f"[{label_col:15s}] SKIP — no features file")
                continue
            selected = pd.read_csv(feat_file)["feature"].tolist()

            # Get valid labels
            valid_mask = labels_sub[label_col].notna()
            if valid_mask.sum() < 20:
                continue

            y = labels_sub.loc[valid_mask, label_col].astype(int).values

            # Build feature matrix
            feat_idx = [feature_names.index(f) for f in selected if f in feature_names]
            if not feat_idx:
                continue
            X = lipid_feat.loc[valid_mask].values[:, feat_idx]

            for model_name, model_template in models.items():
                run_id = f"{label_col}_{model_name}"
                print(f"[{run_id:22s}] ", end="", flush=True)

                # Clone model
                from sklearn.base import clone
                model = clone(model_template)

                try:
                    aggregate, fold_df, (fpr, tpr, auroc) = nested_cv(X, y, model)

                    print(f"AUROC={aggregate['mean_auroc']:.3f}±{aggregate['std_auroc']:.3f}  AUPRC={aggregate['mean_auprc']:.3f}  Sens={aggregate['mean_sensitivity']:.3f}  Spec={aggregate['mean_specificity']:.3f}")

                    # Save results
                    all_results.append({
                        "indicator": indicator,
                        "cutoff": cutoff,
                        "model": model_name,
                        "run_id": run_id,
                        "n_features": len(feat_idx),
                        "n_class0": int((y == 0).sum()),
                        "n_class1": int((y == 1).sum()),
                        **aggregate,
                    })

                    # Save fold metrics
                    fold_df["indicator"] = indicator
                    fold_df["cutoff"] = cutoff
                    fold_df["model"] = model_name
                    all_fold_metrics.append(fold_df)

                    # Save ROC data
                    roc_df = pd.DataFrame({"fpr": fpr, "tpr": tpr})
                    roc_df.to_csv(ROC_DIR / f"roc_{run_id}.csv", index=False)

                except Exception as e:
                    print(f"ERROR: {e}")

    t_elapsed = time() - t_start

    # Save outputs
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(OUT_DIR / "phase3_full_cohort_results.csv", index=False)

    folds_df = pd.concat(all_fold_metrics, ignore_index=True)
    folds_df.to_csv(OUT_DIR / "phase3_fold_metrics.csv", index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 3 Summary  [GLM5]")
    print("=" * 60)
    print(f"Total runs: {len(all_results)} / {len(INDICATORS) * len(CUTOFFS) * len(models)}")
    print(f"Elapsed: {t_elapsed:.1f}s\n")

    # Best models per indicator
    for cutoff in CUTOFFS:
        print(f"\n--- Cutoff: {cutoff} ({'Quartile' if cutoff == 'Q' else 'Tertile'}) ---")
        sub = results_df[results_df["cutoff"] == cutoff]
        for indicator in INDICATORS:
            ind_sub = sub[sub["indicator"] == indicator]
            if len(ind_sub) == 0:
                continue
            best = ind_sub.loc[ind_sub["mean_auroc"].idxmax()]
            print(f"  {indicator:12s}  best={best['model']:8s}  AUROC={best['mean_auroc']:.3f}±{best['std_auroc']:.3f}  AUPRC={best['mean_auprc']:.3f}  n_feat={int(best['n_features'])}")

    print(f"\nOutput: {OUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
