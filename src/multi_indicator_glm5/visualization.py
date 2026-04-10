"""
Phase 5: Result summary, screening, and visualization.
GLM5 execution — 2026-04-10
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
plt.rcParams["font.sans-serif"] = ["PingFang HK", "Heiti TC", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
FIG_DIR = OUT_DIR / "phase5_figures"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
INDICATOR_CN = {
    "BMI": "BMI", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}


def merge_results():
    full = pd.read_csv(OUT_DIR / "phase3_full_cohort_results.csv")
    cross = pd.read_csv(OUT_DIR / "phase4_cross_gender_all.csv")

    # Pivot cross: one row per (indicator, cutoff, model), with M→F and F→M AUCs
    m2f = cross[cross["direction"] == "M→F"][["indicator", "cutoff", "model", "auroc", "auprc", "sensitivity", "specificity"]].rename(
        columns={"auroc": "m2f_auroc", "auprc": "m2f_auprc", "sensitivity": "m2f_sens", "specificity": "m2f_spec"})
    f2m = cross[cross["direction"] == "F→M"][["indicator", "cutoff", "model", "auroc", "auprc", "sensitivity", "specificity"]].rename(
        columns={"auroc": "f2m_auroc", "auprc": "f2m_auprc", "sensitivity": "f2m_sens", "specificity": "f2m_spec"})

    merge = full[["indicator", "cutoff", "model", "mean_auroc", "std_auroc", "mean_auprc",
                   "mean_sensitivity", "mean_specificity", "n_features", "n_class0", "n_class1"]].copy()
    merge = merge.merge(m2f, on=["indicator", "cutoff", "model"], how="left")
    merge = merge.merge(f2m, on=["indicator", "cutoff", "model"], how="left")
    merge["cross_avg_auroc"] = merge[["m2f_auroc", "f2m_auroc"]].mean(axis=1)

    # Best model per indicator×cutoff
    best_idx = merge.groupby(["indicator", "cutoff"])["mean_auroc"].idxmax()
    merge["is_best"] = merge.index.isin(best_idx)

    merge.to_csv(OUT_DIR / "phase5_master_results.csv", index=False)
    return merge


def plot_auc_heatmap(master):
    """Heatmap: indicator × model for each cutoff."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    models = ["EN_LR", "XGBoost", "RF", "LR_L2"]
    model_labels = ["EN LR", "XGBoost", "RF", "LR L2"]

    for cutoff, cname in [("Q", "四分位 (Q)"), ("T", "三分位 (T)")]:
        sub = master[master["cutoff"] == cutoff]
        pivot = sub.pivot(index="indicator", columns="model", values="mean_auroc")
        pivot = pivot.reindex(index=INDICATORS, columns=models)

        # Also add cross-gender avg
        pivot_cross = sub.pivot(index="indicator", columns="model", values="cross_avg_auroc")
        pivot_cross = pivot_cross.reindex(index=INDICATORS, columns=models)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        for ax, data, title in [
            (axes[0], pivot, f"Full Cohort Nested CV AUROC\n{cname}"),
            (axes[1], pivot_cross, f"Cross-Gender Average AUROC\n{cname}"),
        ]:
            im = ax.imshow(data.values, cmap="RdYlGn", vmin=0.5, vmax=1.0, aspect="auto")
            ax.set_xticks(range(len(models)))
            ax.set_xticklabels(model_labels, fontsize=10)
            ylabels = [f"{INDICATOR_CN.get(i, i)}\n({i})" for i in INDICATORS]
            ax.set_yticks(range(len(INDICATORS)))
            ax.set_yticklabels(ylabels, fontsize=9)
            ax.set_title(title, fontsize=11, fontweight="bold")

            for i in range(len(INDICATORS)):
                for j in range(len(models)):
                    v = data.values[i, j]
                    if not np.isnan(v):
                        ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                                fontsize=9, fontweight="bold" if v > 0.8 else "normal",
                                color="white" if v > 0.85 else "black")

            fig.colorbar(im, ax=ax, shrink=0.8)

        plt.tight_layout()
        plt.savefig(FIG_DIR / f"heatmap_{cutoff}.png", dpi=150, bbox_inches="tight")
        plt.savefig(FIG_DIR / f"heatmap_{cutoff}.pdf", bbox_inches="tight")
        plt.close()
        print(f"  saved: heatmap_{cutoff}.png")


