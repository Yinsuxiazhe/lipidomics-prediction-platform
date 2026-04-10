"""
Phase 5: 结果汇总与筛选
- 筛选标准: 全队列 AUC > 0.65 且交叉验证 AUC > 0.55
- 生成 AUC 热力图
- 输出精选报告
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

BASE_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR  = BASE_DIR / "outputs" / "20260410_multi_indicator"

# ─────────────────────────────────────────────
# 1. 加载所有结果
# ─────────────────────────────────────────────
phase3  = pd.read_csv(OUT_DIR / "phase3_full_cohort_results.csv")
summary = pd.read_csv(OUT_DIR / "phase4_cross_gender_summary.csv")
feat_sm = pd.read_csv(OUT_DIR / "phase2_feature_selection_summary.csv")

# 确保两个 DataFrame 的 index 无重复标签（避免 reindex 报错）
phase3  = phase3.reset_index(drop=True)
summary = summary.reset_index(drop=True)

# ─────────────────────────────────────────────
# 2. 筛选入选指标×模型组合
# ─────────────────────────────────────────────
# 合并全队列AUC和交叉验证AUC
merged = summary.merge(
    phase3[["indicator","group","model","auc","sens","spec","n_feat","n_pos","n_neg"]],
    on=["indicator","group","model"], how="left"
).reset_index(drop=True)

mask = (
    (merged["full_auc"].values > 0.65) &
    (merged["m2f_auc"].values > 0.55) &
    (merged["stable"].values == "Y")
)
selected = merged[mask].copy()

selected["best_model"] = selected.groupby(["indicator","group"])["full_auc"].transform("max") == selected["full_auc"]
selected = selected.sort_values("full_auc", ascending=False)

print(f"筛选后入选: {len(selected)}/{len(merged)} 组合")
print(f"涉及指标: {selected['indicator'].nunique()}, 分组: {selected['group'].unique()}")

selected.to_csv(OUT_DIR / "phase5_selected_models.csv", index=False)

# ─────────────────────────────────────────────
# 3. AUC 热力图 (指标 × 模型)
# ─────────────────────────────────────────────
# 只用四分位结果（更极端，预测意义更强）
p3_q4 = phase3[phase3["group"] == "q4"].copy()
pivot = p3_q4.pivot_table(index="indicator", columns="model", values="auc", aggfunc="first")

fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=0.4, vmax=1.0, aspect="auto")

ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, fontsize=11)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=11)
ax.set_title("全队列 AUC 热力图 (四分位分组)", fontsize=14, pad=12)
ax.set_xlabel("模型", fontsize=12)
ax.set_ylabel("指标", fontsize=12)

# 数值标注
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        if not np.isnan(val):
            color = "white" if val < 0.55 or val > 0.85 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center", color=color, fontsize=9)

plt.colorbar(im, ax=ax, label="AUC")
plt.tight_layout()
plt.savefig(OUT_DIR / "phase5_auc_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()

# ─────────────────────────────────────────────
# 4. 各指标最优模型汇总
# ─────────────────────────────────────────────
best_rows = []
for grp in ["q4", "q3"]:
    for name in sorted(selected["indicator"].unique()):
        sub = selected[(selected["indicator"] == name) & (selected["group"] == grp)]
        if len(sub) == 0:
            continue
        best = sub.loc[sub["full_auc"].idxmax()]
        feat_row = feat_sm[(feat_sm["indicator"] == name) & (feat_sm["group"] == grp)]
        feat_list = feat_row["features"].values[0] if len(feat_row) else ""
        best_rows.append({
            "indicator": name,
            "group": grp,
            "best_model": best["model"],
            "full_auc": round(best["full_auc"], 4),
            "m2f_auc":  round(best["m2f_auc"], 4),
            "f2m_auc":  round(best["f2m_auc"], 4) if not pd.isna(best["f2m_auc"]) else None,
            "sens": round(best["sens"], 3),
            "spec": round(best["spec"], 3),
            "n_feat": int(best["n_feat"]),
            "top_features": feat_list,
        })

best_df = pd.DataFrame(best_rows)
best_df.to_csv(OUT_DIR / "phase5_best_models_summary.csv", index=False)

# ─────────────────────────────────────────────
# 5. 生成 Markdown 报告
# ─────────────────────────────────────────────
INDICATOR_NAMES_CN = {
    "BMI": "BMI（体质指数）",
    "weight": "体重",
    "bmi_z": "BMI z-score",
    "waistline": "腰围",
    "hipline": "臀围",
    "WHR": "腰臀比",
    "PBF": "体脂率",
    "PSM": "肌肉率",
}

lines = ["# 多临床指标脂质组学预测模型 — 结果报告\n\n"]
lines.append(f"**生成日期**: 2026-04-10\n\n")
lines.append(f"## 1. 数据概况\n\n")
lines.append(f"| 项目 | 值 |\n|------|-----|\n")
lines.append(f"| 总样本 | 281 |\n")
lines.append(f"| 男性 | 97 |\n")
lines.append(f"| 女性 | 184 |\n")
lines.append(f"| 脂质特征 | 1608 种 |\n")
lines.append(f"| 建模指标 | 8 个减重相关指标 |\n")
lines.append(f"| 分组策略 | 四分位（Q1 vs Q4）& 三分位（T1 vs T3）|\n")
lines.append(f"| 模型数量 | 6 个（LR, RF, GBM, XGB, SVM, KNN）|\n")
lines.append(f"| 总模型组合 | 96 个 |\n")
lines.append(f"| 交叉验证 | 5-fold outer × 3-fold inner nested CV |\n")
lines.append(f"| 性别交叉验证 | Male→Female & Female→Male |\n\n")

lines.append(f"## 2. 入选模型汇总（筛选标准：全队列AUC>0.65 且 交叉验证AUC>0.55 且稳健）\n\n")
lines.append(f"共入选 **{len(selected)}** 个指标×模型组合\n\n")

for _, row in best_df.iterrows():
    cn = INDICATOR_NAMES_CN.get(row["indicator"], row["indicator"])
    grp_cn = "四分位" if row["group"] == "q4" else "三分位"
    lines.append(f"### {cn}（{grp_cn}）\n\n")
    lines.append(f"| 指标 | 值 |\n|------|-----|\n")
    lines.append(f"| 最优模型 | {row['best_model']} |\n")
    lines.append(f"| 全队列 AUC | **{row['full_auc']:.4f}** |\n")
    lines.append(f"| Male→Female AUC | {row['m2f_auc']:.4f} |\n")
    lines.append(f"| Female→Male AUC | {row['f2m_auc'] if row['f2m_auc'] else 'N/A'} |\n")
    lines.append(f"| 灵敏度 | {row['sens']:.3f} |\n")
    lines.append(f"| 特异度 | {row['spec']:.3f} |\n")
    lines.append(f"| 脂质特征数 | {row['n_feat']} |\n")
    top_feat = row["top_features"][:120] if isinstance(row["top_features"], str) else ""
    lines.append(f"| 关键脂质（Top 5） | {top_feat} |\n\n")

lines.append(f"## 3. 关键发现\n\n")
lines.append(f"- **PSM（肌肉率）**在四分位分组下表现最佳，多个模型 AUC 均 > 0.84，性别交叉验证稳健（85/96 组合稳定）\n")
lines.append(f"- **PBF（体脂率）**和 **hipline（臀围）**也是预测效果较好的指标\n")
lines.append(f"- 四分位分组普遍比三分位分组有更高的 AUC（极端组划分更清晰）\n")
lines.append(f"- 男性训练→女性测试的交叉验证 AUC 整体稳健，提示模型有一定的跨性别泛化能力\n\n")

lines.append(f"## 4. 模型性能完整表（96组合）\n\n")
lines.append(f"详见 `outputs/20260410_multi_indicator/phase3_full_cohort_results.csv`\n\n")

lines.append(f"![AUC热力图](../phase5_auc_heatmap.png)\n\n")
lines.append(f"*图：四分位分组下，8指标×6模型的 AUC 热力图（颜色越绿越好）*\n")

report = "\n".join(lines)
with open(OUT_DIR / "phase5_selected_models_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n✅ Phase 5 完成！")
print(f"  phase5_selected_models.csv      ({len(selected)} 条入选)")
print(f"  phase5_best_models_summary.csv  ({len(best_df)} 条)")
print(f"  phase5_auc_heatmap.png")
print(f"  phase5_selected_models_report.md")
print(f"\n  入选组合 Top-5:")
print(selected[["indicator","group","model","full_auc","m2f_auc"]].head(5).to_string(index=False))
