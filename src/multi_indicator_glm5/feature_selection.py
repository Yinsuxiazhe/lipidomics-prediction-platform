"""
Phase 2: Feature selection for multi-indicator lipidomics prediction.
GLM5 execution — 2026-04-10

For each indicator × cutoff combination:
  Step 1: Mann-Whitney U filter (p < 0.05)
  Step 2: Elastic Net ranking (non-zero coefficients)
  Step 3: XGBoost ranking (top-k feature importance)
  Step 4: Intersection of Step 2 and Step 3 → final feature set
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
FEAT_DIR = OUT_DIR / "phase2_selected_features"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
CUTOFFS = ["Q", "T"]

# Feature selection params
MWU_P_THRESHOLD = 0.05
XGB_TOP_K = 30
EN_C = 0.1
EN_L1_RATIO = 0.5
EN_MAX_ITER = 5000


def load_phase1():
    """Load Phase 1 outputs."""
    lipid = pd.read_csv(PROJECT / "281_merge_lipids_enroll.csv")
    delta = pd.read_csv(OUT_DIR / "phase1_delta_matrix.csv")
    labels = pd.read_csv(OUT_DIR / "phase1_delta_with_lipid_ids.csv")

    # Build lipid feature matrix (281 × 1608, NAME as index)
    lipid_features = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    lipid_ids = lipid["NAME"].values
    feature_names = lipid_features.columns.tolist()

    # Align: only keep subjects in both lipid and delta
    delta["ID"] = delta["ID"].astype(str)
    mask = delta["ID"].isin(lipid_ids)
    delta_sub = delta.loc[mask].reset_index(drop=True)

    lipid_feat_aligned = lipid_features.copy()
    lipid_feat_aligned.index = lipid_ids
    lipid_feat_aligned = lipid_feat_aligned.loc[delta_sub["ID"].values]

    # Load labels
    all_labels = pd.read_csv(OUT_DIR / "phase1_labels.csv")
    all_labels["ID"] = all_labels["ID"].astype(str)
    labels_sub = all_labels[all_labels["ID"].isin(delta_sub["ID"].values)].reset_index(drop=True)

    return lipid_feat_aligned, labels_sub, feature_names, delta_sub


def step_mwu_filter(X, y, feature_names, p_thresh=MWU_P_THRESHOLD):
    """Step 1: Mann-Whitney U test, return features with p < threshold."""
    group0 = X[y == 0]
    group1 = X[y == 1]
    if len(group0) < 3 or len(group1) < 3:
        return feature_names  # not enough data, return all

    pvals = []
    for i in range(X.shape[1]):
        try:
            _, p = mannwhitneyu(group0.iloc[:, i], group1.iloc[:, i], alternative="two-sided")
        except Exception:
            p = 1.0
        pvals.append(p)

    selected = [f for f, p in zip(feature_names, pvals) if p < p_thresh]
    return selected if len(selected) >= 5 else feature_names[:50]  # fallback: top 50


def step_elastic_net(X, y, feature_names):
    """Step 2: Elastic Net logistic regression, return features with non-zero coefficients."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(
        penalty="elasticnet",
        solver="saga",
        C=EN_C,
        l1_ratio=EN_L1_RATIO,
        max_iter=EN_MAX_ITER,
        random_state=42,
    )
    model.fit(X_scaled, y)

    coefs = np.abs(model.coef_[0])
    nonzero_idx = np.where(coefs > 0)[0]
    ranked = sorted(zip(feature_names, coefs), key=lambda x: -x[1])
    return [(f, c) for f, c in ranked if c > 0]


def step_xgboost(X, y, feature_names, top_k=XGB_TOP_K):
    """Step 3: XGBoost feature importance, return top-k."""
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        use_label_encoder=False,
        eval_metric="logloss",
    )
    model.fit(X, y)

    importances = model.feature_importances_
    ranked = sorted(zip(feature_names, importances), key=lambda x: -x[1])
    return ranked[:top_k]


