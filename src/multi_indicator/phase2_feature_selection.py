"""
Phase 2: 脂质特征筛选
对每个指标 × 每种分组策略：
  1. Mann-Whitney U 检验 → p < 0.05 的脂质
  2. Elastic Net 交叉验证 → 系数非零的脂质
  3. XGBoost feature importance → top-30 脂质
  4. 取交集作为最终特征集
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.stats import mannwhitneyu
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR  = BASE_DIR / "outputs" / "20260410_multi_indicator"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FEAT_DIR = OUT_DIR / "phase2_selected_features"
FEAT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# 1. 加载数据
# ─────────────────────────────────────────────
meta = json.loads(open(OUT_DIR / "phase1_indicator_meta.json").read())
full_data = pd.read_csv(OUT_DIR / "phase1_full_data.csv")
LIPID_COLS = open(OUT_DIR / "phase1_lipid_features.txt").read().splitlines()
INDICATORS = [(m["name"]) for m in meta["indicators"]]
GROUPS = ["q4", "q3"]  # 四分位、三分位
LABEL_MAP = {g: {m["name"]: m[f"label_{g}"]
                  for m in meta["indicators"]}
             for g in GROUPS}

X_all = full_data[LIPID_COLS].values
# 缺失值填充：中位数
X_all = np.nan_to_num(X_all, nan=np.nanmedian(X_all))
print(f"脂质特征矩阵: {X_all.shape}, 指标: {INDICATORS}, 分组: {GROUPS}")

# ─────────────────────────────────────────────
# 2. 辅助函数
# ─────────────────────────────────────────────
def get_label(group_key, indicator):
    lbl = LABEL_MAP[group_key][indicator]
    return full_data[lbl].values

def get_valid_mask(y):
    return ~np.isnan(y)

def mwu_filter(X, y, alpha=0.05):
    """Mann-Whitney U 检验，返回 p < alpha 的脂质索引"""
    y_valid = y[get_valid_mask(y)]
    X_valid = X[get_valid_mask(y)]
    pos_mask = y_valid == 1
    neg_mask = y_valid == 0
    if pos_mask.sum() < 5 or neg_mask.sum() < 5:
        return set()
    sig_idx = set()
    for j in range(X.shape[1]):
        vals_pos = X_valid[pos_mask, j]
        vals_neg = X_valid[neg_mask, j]
        if np.std(vals_pos) == 0 or np.std(vals_neg) == 0:
            continue
        try:
            _, p = mannwhitneyu(vals_pos, vals_neg, alternative="two-sided")
            if p < alpha:
                sig_idx.add(j)
        except Exception:
            pass
    return sig_idx

def en_filter(X, y, max_features=200):
    """ElasticNetCV 提取非零系数脂质"""
    mask = get_valid_mask(y)
    Xv, yv = X[mask], y[mask]
    scaler = StandardScaler()
    Xs = scaler.fit_transform(Xv)
    en = ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9], cv=3, max_iter=5000, n_jobs=-1)
    try:
        en.fit(Xs, yv)
        nonzero = np.where(np.abs(en.coef_) > 1e-6)[0]
        return set(nonzero[:max_features])
    except Exception as e:
        print(f"    EN failed: {e}")
        return set()

def xgb_filter(X, y, top_k=30):
    """XGBoost feature importance，取 top-k"""
    mask = get_valid_mask(y)
    Xv, yv = X[mask], y[mask]
    clf = xgb.XGBClassifier(n_estimators=100, max_depth=3, use_label_encoder=False,
                             eval_metric="logloss", verbosity=0, n_jobs=-1)
    clf.fit(Xv, yv)
    imp = clf.feature_importances_
    top_idx = np.argsort(imp)[::-1][:top_k]
    return set(top_idx)

# ─────────────────────────────────────────────
# 3. 逐指标 × 分组运行特征筛选
# ─────────────────────────────────────────────
summary_rows = []
all_selected = {}

for grp in GROUPS:
    for name in INDICATORS:
        key = f"{grp}_{name}"
        y = get_label(grp, name)
        valid_mask = get_valid_mask(y)
        n_pos = int(np.sum(y[valid_mask] == 1))
        n_neg = int(np.sum(y[valid_mask] == 0))
        print(f"\n  [{key}] 有效样本: {valid_mask.sum()} (高={n_pos}, 低={n_neg})")

        # 3.1 MWU
        mwu_idx = mwu_filter(X_all, y)
        print(f"    MWU (p<0.05): {len(mwu_idx)} 个")

        # 3.2 ElasticNet
        en_idx = en_filter(X_all, y)
        print(f"    ElasticNet: {len(en_idx)} 个")

        # 3.3 XGBoost top-30
        xgb_idx = xgb_filter(X_all, y)
        print(f"    XGBoost top-30: {len(xgb_idx)} 个")

        # 3.4 交集
        if mwu_idx and en_idx and xgb_idx:
            final_idx = mwu_idx & en_idx & xgb_idx
        elif mwu_idx and en_idx:
            final_idx = mwu_idx & en_idx
        elif mwu_idx and xgb_idx:
            final_idx = mwu_idx & xgb_idx
        else:
            # 回退：取 MWU + XGB 并集再取前30
            union = mwu_idx | en_idx | xgb_idx
            imp_sum = np.zeros(X_all.shape[1])
            mask = get_valid_mask(y)
            clf = xgb.XGBClassifier(n_estimators=100, max_depth=3, use_label_encoder=False,
                                     verbosity=0, n_jobs=-1)
            clf.fit(X_all[mask], y[mask])
            for idx in union:
                imp_sum[idx] = clf.feature_importances_[idx]
            final_idx = set(np.argsort(imp_sum)[::-1][:30])
        
        final_names = [LIPID_COLS[i] for i in final_idx]
        print(f"    交集/并集后: {len(final_idx)} 个特征")
        all_selected[key] = final_names

        # 保存特征列表
        feat_df = pd.DataFrame({
            "rank": range(1, len(final_names) + 1),
            "lipid_name": final_names
        })
        feat_df.to_csv(FEAT_DIR / f"{key}.csv", index=False)

        summary_rows.append({
            "group": grp,
            "indicator": name,
            "n_pos": n_pos,
            "n_neg": n_neg,
            "n_mwu": len(mwu_idx),
            "n_en": len(en_idx),
            "n_xgb": len(xgb_idx),
            "n_final": len(final_idx),
            "features": "; ".join(final_names[:5]) + (" ..." if len(final_names) > 5 else "")
        })

# ─────────────────────────────────────────────
# 4. 保存汇总表
# ─────────────────────────────────────────────
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(OUT_DIR / "phase2_feature_selection_summary.csv", index=False)

# 保存完整特征名映射
with open(FEAT_DIR / "all_selected_features.json", "w") as f:
    json.dump({k: list(v) for k, v in all_selected.items()}, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 2 完成！")
print(f"  特征筛选汇总: phase2_feature_selection_summary.csv")
print(f"  各指标特征文件: phase2_selected_features/*.csv")
