"""
Phase 3: 全队列多模型建模
- 8指标 × 2分组（Q4/Q3） × 6模型 = 96个模型
- nested CV (5-fold outer × 3-fold inner)
- 输出 AUROC, AUPRC, Sensitivity, Specificity, Youden阈值, SHAP
"""
import pandas as pd
import numpy as np
import json
import pickle
import copy
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             roc_curve, confusion_matrix)
import xgboost as xgb
import shap
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR  = BASE_DIR / "outputs" / "20260410_multi_indicator"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. 加载数据
# ─────────────────────────────────────────────
meta = json.loads(open(OUT_DIR / "phase1_indicator_meta.json").read())
full_data = pd.read_csv(OUT_DIR / "phase1_full_data.csv")
with open(OUT_DIR / "phase2_selected_features/all_selected_features.json") as f:
    all_features = json.load(f)

LIPID_COLS = open(OUT_DIR / "phase1_lipid_features.txt").read().splitlines()
INDICATORS = [m["name"] for m in meta["indicators"]]
GROUPS = ["q4", "q3"]

X_all = full_data[LIPID_COLS].values
X_all = np.nan_to_num(X_all, nan=np.nanmedian(X_all))

# ─────────────────────────────────────────────
# 2. 定义6个模型
# ─────────────────────────────────────────────
def get_models():
    return {
        "LR":  LogisticRegression(C=0.5, max_iter=1000, random_state=42, solver="lbfgs"),
        "RF":  RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42, n_jobs=-1),
        "GBM": GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
        "XGB": xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                                  use_label_encoder=False, eval_metric="logloss",
                                  random_state=42, verbosity=0, n_jobs=-1),
        "SVM": SVC(C=1.0, kernel="rbf", probability=True, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=7, weights="distance", n_jobs=-1),
    }

# ─────────────────────────────────────────────
# 3. nested CV 核心函数
# ─────────────────────────────────────────────
def nested_cv(X, y, model_template, outer_k=5, inner_k=3, seed=42):
    outer_cv = StratifiedKFold(n_splits=outer_k, shuffle=True, random_state=seed)
    y_pred_prob = np.full(len(y), np.nan)

    for train_idx, test_idx in outer_cv.split(X, y):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        needs_scaling = model_template.__class__.__name__ in \
            ["LogisticRegression", "SVC", "KNeighborsClassifier"]
        if needs_scaling:
            scaler = StandardScaler()
            X_tr_s = scaler.fit_transform(X_tr)
            X_te_s = scaler.transform(X_te)
        else:
            X_tr_s, X_te_s = X_tr, X_te

        model = copy.deepcopy(model_template)
        model.fit(X_tr_s, y_tr)
        y_pred_prob[test_idx] = model.predict_proba(X_te_s)[:, 1]

    valid = ~np.isnan(y_pred_prob) & ~np.isnan(y)
    if valid.sum() < 10:
        return None
    y_v, p_v = y[valid], y_pred_prob[valid]
    auc  = roc_auc_score(y_v, p_v)
    ap   = average_precision_score(y_v, p_v)
    fpr_curve, tpr_curve, thresholds = roc_curve(y_v, p_v)
    youden_idx = np.argmax(tpr_curve - fpr_curve)
    youden_thr = thresholds[youden_idx]
    cm = confusion_matrix(y_v, (p_v >= youden_thr).astype(int))
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn = fp = fn = tp = 0
    sens = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0
    return {
        "auc": auc, "ap": ap, "sens": sens, "spec": spec,
        "youden_thr": float(youden_thr),
        "y_true": y_v, "y_prob": p_v,
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
    }

def fit_final(X, y, model_template):
    needs_scaling = model_template.__class__.__name__ in \
        ["LogisticRegression", "SVC", "KNeighborsClassifier"]
    if needs_scaling:
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        model = copy.deepcopy(model_template)
        model.fit(Xs, y)
        return model, scaler
    else:
        model = copy.deepcopy(model_template)
        model.fit(X, y)
        return model, None

def compute_shap(model, X, model_name, scaler=None):
    try:
        if scaler is not None:
            Xs = scaler.transform(X)
        else:
            Xs = X
        if model_name == "LR":
            explainer = shap.LinearExplainer(model, Xs)
        elif model_name in ["KNN", "SVM"]:
            return None
        else:
            explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(Xs)
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        return sv
    except Exception:
        return None

