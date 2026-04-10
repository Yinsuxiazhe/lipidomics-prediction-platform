"""
Phase 3b: Export trained models as pickle files + Bootstrap 95% CI.
GLM5 execution — 2026-04-10

Trains ALL indicator × cutoff × model combinations on full data,
saves each as .pkl for the Streamlit app to load on demand.
Computes bootstrap CI for AUROC, Sensitivity, Specificity, ROC curve bands.
Saves all metadata as JSON.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import json
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    roc_auc_score, roc_curve, average_precision_score,
    precision_recall_curve, confusion_matrix,
)
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
FEAT_DIR = OUT_DIR / "phase2_selected_features"
MODEL_DIR = OUT_DIR / "trained_models"
ROC_DIR = OUT_DIR / "phase3_roc_data"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
INDICATOR_CN = {
    "BMI": "BMI", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}
CUTOFFS = ["Q", "T"]
RANDOM_STATE = 42
N_BOOTSTRAPS = 1000


def get_models():
    return {
        "EN_LR": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(penalty="elasticnet", solver="saga",
                C=0.1, l1_ratio=0.5, max_iter=5000, random_state=RANDOM_STATE)),
        ]),
        "XGBoost": xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
            random_state=RANDOM_STATE, use_label_encoder=False, eval_metric="logloss"),
        "RF": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=RANDOM_STATE),
        "LR_L2": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(penalty="l2", solver="lbfgs", C=1.0,
                max_iter=2000, random_state=RANDOM_STATE)),
        ]),
    }


# ── Bootstrap CI functions (from MetFIB reference) ──────────────────────

def bootstrap_ci(y_true, y_scores, metric_func, n_bootstraps=N_BOOTSTRAPS, confidence=0.95):
    """Bootstrap CI for any scalar metric."""
    np.random.seed(42)
    scores = []
    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = np.random.randint(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        scores.append(metric_func(y_true[idx], y_scores[idx]))
    scores = np.array(scores)
    alpha = 1.0 - confidence
    lower = float(np.percentile(scores, alpha / 2 * 100))
    upper = float(np.percentile(scores, (1 - alpha / 2) * 100))
    return lower, upper


def compute_roc_ci_band(y_true, y_scores, n_bootstraps=N_BOOTSTRAPS):
    """Bootstrap CI band for the ROC curve (TPR at fixed FPR grid)."""
    np.random.seed(42)
    base_fpr = np.linspace(0, 1, 100)
    tprs = []
    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = np.random.randint(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        fpr, tpr, _ = roc_curve(y_true[idx], y_scores[idx])
        tpr_interp = np.interp(base_fpr, fpr, tpr)
        tpr_interp[0] = 0.0
        tprs.append(tpr_interp)
    tprs = np.array(tprs)
    tpr_lower = np.percentile(tprs, 2.5, axis=0)
    tpr_upper = np.percentile(tprs, 97.5, axis=0)
    return base_fpr.tolist(), tpr_lower.tolist(), tpr_upper.tolist()


def compute_prc_ci_band(y_true, y_scores, n_bootstraps=N_BOOTSTRAPS):
    """Bootstrap CI band for the PRC curve (Precision at fixed Recall grid)."""
    np.random.seed(42)
    base_recall = np.linspace(0, 1, 100)
    precisions = []
    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = np.random.randint(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        prec, rec, _ = precision_recall_curve(y_true[idx], y_scores[idx])
        prec = prec[::-1]
        rec = rec[::-1]
        prec_interp = np.interp(base_recall, rec, prec)
        precisions.append(prec_interp)
    precisions = np.array(precisions)
    prec_lower = np.percentile(precisions, 2.5, axis=0)
    prec_upper = np.percentile(precisions, 97.5, axis=0)
    return base_recall.tolist(), prec_lower.tolist(), prec_upper.tolist()


def compute_sens_spec_at_youden(y_true, y_scores):
    """Compute Sensitivity and Specificity at Youden-optimal threshold."""
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    youden_idx = np.argmax(tpr - fpr)
    youden_thresh = float(thresholds[youden_idx])
    y_pred = (y_scores >= youden_thresh).astype(int)
    if (y_pred == 1).sum() > 0 and (y_pred == 0).sum() > 0:
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        sens = float(tp / (tp + fn)) if (tp + fn) > 0 else None
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else None
    else:
        sens, spec = None, None
    return sens, spec, youden_thresh


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 3b: Export Trained Models + Bootstrap CI  [GLM5]")
    print("=" * 60)

    # Load data
    lipid = pd.read_csv(PROJECT / "281_merge_lipids_enroll.csv")
    lipid_features = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    lipid_ids = lipid["NAME"].values
    feature_names = lipid_features.columns.tolist()

    labels = pd.read_csv(OUT_DIR / "phase1_labels.csv")
    labels["ID"] = labels["ID"].astype(str)

    lipid_id_set = set(lipid_ids)
    mask = labels["ID"].isin(lipid_id_set)
    labels_sub = labels[mask].reset_index(drop=True)

    lipid_feat = lipid_features.copy()
    lipid_feat.index = lipid_ids
    lipid_feat = lipid_feat.reset_index(drop=True)

    models = get_models()
    master = pd.read_csv(OUT_DIR / "phase5_master_results.csv")

    metadata = {}

    for indicator in INDICATORS:
        for cutoff in CUTOFFS:
            label_col = f"{indicator}_{cutoff}"
            feat_file = FEAT_DIR / f"features_{label_col}.csv"
            if not feat_file.exists():
                continue
            selected = pd.read_csv(feat_file)["feature"].tolist()
            feat_idx = [feature_names.index(f) for f in selected if f in feature_names]
            if not feat_idx:
                continue

            valid_mask = labels_sub[label_col].notna()
            y = labels_sub.loc[valid_mask, label_col].astype(int).values
            X = lipid_feat.loc[valid_mask].values[:, feat_idx]

            for model_name, model_template in models.items():
                run_id = f"{label_col}_{model_name}"

                try:
                    model = clone(model_template)
                    model.fit(X, y)

                    # Save model pkl
                    pkl_path = MODEL_DIR / f"{run_id}.pkl"
                    with open(pkl_path, "wb") as f:
                        pickle.dump(model, f)

                    # ── Cross-validation OOF predictions for CI ──
                    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
                    try:
                        oof_probs = cross_val_predict(
                            clone(model_template), X, y, cv=cv, method="predict_proba"
                        )[:, 1]
                    except Exception:
                        oof_probs = model.predict_proba(X)[:, 1]

                    # ── Bootstrap CIs ──
                    auroc_ci = bootstrap_ci(y, oof_probs, roc_auc_score)
                    auprc_ci = bootstrap_ci(y, oof_probs, average_precision_score)

                    sens_point, spec_point, youden_thresh = compute_sens_spec_at_youden(y, oof_probs)
                    if sens_point is not None:
                        sens_ci = bootstrap_ci(y, oof_probs,
                            lambda yt, yp: compute_sens_spec_at_youden(yt, yp)[0])
                        spec_ci = bootstrap_ci(y, oof_probs,
                            lambda yt, yp: compute_sens_spec_at_youden(yt, yp)[1])
                    else:
                        sens_ci = (None, None)
                        spec_ci = (None, None)

                    # ROC CI band
                    roc_fpr_grid, roc_tpr_lower, roc_tpr_upper = compute_roc_ci_band(y, oof_probs)

                    # PRC CI band
                    prc_recall_grid, prc_prec_lower, prc_prec_upper = compute_prc_ci_band(y, oof_probs)

                    # PRC curve data
                    prec_vals, rec_vals, _ = precision_recall_curve(y, oof_probs)
                    prc_points = [{"recall": float(rec_vals[i]), "precision": float(prec_vals[i])}
                                  for i in range(len(prec_vals))]

                    # Get performance from master (nested CV results)
                    row = master[(master["indicator"] == indicator) &
                                 (master["cutoff"] == cutoff) &
                                 (master["model"] == model_name)]
                    perf = {}
                    if len(row) > 0:
                        r = row.iloc[0]
                        perf = {
                            "full_auroc": round(float(r["mean_auroc"]), 4),
                            "full_std": round(float(r["std_auroc"]), 4),
                            "full_auprc": round(float(r["mean_auprc"]), 4),
                            "full_sens": round(float(r["mean_sensitivity"]), 4),
                            "full_spec": round(float(r["mean_specificity"]), 4),
                            "m2f_auroc": round(float(r["m2f_auroc"]), 4) if not np.isnan(r.get("m2f_auroc", np.nan)) else None,
                            "f2m_auroc": round(float(r["f2m_auroc"]), 4) if not np.isnan(r.get("f2m_auroc", np.nan)) else None,
                            "cross_avg": round(float(r["cross_avg_auroc"]), 4) if not np.isnan(r.get("cross_avg_auroc", np.nan)) else None,
                            "is_best": bool(r.get("is_best", False)),
                        }

                    # Add CI data to perf
                    perf["auroc_ci_lower"] = round(auroc_ci[0], 4) if auroc_ci[0] is not None else None
                    perf["auroc_ci_upper"] = round(auroc_ci[1], 4) if auroc_ci[1] is not None else None
                    perf["auprc_ci_lower"] = round(auprc_ci[0], 4) if auprc_ci[0] is not None else None
                    perf["auprc_ci_upper"] = round(auprc_ci[1], 4) if auprc_ci[1] is not None else None
                    perf["sens_point"] = round(sens_point, 4) if sens_point is not None else None
                    perf["spec_point"] = round(spec_point, 4) if spec_point is not None else None
                    perf["sens_ci_lower"] = round(sens_ci[0], 4) if sens_ci[0] is not None else None
                    perf["sens_ci_upper"] = round(sens_ci[1], 4) if sens_ci[1] is not None else None
                    perf["spec_ci_lower"] = round(spec_ci[0], 4) if spec_ci[0] is not None else None
                    perf["spec_ci_upper"] = round(spec_ci[1], 4) if spec_ci[1] is not None else None
                    perf["youden_thresh"] = round(youden_thresh, 4) if youden_thresh is not None else None

                    # Load ROC data
                    roc_file = ROC_DIR / f"roc_{run_id}.csv"
                    roc_points = []
                    if roc_file.exists():
                        roc_df = pd.read_csv(roc_file)
                        roc_points = [{"fpr": float(r2["fpr"]), "tpr": float(r2["tpr"])}
                                      for _, r2 in roc_df.iterrows()]

                    metadata[run_id] = {
                        "indicator": indicator,
                        "indicator_cn": INDICATOR_CN[indicator],
                        "cutoff": cutoff,
                        "model": model_name,
                        "features": selected,
                        "n_features": len(selected),
                        "n_samples": int(len(y)),
                        "n_class0": int((y == 0).sum()),
                        "n_class1": int((y == 1).sum()),
                        "performance": perf,
                        "roc_data": roc_points,
                        "roc_ci_band": {
                            "fpr_grid": roc_fpr_grid,
                            "tpr_lower": roc_tpr_lower,
                            "tpr_upper": roc_tpr_upper,
                        },
                        "prc_data": prc_points,
                        "prc_ci_band": {
                            "recall_grid": prc_recall_grid,
                            "prec_lower": prc_prec_lower,
                            "prec_upper": prc_prec_upper,
                        },
                    }

                    print(f"[{run_id:22s}] AUC={perf.get('full_auroc', '?'):.3f} "
                          f"[{auroc_ci[0]:.3f}-{auroc_ci[1]:.3f}]  "
                          f"Sens={sens_point:.3f} [{sens_ci[0]:.3f}-{sens_ci[1]:.3f}]  "
                          f"Spec={spec_point:.3f} [{spec_ci[0]:.3f}-{spec_ci[1]:.3f}]"
                          if sens_point else f"[{run_id:22s}] AUC={perf.get('full_auroc', '?')}")

                except Exception as e:
                    print(f"[{run_id:22s}] ERROR: {e}")

    # Save metadata
    meta_path = MODEL_DIR / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"\nMetadata: {meta_path}")

    print(f"\nModels exported: {len(metadata)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
