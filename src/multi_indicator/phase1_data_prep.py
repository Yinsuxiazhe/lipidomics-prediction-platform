"""
Phase 1: 数据准备
- 加载入组/出组数据，计算 delta
- 生成四分位/三分位分组标签
- 统计性别人数，生成子集
- 输出基线描述性统计
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR  = BASE_DIR / "outputs" / "20260410_multi_indicator"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. 加载原始数据
# ─────────────────────────────────────────────
enroll  = pd.read_csv(BASE_DIR / "287_enroll_data_clean.csv")
outroll = pd.read_csv(BASE_DIR / "287_outroll_data_clean.csv")
lipids  = pd.read_csv(BASE_DIR / "281_merge_lipids_enroll.csv")

# ─────────────────────────────────────────────
# 2. 定义8个减重指标及合并后的列名
# ─────────────────────────────────────────────
# merged 后统一命名为: {name}_e (入组) 和 {name}_o (出组)
INDICATORS = [
    ("BMI",       "BMI",                               "BMI"),
    ("weight",    "weight",                            "weight"),
    ("bmi_z",     "bmi_z_enroll",                    "bmi_z_out"),
    ("waistline", "waistline",                        "waistline"),
    ("hipline",   "hipline",                          "hipline"),
    ("WHR",       "WHR",                              "WHR"),
    ("PBF",       "Inbody_39_PBF_.Percent_Body_Fat.", "Inbody_39_PBF_.Percent_Body_Fat."),
    ("PSM",       "Inbody_PSM_.Percent_Skeletal_Muscle_Mass.", "Inbody_PSM_.Percent_Skeletal_Muscle_Mass."),
]

# ─────────────────────────────────────────────
# 3. 分别提取所需列，预先重命名为 {name}_e / {name}_o
# ─────────────────────────────────────────────
def build_indicator_df(df, indicators, suffix, include_gender=True):
    """从原始 df 中提取指标列，重命名为 {name}_{suffix}，自动转数值"""
    rows = {"ID": df["ID"].values}
    if include_gender and "Gender" in df.columns:
        rows["Gender"] = df["Gender"].values
    for name, enroll_col, out_col in indicators:
        orig_col = enroll_col if suffix == "e" else out_col
        vals = pd.to_numeric(df[orig_col], errors="coerce")
        rows[f"{name}_{suffix}"] = vals.values
    return pd.DataFrame(rows)

e_df = build_indicator_df(enroll,  INDICATORS, "e", include_gender=True)
o_df = build_indicator_df(outroll, INDICATORS, "o", include_gender=False)

merged = pd.merge(e_df, o_df, on="ID", how="inner")
print(f"合并后: {len(merged)} 行, {len(merged.columns)} 列")
for c in sorted(merged.columns):
    if any(x in c for x in ["bmi","BMI","weight","waist","hip","WHR","PBF","PSM"]):
        print(f"  {c}")

# ─────────────────────────────────────────────
# 4. 计算 delta = out - enroll
# ─────────────────────────────────────────────
delta_rows = {"ID": merged["ID"].values, "Gender": merged["Gender"].values}
for name, _, _ in INDICATORS:
    col_e = f"{name}_e"
    col_o = f"{name}_o"
    dv = merged[col_o] - merged[col_e]
    delta_rows[f"delta_{name}"]   = dv
    delta_rows[f"enroll_{name}"]  = merged[col_e]
    delta_rows[f"outroll_{name}"] = merged[col_o]
    print(f"  {name}: Δmean={dv.mean():.4f}±{dv.std():.4f}, n={dv.notna().sum()}")

delta_df = pd.DataFrame(delta_rows)

# ─────────────────────────────────────────────
# 5. 与脂质组 merge
# ─────────────────────────────────────────────
lipids_renamed = lipids.rename(columns={"NAME": "ID"})
full_df = pd.merge(delta_df, lipids_renamed, on="ID", how="inner")
print(f"\n脂质组匹配后样本数: {len(full_df)}")

LIPID_COLS = [c for c in full_df.columns
              if c not in delta_df.columns and c != "ID"]
print(f"脂质特征数量: {len(LIPID_COLS)}")

# ─────────────────────────────────────────────
# 6. 四分位/三分位分组标签
# 约定: 1=高响应(Δ最小/下降最多), 0=低响应(Δ最大/下降最少或上升)
# ─────────────────────────────────────────────
label_rows = {}
for name, _, _ in INDICATORS:
    dv_all = full_df[f"delta_{name}"]

    q1 = dv_all.quantile(0.25)
    q3 = dv_all.quantile(0.75)
    t1 = dv_all.quantile(1/3)
    t3 = dv_all.quantile(2/3)

    # 四分位: Q1 vs Q4（排除中间50%）
    lq4 = np.where(
        (dv_all <= q1) | (dv_all >= q3),
        np.where(dv_all <= q1, 1, 0),
        np.nan
    )
    # 三分位: T1 vs T3（排除中间33%）
    lq3 = np.where(
        (dv_all <= t1) | (dv_all >= t3),
        np.where(dv_all <= t1, 1, 0),
        np.nan
    )
    label_rows[f"label_q4_{name}"] = lq4
    label_rows[f"label_q3_{name}"] = lq3

    n_q4_h = int(np.nansum(lq4 == 1))
    n_q4_l = int(np.nansum(lq4 == 0))
    n_q3_h = int(np.nansum(lq3 == 1))
    n_q3_l = int(np.nansum(lq3 == 0))
    print(f"  {name}: Q1={q1:.4f} Q3={q3:.4f} → 四分位 高={n_q4_h} 低={n_q4_l} | "
          f"T1={t1:.4f} T3={t3:.4f} → 三分位 高={n_q3_h} 低={n_q3_l}")

labels_df = pd.DataFrame(label_rows)
full_labeled = pd.concat([full_df.reset_index(drop=True),
                           labels_df.reset_index(drop=True)], axis=1)

# ─────────────────────────────────────────────
# 7. 性别人数统计
# ─────────────────────────────────────────────
gc = full_labeled["Gender"].value_counts()
male_n   = int(gc.get(1, 0))
female_n = int(gc.get(0, 0))
print(f"\n性别分布: Male={male_n}, Female={female_n}")

male_ids   = full_labeled[full_labeled["Gender"] == 1]["ID"].tolist()
female_ids = full_labeled[full_labeled["Gender"] == 0]["ID"].tolist()
pd.DataFrame({"ID": male_ids}).to_csv(OUT_DIR / "ids_male.csv",   index=False)
pd.DataFrame({"ID": female_ids}).to_csv(OUT_DIR / "ids_female.csv", index=False)

# ─────────────────────────────────────────────
# 8. 基线描述性统计
# ─────────────────────────────────────────────
stats_rows = []
for name, _, _ in INDICATORS:
    col = f"enroll_{name}"
    for gval, glabel in [(1, "Male"), (0, "Female")]:
        sub = full_labeled[full_labeled["Gender"] == gval][col].dropna()
        stats_rows.append({"indicator": name, "gender": glabel, "n": len(sub),
                           "mean": round(sub.mean(), 4), "std": round(sub.std(), 4),
                           "median": round(sub.median(), 4)})
    sub_all = full_labeled[col].dropna()
    stats_rows.append({"indicator": name, "gender": "All", "n": len(sub_all),
                       "mean": round(sub_all.mean(), 4), "std": round(sub_all.std(), 4),
                       "median": round(sub_all.median(), 4)})
pd.DataFrame(stats_rows).to_csv(OUT_DIR / "phase1_baseline_stats.csv", index=False)

# ─────────────────────────────────────────────
# 9. 输出文件
# ─────────────────────────────────────────────
full_labeled.to_csv(OUT_DIR / "phase1_full_data.csv", index=False)

lipid_matrix = full_labeled[["ID", "Gender"] + LIPID_COLS].copy()
lipid_matrix.to_csv(OUT_DIR / "phase1_lipid_matrix.csv", index=False)

delta_out = full_labeled[["ID", "Gender"] + [f"delta_{n}" for n, _, _ in INDICATORS]].copy()
delta_out.to_csv(OUT_DIR / "phase1_delta_only.csv", index=False)

with open(OUT_DIR / "phase1_lipid_features.txt", "w") as f:
    f.write("\n".join(LIPID_COLS))

with open(OUT_DIR / "phase1_indicator_meta.json", "w") as f:
    json.dump({
        "indicators": [
            {"name": n, "enroll_col": f"enroll_{n}", "outroll_col": f"outroll_{n}",
             "delta_col": f"delta_{n}", "label_q4": f"label_q4_{n}", "label_q3": f"label_q3_{n}"}
            for n, _, _ in INDICATORS
        ],
        "total_samples": int(len(full_labeled)),
        "male_n": male_n, "female_n": female_n,
        "lipid_feature_count": len(LIPID_COLS)
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 1 完成！")
print(f"  输出目录: {OUT_DIR}")
print(f"  phase1_full_data.csv        {full_labeled.shape}")
print(f"  phase1_lipid_matrix.csv     {lipid_matrix.shape}")
print(f"  phase1_delta_only.csv       {delta_out.shape}")
print(f"  phase1_baseline_stats.csv   8指标×3性别")
print(f"  ids_male.csv ({male_n}), ids_female.csv ({female_n})")
print(f"  phase1_lipid_features.txt   {len(LIPID_COLS)}个脂质")
print(f"  phase1_indicator_meta.json")
