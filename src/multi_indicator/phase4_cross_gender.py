"""
Phase 4: 性别交叉验证
- Male 训练 → Female 测试
- Female 训练 → Male 测试
- 与全队列 nested CV 结果对比
"""
import pandas as pd
import numpy as np
import json
import copy
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, confusion_matrix
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR  = BASE_DIR / "outputs" / "20260410_multi_indicator"

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

male_ids   = set(pd.read_csv(OUT_DIR / "ids_male.csv")["ID"].tolist())
female_ids = set(pd.read_csv(OUT_DIR / "ids_female.csv")["ID"].tolist())
full_data["is_male"]   = full_data["ID"].isin(male_ids)
full_data["is_female"] = full_data["ID"].isin(female_ids)

# ─────────────────────────────────────────────
# 2. 模型定义
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
# 3. 交叉验证函数
# ─────────────────────────────────────────────
def cross_gender_eval(full_df, X_all, LIPID_COLS, all_features,
                      indicator, grp, model_template, direction):
    """
    direction: 'm2f' (Male训练→Female测试) 或 'f2m' (Female训练→Male测试)
    """
    lbl_col = f"label_{grp}_{indicator}"
    y_full = full_df[lbl_col].values
    valid = ~np.isnan(y_full)
    # 子集掩码
    if direction == "m2f":
        train_mask = valid & full_df["is_male"].values
        test_mask  = valid & full_df["is_female"].values
    else:
        train_mask = valid & full_df["is_female"].values
        test_mask  = valid & full_df["is_male"].values

    if train_mask.sum() < 10 or test_mask.sum() < 5:
        return None

    # 脂质特征
    key = f"{grp}_{indicator}"
    feat_names = all_features.get(key, [])
    feat_idx = [LIPID_COLS.index(f) for f in feat_names if f in LIPID_COLS]
    if len(feat_idx) < 2:
        feat_idx = list(range(min(20, X_all.shape[1])))
    X = X_all[:, feat_idx]

    X_tr, X_te = X[train_mask], X[test_mask]
    y_tr, y_te = y_full[train_mask], y_full[test_mask]

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
    y_prob = model.predict_proba(X_te_s)[:, 1]

    auc = roc_auc_score(y_te, y_prob)
    ap  = average_precision_score(y_te, y_prob)
    fpr_curve, tpr_curve, thresholds = roc_curve(y_te, y_prob)
    youden_idx = np.argmax(tpr_curve - fpr_curve)
    thr = thresholds[youden_idx]
    cm = confusion_matrix(y_te, (y_prob >= thr).astype(int))
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn = fp = fn = tp = 0
    sens = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0

    return {
        "direction": direction,
        "auc": auc, "ap": ap, "sens": sens, "spec": spec,
        "youden_thr": float(thr),
        "train_n": int(train_mask.sum()),
        "test_n":  int(test_mask.sum()),
        "train_pos": int((y_tr == 1).sum()),
        "test_pos":  int((y_te == 1).sum()),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }

# ─────────────────────────────────────────────
# 4. 主循环
# ─────────────────────────────────────────────
models = get_models()
results_m2f = []
results_f2m = []

for grp in GROUPS:
    for name in INDICATORS:
        for mname, mtemplate in models.items():
            for direction in ["m2f", "f2m"]:
                res = cross_gender_eval(full_data, X_all, LIPID_COLS, all_features,
                                        name, grp, mtemplate, direction)
                if res is None:
                    continue
                row = {
                    "group": grp, "indicator": name, "model": mname,
                    "direction": direction,
                    "train_n": res["train_n"], "test_n": res["test_n"],
                    "train_pos": res["train_pos"], "test_pos": res["test_pos"],
                    "auc": round(res["auc"], 4),
                    "ap":  round(res["ap"], 4),
                    "sens": round(res["sens"], 4),
                    "spec": round(res["spec"], 4),
                    "youden_thr": res["youden_thr"],
                }
                if direction == "m2f":
                    results_m2f.append(row)
                else:
                    results_f2m.append(row)

# ─────────────────────────────────────────────
# 5. 与全队列结果合并
# ─────────────────────────────────────────────
phase3 = pd.read_csv(OUT_DIR / "phase3_full_cohort_results.csv")
df_m2f = pd.DataFrame(results_m2f)
df_f2m = pd.DataFrame(results_f2m)

# 合并全队列 AUC
for df_xval, fname in [(df_m2f, "phase4_cross_gender_m2f.csv"),
                          (df_f2m, "phase4_cross_gender_f2m.csv")]:
    merged = df_xval.merge(
        phase3[["indicator","group","model","auc"]].rename(columns={"auc": "full_cohort_auc"}),
        on=["indicator","group","model"], how="left"
    )
    merged["auc_drop"] = merged["full_cohort_auc"] - merged["auc"]
    merged.to_csv(OUT_DIR / fname, index=False)

# 汇总对比表
summary_rows = []
for grp in GROUPS:
    for name in INDICATORS:
        for mname in models.keys():
            row_m2f = df_m2f[(df_m2f.group==grp) & (df_m2f.indicator==name) & (df_m2f.model==mname)]
            row_f2m = df_f2m[(df_f2m.group==grp) & (df_f2m.indicator==name) & (df_f2m.model==mname)]
            row_full = phase3[(phase3.group==grp) & (phase3.indicator==name) & (phase3.model==mname)]
            if len(row_full) == 0 or len(row_m2f) == 0:
                continue
            full_auc = row_full["auc"].values[0]
            m2f_auc  = row_m2f["auc"].values[0]
            f2m_auc  = row_f2m["auc"].values[0] if len(row_f2m) else np.nan
            summary_rows.append({
                "indicator": name, "group": grp, "model": mname,
                "full_auc": full_auc,
                "m2f_auc": m2f_auc, "f2m_auc": f2m_auc,
                "m2f_drop": round(full_auc - m2f_auc, 4),
                "f2m_drop": round(full_auc - f2m_auc, 4) if not np.isnan(f2m_auc) else np.nan,
                "stable": "Y" if (abs(full_auc - m2f_auc) < 0.1 and abs(full_auc - f2m_auc) < 0.1) else "N",
            })

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(OUT_DIR / "phase4_cross_gender_summary.csv", index=False)

print(f"\n✅ Phase 4 完成！")
print(f"  Male→Female: {len(df_m2f)} 条, phase4_cross_gender_m2f.csv")
print(f"  Female→Male: {len(df_f2m)} 条, phase4_cross_gender_f2m.csv")
print(f"  汇总对比: phase4_cross_gender_summary.csv")
print(f"\n  稳健性达标(全队列AUC vs 交叉验证AUC差距<0.1):")
stable = summary_df[summary_df["stable"] == "Y"]
print(f"  {len(stable)}/{len(summary_df)} 指标×模型组合")
print(f"\n  Top-10 交叉验证AUC (M→F):")
print(df_m2f.nlargest(10, "auc")[["indicator","group","model","auc","train_n","test_n"]].to_string(index=False))
