"""
训练并保存多指标预测模型（14个入选组合）。
输出: website/models/*.pkl, website/data/model_info.json
"""
import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
LIPID_FILE = PROJECT / "281_merge_lipids_enroll.csv"
ENROLL_FILE = PROJECT / "287_enroll_data_clean.csv"
OUTROLL_FILE = PROJECT / "287_outroll_data_clean.csv"
PHASE2_FEAT = PROJECT / "outputs/20260410_multi_indicator/phase2_selected_features"
PHASE5_SUMMARY = PROJECT / "outputs/20260410_multi_indicator/phase5_best_models_summary.csv"
WEBSITE_DIR = PROJECT / "website"
WEBSITE_DATA = WEBSITE_DIR / "data"
WEBSITE_MODELS = WEBSITE_DIR / "models"

WEBSITE_DATA.mkdir(parents=True, exist_ok=True)
WEBSITE_MODELS.mkdir(parents=True, exist_ok=True)

# ── 8个临床指标配置 ──────────────────────────────────────────────
INDICATORS = {
    "BMI":       ("BMI",    "BMI"),
    "weight":    ("weight", "weight"),
    "bmi_z":     ("bmi_z_enroll", "bmi_z_out"),
    "waistline": ("waistline", "waistline"),
    "hipline":   ("hipline", "hipline"),
    "WHR":       ("WHR",    "WHR"),
    "PBF":       ("Inbody_39_PBF_.Percent_Body_Fat.", "Inbody_39_PBF_.Percent_Body_Fat."),
    "PSM":       ("Inbody_PSM_.Percent_Skeletal_Muscle_Mass.", "Inbody_PSM_.Percent_Skeletal_Muscle_Mass."),
}

INDICATOR_CN = {
    "BMI": "BMI（体质指数）", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}

# ── 方向定义：值越大 → 运动效果越好 = 标签1（高响应）──────
# BMI/weight/PBF/WHR/waistline/hipline: 减少 = 好 → delta小 → Q1=1
# PSM: 增加 = 好 → delta大 → Q4=1
RESPONSE_DIRECTION = {
    "BMI": "negative", "weight": "negative", "bmi_z": "negative",
    "waistline": "negative", "hipline": "negative", "WHR": "negative",
    "PBF": "negative", "PSM": "positive",
}

# ── 模型工厂 ──────────────────────────────────────────────────────
def make_model(name):
    if name == "LR":
        return LogisticRegression(max_iter=5000, random_state=42, C=0.1)
    if name == "RF":
        return RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    if name == "GBM":
        return GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
    if name == "SVM":
        return SVC(kernel="rbf", C=1.0, probability=True, random_state=42)
    if name == "KNN":
        return KNeighborsClassifier(n_neighbors=5)
    raise ValueError(f"Unknown model: {name}")


def make_pipeline(model_name, use_scaling=True):
    """Wrap model in pipeline with optional scaler."""
    inner = []
    if use_scaling and model_name in ["LR", "SVM", "KNN"]:
        inner.append(("scaler", StandardScaler()))
    inner.append(("clf", make_model(model_name)))
    return Pipeline(inner)


# ── 加载脂质数据 ───────────────────────────────────────────────────
print("Loading lipid data ...")
lipid_df = pd.read_csv(LIPID_FILE)
lipid_ids = lipid_df["NAME"].astype(str).tolist()
lipid_features = lipid_df.drop(columns=["NAME"])
feature_names = lipid_features.columns.tolist()

# ── 加载临床数据 ──────────────────────────────────────────────────
enroll  = pd.read_csv(ENROLL_FILE)
outroll = pd.read_csv(OUTROLL_FILE)

# 计算 delta
delta_rows = []
for label, (col_e, col_o) in INDICATORS.items():
    delta = pd.to_numeric(outroll[col_o], errors="coerce") - pd.to_numeric(enroll[col_e], errors="coerce")
    delta_rows.append(delta.rename(label))
delta_df = pd.concat(delta_rows, axis=1)
delta_df.insert(0, "ID", enroll["ID"].values)

# ── 合并 ──────────────────────────────────────────────────────────
delta_df["ID"] = delta_df["ID"].astype(str)
lipid_df["NAME"] = lipid_df["NAME"].astype(str)
merged = lipid_df.merge(delta_df, left_on="NAME", right_on="ID", how="inner")
print(f"Merged: {len(merged)} subjects with both lipid and clinical data")

# ── 加载入选模型清单 ──────────────────────────────────────────────
best_models = pd.read_csv(PHASE5_SUMMARY)
print(f"\n入选模型: {len(best_models)} 个组合\n")


# ── 训练每个模型 ──────────────────────────────────────────────────
model_info = {}
skipped = []