def plot_best_comparison(master):
    """Bar chart: best AUROC per indicator, full vs cross-gender."""
    best = master[master["is_best"]].copy()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, cutoff, cname in [(axes[0], "Q", "四分位"), (axes[1], "T", "三分位")]:
        sub = best[best["cutoff"] == cutoff].set_index("indicator").reindex(INDICATORS)

        x = np.arange(len(INDICATORS))
        w = 0.25

        bars1 = ax.bar(x - w, sub["mean_auroc"], w, label="Full Cohort", color="#4C78A8", edgecolor="white")
        bars2 = ax.bar(x, sub["m2f_auroc"], w, label="Male→Female", color="#F58518", edgecolor="white")
        bars3 = ax.bar(x + w, sub["f2m_auroc"], w, label="Female→Male", color="#E45756", edgecolor="white")

        ax.set_xticks(x)
        ax.set_xticklabels([INDICATOR_CN.get(i, i) for i in INDICATORS], fontsize=9)
        ax.set_ylabel("AUROC", fontsize=11)
        ax.set_title(f"最佳模型 AUROC 对比 — {cname}", fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.set_ylim(0.4, 1.0)
        ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
        ax.axhline(0.7, color="gray", linestyle=":", alpha=0.3)

        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                h = bar.get_height()
                if not np.isnan(h):
                    ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.2f}",
                            ha="center", va="bottom", fontsize=7)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "best_model_comparison.png", dpi=150, bbox_inches="tight")
    plt.savefig(FIG_DIR / "best_model_comparison.pdf", bbox_inches="tight")
    plt.close()
    print("  saved: best_model_comparison.png")


def generate_report(master):
    """Generate markdown summary report."""
    lines = [
        "# Phase 5: 结果汇总与筛选报告  [GLM5]",
        "",
        "## 总览",
        "",
        f"- 全队列 nested CV 模型数: {len(master)}",
        f"- 最佳筛选线: AUROC > 0.70 (全队列) 且 cross_avg > 0.65",
        "",
    ]

    # Screening
    good = master[(master["mean_auroc"] > 0.70) & (master["cross_avg_auroc"] > 0.65)]
    lines.append(f"## 入选模型: {len(good)} 个\n")
    lines.append("| 指标 | 截止 | 模型 | 全队列 AUC | M→F AUC | F→M AUC | 交叉均值 |")
    lines.append("|------|------|------|-----------|---------|---------|---------|")
    for _, r in good.sort_values("mean_auroc", ascending=False).iterrows():
        lines.append(f"| {INDICATOR_CN.get(r['indicator'], r['indicator'])} | {r['cutoff']} | {r['model']} "
                     f"| {r['mean_auroc']:.3f} | {r['m2f_auroc']:.3f} | {r['f2m_auroc']:.3f} "
                     f"| {r['cross_avg_auroc']:.3f} |")

    report = "\n".join(lines)
    (OUT_DIR / "phase5_selected_models_report.md").write_text(report, encoding="utf-8")
    print(f"  saved: phase5_selected_models_report.md")

    return good


def main():
    print("=" * 60)
    print("Phase 5: Result Summary & Visualization  [GLM5]")
    print("=" * 60)

    print("\n[1/4] Merging results ...")
    master = merge_results()
    print(f"  {len(master)} rows in master table")

    print("\n[2/4] Generating heatmaps ...")
    plot_auc_heatmap(master)

    print("\n[3/4] Generating best-model comparison ...")
    plot_best_comparison(master)

    print("\n[4/4] Generating screening report ...")
    good = generate_report(master)
    print(f"  {len(good)} models passed screening (AUROC>0.70, cross_avg>0.65)")

    print("\n" + "=" * 60)
    print("Phase 5 complete. [GLM5]")
    print(f"Figures: {FIG_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