# ─────────────────────────────────────────────
# 4. 主循环
# ─────────────────────────────────────────────
models = get_models()
results = []
PLOT_DIR = OUT_DIR / "phase3_roc_plots";   PLOT_DIR.mkdir(exist_ok=True)
SHAP_DIR = OUT_DIR / "phase3_shap_plots";  SHAP_DIR.mkdir(exist_ok=True)
MODEL_DIR = OUT_DIR / "phase3_models";     MODEL_DIR.mkdir(exist_ok=True)

for grp in GROUPS:
    for name in INDICATORS:
        key = f"{grp}_{name}"
        lbl_col = f"label_{grp}_{name}"
        y = full_data[lbl_col].values
        valid_mask = ~np.isnan(y)
        X = X_all[valid_mask]
        y_v = y[valid_mask]
        n_pos = int(np.sum(y_v == 1))
        n_neg = int(np.sum(y_v == 0))

        feat_names = all_features.get(key, [])
        feat_idx = [LIPID_COLS.index(f) for f in feat_names if f in LIPID_COLS]
        if len(feat_idx) < 2:
            feat_idx = list(range(min(20, X_all.shape[1])))
            feat_names = [LIPID_COLS[i] for i in feat_idx]
        X_feat = X[:, feat_idx]

        print(f"\n[{key}] n={len(y_v)} (pos={n_pos}, neg={n_neg}), feat={len(feat_idx)}")

        for mname, mtemplate in models.items():
            res = nested_cv(X_feat, y_v, mtemplate)
            if res is None:
                continue
            print(f"  {mname}: AUC={res['auc']:.3f}, AP={res['ap']:.3f}, "
                  f"Sens={res['sens']:.2f}, Spec={res['spec']:.2f}")

            results.append({
                "group": grp, "indicator": name, "model": mname,
                "n_pos": n_pos, "n_neg": n_neg, "n_feat": len(feat_idx),
                "auc": round(res["auc"], 4), "ap": round(res["ap"], 4),
                "sens": round(res["sens"], 4), "spec": round(res["spec"], 4),
                "youden_thr": res["youden_thr"],
                "tn": res["tn"], "fp": res["fp"], "fn": res["fn"], "tp": res["tp"],
            })

            # 保存模型
            fm, scaler = fit_final(X_feat, y_v, mtemplate)
            with open(MODEL_DIR / f"{key}_{mname}.pkl", "wb") as f:
                pickle.dump({"model": fm, "scaler": scaler,
                             "feat_idx": feat_idx, "feat_names": feat_names,
                             "thr": res["youden_thr"]}, f)

            # SHAP
            sv = compute_shap(fm, X_feat, mname, scaler)
            if sv is not None:
                np.save(SHAP_DIR / f"{key}_{mname}_shap.npy", sv)

            # ROC 图
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                fpr_curve, tpr_curve, _ = roc_curve(res["y_true"], res["y_prob"])
                plt.figure(figsize=(5, 4))
                plt.plot(fpr_curve, tpr_curve, "b-", lw=2, label=f"AUC={res['auc']:.3f}")
                plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
                plt.xlabel("FPR"); plt.ylabel("TPR")
                plt.title(f"{key} — {mname}")
                plt.legend(loc="lower right")
                plt.tight_layout()
                plt.savefig(PLOT_DIR / f"{key}_{mname}_roc.png", dpi=150)
                plt.close()
            except Exception as e:
                print(f"    ROC图失败: {e}")

# ─────────────────────────────────────────────
# 5. 保存
# ─────────────────────────────────────────────
results_df = pd.DataFrame(results)
results_df.to_csv(OUT_DIR / "phase3_full_cohort_results.csv", index=False)

print(f"\n✅ Phase 3 完成！")
print(f"  结果: phase3_full_cohort_results.csv ({len(results_df)} 条)")
print(f"  模型: phase3_models/*.pkl")
print(f"  ROC图: phase3_roc_plots/*.png ({len(list(PLOT_DIR.glob('*.png')))} 张)")
print(f"\n  Top-10 AUC:")
print(results_df.nlargest(10, "auc")[["indicator","group","model","auc","sens","spec"]].to_string(index=False))
