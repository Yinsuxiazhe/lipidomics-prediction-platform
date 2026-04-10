"""
Phase 4: Gender cross-validation.
GLM5 execution — 2026-04-10

Male train → Female test, Female train → Male test.
8 indicators × 2 cutoffs × 4 models = 64 runs each direction = 128 total.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    roc_curve, confusion_matrix, accuracy_score, f1_score,
)
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
FEAT_DIR = OUT_DIR / "phase2_selected_features"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
CUTOFFS = ["Q", "T"]
RANDOM_STATE = 42


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


def train_test_eval(X_train, y_train, X_test, y_test, model):
    """Train on one gender, test on the other. Return metrics."""
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]

    auroc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else np.nan
    auprc = average_precision_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else np.nan

    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    youden_idx = np.argmax(tpr - fpr)
    youden_thresh = thresholds[youden_idx]
    y_pred = (y_prob >= youden_thresh).astype(int)

    if (y_pred == 1).sum() > 0 and (y_pred == 0).sum() > 0:
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
        spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    else:
        sens, spec = np.nan, np.nan

    return {
        "auroc": auroc, "auprc": auprc,
        "youden_thresh": youden_thresh,
        "sensitivity": sens, "specificity": spec,
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred, zero_division=0),
    }, (fpr, tpr, auroc)


def main():
    print("=" * 60)
    print("Phase 4: Gender Cross-Validation  [GLM5]")
    print("=" * 60)

    # Load
    lipid = pd.read_csv(PROJECT / "281_merge_lipids_enroll.csv")
    lipid_features = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    lipid_ids = lipid["NAME"].values
    feature_names = lipid_features.columns.tolist()

    labels = pd.read_csv(OUT_DIR / "phase1_labels.csv")
    labels["ID"] = labels["ID"].astype(str)

    male_ids = set(pd.read_csv(OUT_DIR / "ids_male.csv")["ID"].astype(str))
    female_ids = set(pd.read_csv(OUT_DIR / "ids_female.csv")["ID"].astype(str))

    # Build lipid matrix indexed by ID
    lipid_feat = lipid_features.copy()
    lipid_feat.index = lipid_ids

    models = get_models()
    print(f"\nMale: {len(male_ids)}, Female: {len(female_ids)}")
    print(f"Runs: 8 indicators × 2 cutoffs × 4 models × 2 directions = 128\n")

    m2f_results = []
    f2m_results = []

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

            # Get valid labels
            valid = labels[labels[label_col].notna()].copy()
            y_all = valid[label_col].astype(int).values
            ids_all = valid["ID"].values

            for model_name, model_template in models.items():
                # Male → Female
                m_mask = np.isin(ids_all, list(male_ids))
                f_mask = np.isin(ids_all, list(female_ids))

                if m_mask.sum() > 10 and f_mask.sum() > 10:
                    X_train = lipid_feat.loc[ids_all[m_mask]].values[:, feat_idx]
                    y_train = y_all[m_mask]
                    X_test = lipid_feat.loc[ids_all[f_mask]].values[:, feat_idx]
                    y_test = y_all[f_mask]

                    if len(np.unique(y_train)) > 1 and len(np.unique(y_test)) > 1:
                        try:
                            model = clone(model_template)
                            metrics, (fpr, tpr, auc) = train_test_eval(X_train, y_train, X_test, y_test, model)
                            m2f_results.append({
                                "indicator": indicator, "cutoff": cutoff, "model": model_name,
                                "direction": "M→F", "n_train": len(y_train), "n_test": len(y_test),
                                **metrics,
                            })
                            flag = f"AUROC={metrics['auroc']:.3f}"
                        except Exception as e:
                            flag = f"ERR: {e}"
                    else:
                        flag = "SKIP(1-class)"
                else:
                    flag = "SKIP(n<10)"

                # Female → Male
                if f_mask.sum() > 10 and m_mask.sum() > 10:
                    X_train = lipid_feat.loc[ids_all[f_mask]].values[:, feat_idx]
                    y_train = y_all[f_mask]
                    X_test = lipid_feat.loc[ids_all[m_mask]].values[:, feat_idx]
                    y_test = y_all[m_mask]

                    if len(np.unique(y_train)) > 1 and len(np.unique(y_test)) > 1:
                        try:
                            model = clone(model_template)
                            metrics, _ = train_test_eval(X_train, y_train, X_test, y_test, model)
                            f2m_results.append({
                                "indicator": indicator, "cutoff": cutoff, "model": model_name,
                                "direction": "F→M", "n_train": len(y_train), "n_test": len(y_test),
                                **metrics,
                            })
                            flag += f" / F→M AUROC={metrics['auroc']:.3f}"
                        except Exception as e:
                            flag += f" / F→M ERR"

                print(f"[{label_col:15s} {model_name:8s}] {flag}")

    # Save
    m2f_df = pd.DataFrame(m2f_results)
    f2m_df = pd.DataFrame(f2m_results)
    cross_df = pd.concat([m2f_df, f2m_df], ignore_index=True)

    m2f_df.to_csv(OUT_DIR / "phase4_cross_gender_m2f.csv", index=False)
    f2m_df.to_csv(OUT_DIR / "phase4_cross_gender_f2m.csv", index=False)
    cross_df.to_csv(OUT_DIR / "phase4_cross_gender_all.csv", index=False)

    # Summary: compare full cohort vs cross-gender
    full = pd.read_csv(OUT_DIR / "phase3_full_cohort_results.csv")

    print("\n" + "=" * 60)
    print("Phase 4 Summary  [GLM5]")
    print("=" * 60)
    print(f"Male→Female: {len(m2f_results)} runs")
    print(f"Female→Male: {len(f2m_results)} runs\n")

    # Best per indicator: full cohort vs cross-gender average
    print(f"{'Indicator':12s} {'Cut':3s} {'Model':8s} | {'Full_AUC':8s} {'M→F_AUC':8s} {'F→M_AUC':8s}")
    print("-" * 60)
    for indicator in INDICATORS:
        for cutoff in CUTOFFS:
            full_sub = full[(full["indicator"] == indicator) & (full["cutoff"] == cutoff)]
            if len(full_sub) == 0:
                continue
            best = full_sub.loc[full_sub["mean_auroc"].idxmax()]
            model_name = best["model"]

            m2f = cross_df[(cross_df["indicator"] == indicator) &
                          (cross_df["cutoff"] == cutoff) &
                          (cross_df["model"] == model_name) &
                          (cross_df["direction"] == "M→F")]
            f2m = cross_df[(cross_df["indicator"] == indicator) &
                          (cross_df["cutoff"] == cutoff) &
                          (cross_df["model"] == model_name) &
                          (cross_df["direction"] == "F→M")]

            m2f_auc = m2f["auroc"].values[0] if len(m2f) > 0 else np.nan
            f2m_auc = f2m["auroc"].values[0] if len(f2m) > 0 else np.nan
            print(f"{indicator:12s} {cutoff:3s} {model_name:8s} | {best['mean_auroc']:.3f}    {m2f_auc:.3f}    {f2m_auc:.3f}")

    print("=" * 60)


if __name__ == "__main__":
    main()