for _, row in best_models.iterrows():
    indicator = row["indicator"]
    group = row["group"]      # "q4" or "q3"
    model_name = row["best_model"]

    # 标签列名
    label_col = f"{indicator}_Q" if group == "q4" else f"{indicator}_T"
    direction = RESPONSE_DIRECTION[indicator]

    # 生成二分类标签
    # Q: Q1(bottom 25%)=0, Q4(top 25%)=1
    # 对于 negative 指标: 值越小越好 → Q1 = 高响应(1)
    # 对于 positive 指标: 值越大越好 → Q4 = 高响应(1)
    vals = merged[indicator]
    q25 = vals.quantile(0.25)
    q75 = vals.quantile(0.75)
    t33 = vals.quantile(0.333)
    t67 = vals.quantile(0.667)

    y = pd.Series(np.nan, index=merged.index)
    if group == "q4":
        # Q1=0, Q4=1
        y[vals <= q25] = 0
        y[vals >  q75] = 1
    else:
        # T1=0, T3=1
        y[vals <= t33] = 0
        y[vals >  t67] = 1

    # 应用方向映射
    # negative 指标: Q1=1（减少最多=运动效果最好）
    # positive 指标: Q4=1（增加最多=运动效果最好）
    if direction == "negative":
        y = 1 - y

    valid = y.notna()
    if valid.sum() < 30:
        skipped.append(f"{indicator}/{group}/{model_name} (n={valid.sum()})")
        continue

    y = y[valid].astype(int).values

    # 加载特征列表
    feat_file = PHASE2_FEAT / f"q4_{indicator}.csv" if group == "q4" else PHASE2_FEAT / f"q3_{indicator}.csv"
    if not feat_file.exists():
        skipped.append(f"{indicator}/{group}/{model_name} (feature file not found: {feat_file.name})")
        continue

    feat_df = pd.read_csv(feat_file)
    # 列名可能是 'lipid_name' 或 'feature'
    feat_col = "lipid_name" if "lipid_name" in feat_df.columns else "feature"
    selected_feats = feat_df[feat_col].tolist()[:int(row["n_feat"])]
    # 只保留实际存在于数据中的特征
    selected_feats = [f for f in selected_feats if f in feature_names]
    if len(selected_feats) < 2:
        selected_feats = feature_names[:5]

    X = merged.loc[valid, selected_feats].values

    # 训练
    model = make_pipeline(model_name)
    model.fit(X, y)

    # 保存
    key = f"{indicator}_{group}_{model_name}"
    out_path = WEBSITE_MODELS / f"{key}.pkl"
    with open(out_path, "wb") as f:
        pickle.dump({
            "model": model,
            "features": selected_feats,
            "indicator": indicator,
            "group": group,
            "model_name": model_name,
            "full_auc": float(row["full_auc"]),
            "m2f_auc": float(row["m2f_auc"]),
            "f2m_auc": float(row["f2m_auc"]) if not pd.isna(row["f2m_auc"]) else None,
            "sens": float(row["sens"]),
            "spec": float(row["spec"]),
        }, f)

    model_info[key] = {
        "path": str(out_path.relative_to(WEBSITE_DIR)),
        "indicator": indicator,
        "indicator_cn": INDICATOR_CN[indicator],
        "group": group,
        "group_cn": "四分位" if group == "q4" else "三分位",
        "model_name": model_name,
        "full_auc": float(row["full_auc"]),
        "m2f_auc": float(row["m2f_auc"]),
        "f2m_auc": float(row["f2m_auc"]) if not pd.isna(row["f2m_auc"]) else None,
        "sens": float(row["sens"]),
        "spec": float(row["spec"]),
        "n_feat": len(selected_feats),
        "features": selected_feats,
        "direction": direction,
        "description": f"预测 {INDICATOR_CN[indicator]} 在四分位分组下{'减少最多' if direction == 'negative' else '增加最多'}（高响应）与{'减少最少' if direction == 'negative' else '增加最少'}（低响应）的分类",
    }
    print(f"  [{key}] trained ({len(selected_feats)} features, n={len(y)}, AUC={row['full_auc']:.4f})")

# ── 保存模型元信息 ─────────────────────────────────────────────────
with open(WEBSITE_DATA / "model_info.json", "w", encoding="utf-8") as f:
    json.dump(model_info, f, ensure_ascii=False, indent=2)

print(f"\n✅ 模型训练完成")
print(f"   成功: {len(model_info)} 个")
if skipped:
    print(f"   跳过: {skipped}")
print(f"   输出: {WEBSITE_MODELS}/")
print(f"   元信息: {WEBSITE_DATA}/model_info.json")