def run_feature_selection():
    FEAT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 2: Feature Selection  [GLM5]")
    print("=" * 60)

    X_all, labels_df, feature_names, delta_sub = load_phase1()
    print(f"\nLoaded: {X_all.shape[0]} subjects × {X_all.shape[1]} lipid features")
    print(f"Feature selection: {len(INDICATORS)} indicators × {len(CUTOFFS)} cutoffs = {len(INDICATORS)*len(CUTOFFS)} groups\n")

    # Reset X_all index to 0-based for alignment with labels_df
    X_all = X_all.reset_index(drop=True)

    summary_rows = []

    for indicator in INDICATORS:
        for cutoff in CUTOFFS:
            label_col = f"{indicator}_{cutoff}"
            print(f"[{label_col:15s}] ", end="", flush=True)

            # Get non-NaN labels
            valid_mask = labels_df[label_col].notna()
            if valid_mask.sum() < 20:
                print(f"SKIP (only {valid_mask.sum()} valid labels)")
                continue

            y = labels_df.loc[valid_mask, label_col].astype(int).values
            X = X_all.loc[valid_mask].values
            cols = feature_names.copy()

            # Step 1: MWU filter
            mwu_feats = step_mwu_filter(
                pd.DataFrame(X, columns=cols), pd.Series(y), cols
            )
            print(f"MWU={len(mwu_feats):4d} → ", end="", flush=True)

            # Subset to MWU features for EN and XGB
            mwu_idx = [cols.index(f) for f in mwu_feats if f in cols]
            X_mwu = X[:, mwu_idx]
            mwu_names = [cols[i] for i in mwu_idx]

            # Step 2: Elastic Net
            en_ranked = step_elastic_net(X_mwu, y, mwu_names)
            en_feats = set(f for f, _ in en_ranked)
            print(f"EN={len(en_feats):3d} → ", end="", flush=True)

            # Step 3: XGBoost
            xgb_ranked = step_xgboost(X_mwu, y, mwu_names)
            xgb_feats = set(f for f, _ in xgb_ranked)
            print(f"XGB={len(xgb_feats):3d} → ", end="", flush=True)

            # Step 4: Intersection
            final_feats = en_feats & xgb_feats
            # If intersection is too small, take union of top-10 from each
            if len(final_feats) < 3:
                en_top = set(f for f, _ in en_ranked[:10])
                xgb_top = set(f for f, _ in xgb_ranked[:10])
                final_feats = en_top | xgb_top

            # Build final ranking by XGBoost importance
            xgb_dict = dict(xgb_ranked)
            final_ranked = sorted(
                [(f, xgb_dict.get(f, 0)) for f in final_feats],
                key=lambda x: -x[1],
            )

            print(f"FINAL={len(final_feats):3d}")

            # Save per-group features
            feat_df = pd.DataFrame(final_ranked, columns=["feature", "importance"])
            feat_df.to_csv(FEAT_DIR / f"features_{label_col}.csv", index=False)

            summary_rows.append({
                "indicator": indicator,
                "cutoff": cutoff,
                "label_col": label_col,
                "n_class0": int((y == 0).sum()),
                "n_class1": int((y == 1).sum()),
                "n_mwu_pass": len(mwu_feats),
                "n_en_nonzero": len(en_feats),
                "n_xgb_top": len(xgb_feats),
                "n_final_features": len(final_feats),
                "top5_features": ", ".join(f for f, _ in final_ranked[:5]),
            })

    # Save summary
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "phase2_feature_selection_summary.csv", index=False)

    print("\n" + "=" * 60)
    print("Phase 2 Summary  [GLM5]")
    print("=" * 60)
    print(summary[["indicator", "cutoff", "n_class0", "n_class1", "n_final_features", "top5_features"]].to_string(index=False))
    print(f"\nOutput: {FEAT_DIR}/")
    print(f"Summary: {OUT_DIR / 'phase2_feature_selection_summary.csv'}")
    print("=" * 60)


if __name__ == "__main__":
    run_feature_selection()
