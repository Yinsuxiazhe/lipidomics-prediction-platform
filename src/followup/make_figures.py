from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

MODEL_LABEL_MAP = {
    "clinical_baseline_main": "Clinical baseline",
    "ultra_sparse_lipid": "Ultra-sparse lipid",
    "compact_fusion": "Compact fusion",
}

SCHEME_LABEL_MAP = {
    "strict": "Strict nested CV",
    "repeated_random_holdout": "Repeated hold-out",
    "leave_one_prefix_out": "Prefix hold-out\n(exploratory weak proxy)",
    "leave_one_school_out": "School hold-out",
    "outphase_repeated_random_holdout": "Out-phase hold-out\n(internal temporal)",
    "outphase_leave_one_prefix_out": "Out-phase prefix hold-out\n(exploratory temporal proxy)",
    "outphase_leave_one_school_out": "Out-phase school hold-out\n(internal temporal grouped)",
}

SCHEME_COLOR_MAP = {
    "strict": "#4C78A8",
    "repeated_random_holdout": "#F58518",
    "leave_one_prefix_out": "#54A24B",
    "leave_one_school_out": "#2E8B57",
    "outphase_repeated_random_holdout": "#B279A2",
    "outphase_leave_one_prefix_out": "#72B7B2",
    "outphase_leave_one_school_out": "#4C9F70",
}

SCHEME_DISTRIBUTION_TICK_LABEL_MAP = {
    "repeated_random_holdout": "Repeated hold-out",
    "leave_one_prefix_out": "Prefix proxy",
    "leave_one_school_out": "School hold-out",
    "outphase_repeated_random_holdout": "Out-phase hold-out",
    "outphase_leave_one_prefix_out": "Out-phase prefix proxy",
    "outphase_leave_one_school_out": "Out-phase school hold-out",
}


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.bbox": "tight",
            "savefig.dpi": 300,
        }
    )


def _save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> dict[str, str]:
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(png_path)
    fig.savefig(pdf_path)
    plt.close(fig)
    return {"png": str(png_path), "pdf": str(pdf_path)}


def _format_model_label(model_label: str) -> str:
    return MODEL_LABEL_MAP.get(model_label, model_label.replace("_", " ").title())


def _format_distribution_tick_label(model_label: str, scheme: str) -> str:
    scheme_label = SCHEME_DISTRIBUTION_TICK_LABEL_MAP.get(scheme, SCHEME_LABEL_MAP.get(scheme, scheme))
    return f"{_format_model_label(model_label)}\n{scheme_label}"


def _first_available_scheme(available_keys: set[str], candidates: list[str]) -> str | None:
    for scheme in candidates:
        if scheme in available_keys:
            return scheme
    return None


def _resolve_followup_grouped_scheme_from_columns(frame: pd.DataFrame) -> str | None:
    column_to_scheme = {
        "leave_one_school_out_mean_auc": "leave_one_school_out",
        "leave_one_prefix_out_mean_auc": "leave_one_prefix_out",
    }
    available_keys = {scheme for column, scheme in column_to_scheme.items() if column in frame.columns}
    return _first_available_scheme(available_keys, ["leave_one_school_out", "leave_one_prefix_out"])


def _resolve_grouped_scheme_from_validation_summary(frame: pd.DataFrame, *, outphase: bool = False) -> str | None:
    available = set(frame.get("validation_scheme", pd.Series(dtype=object)).astype(str))
    candidates = (
        ["outphase_leave_one_school_out", "outphase_leave_one_prefix_out"]
        if outphase
        else ["leave_one_school_out", "leave_one_prefix_out"]
    )
    return _first_available_scheme(available, candidates)


def _draw_grouped_bars(
    ax: plt.Axes,
    frame: pd.DataFrame,
    value_columns: list[tuple[str, str]],
    ylabel: str,
    title: str,
) -> None:
    x = np.arange(len(frame))
    width = 0.24
    plotted_any = False
    for idx, (scheme_key, column) in enumerate(value_columns):
        if column not in frame.columns:
            continue
        offset = (idx - (len(value_columns) - 1) / 2) * width
        values = frame[column].astype(float).to_numpy()
        bars = ax.bar(
            x + offset,
            values,
            width=width,
            label=SCHEME_LABEL_MAP.get(scheme_key, scheme_key),
            color=SCHEME_COLOR_MAP.get(scheme_key, "#999999"),
            alpha=0.9,
        )
        plotted_any = True
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=90,
            )

    ax.set_xticks(x)
    ax.set_xticklabels([_format_model_label(x) for x in frame["model_label"]])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if plotted_any:
        ax.legend(frameon=False)
    else:
        ax.text(0.5, 0.5, "No plotted summary columns available", ha="center", va="center")
    ax.grid(axis="y", alpha=0.25, linestyle="--")


def _safe_frame_max(frame: pd.DataFrame, columns: list[str], default: float) -> float:
    available = [column for column in columns if column in frame.columns]
    if not available:
        return default
    values = pd.to_numeric(frame[available].stack(), errors="coerce").dropna()
    if values.empty:
        return default
    return float(values.max())


def _plot_model_performance(small_model_comparison: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    _apply_style()
    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    grouped_scheme = _resolve_followup_grouped_scheme_from_columns(small_model_comparison)
    value_columns = [
        ("strict", "strict_mean_auc"),
        ("repeated_random_holdout", "repeated_random_holdout_mean_auc"),
    ]
    if grouped_scheme:
        value_columns.append((grouped_scheme, f"{grouped_scheme}_mean_auc"))
    _draw_grouped_bars(
        ax=ax,
        frame=small_model_comparison,
        value_columns=value_columns,
        ylabel="Mean AUC",
        title="Figure F1. Follow-up small models across validation schemes",
    )
    max_columns = ["strict_mean_auc", "repeated_random_holdout_mean_auc"]
    if grouped_scheme:
        max_columns.append(f"{grouped_scheme}_mean_auc")
    auc_max = _safe_frame_max(small_model_comparison, max_columns, default=0.7)
    ax.set_ylim(0.0, max(0.8, auc_max + 0.08))
    return _save_figure(fig, output_dir, "FigureF1_Followup_ModelPerformance")


def _plot_generalization_gap(small_model_comparison: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    _apply_style()
    frame = small_model_comparison.copy()
    frame["strict_mean_gap"] = frame["strict_mean_train_auc"].astype(float) - frame["strict_mean_auc"].astype(float)
    grouped_scheme = _resolve_followup_grouped_scheme_from_columns(frame)

    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    value_columns = [
        ("strict", "strict_mean_gap"),
        ("repeated_random_holdout", "repeated_random_holdout_mean_gap"),
    ]
    if grouped_scheme:
        value_columns.append((grouped_scheme, f"{grouped_scheme}_mean_gap"))
    _draw_grouped_bars(
        ax=ax,
        frame=frame,
        value_columns=value_columns,
        ylabel="Train-test gap",
        title="Figure F2. Generalization gap of follow-up small models",
    )
    ax.axhline(0.1, color="#999999", linestyle=":", linewidth=1)
    max_columns = ["strict_mean_gap", "repeated_random_holdout_mean_gap"]
    if grouped_scheme:
        max_columns.append(f"{grouped_scheme}_mean_gap")
    gap_max = _safe_frame_max(frame, max_columns, default=0.25)
    ax.set_ylim(0.0, max(0.35, gap_max + 0.05))
    return _save_figure(fig, output_dir, "FigureF2_Followup_GeneralizationGap")


def _plot_self_validation_distribution(fold_metrics: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    _apply_style()
    frame = fold_metrics.loc[fold_metrics["status"] == "completed"].copy()
    frame["gap"] = frame["train_auc"].astype(float) - frame["auc"].astype(float)
    model_order = [
        label for label in ["clinical_baseline_main", "ultra_sparse_lipid", "compact_fusion"] if label in set(frame["model_label"])
    ]
    grouped_scheme = _resolve_grouped_scheme_from_validation_summary(frame, outphase=False)
    scheme_order = ["repeated_random_holdout"]
    if grouped_scheme:
        scheme_order.append(grouped_scheme)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.6), constrained_layout=True)
    for panel_index, metric in enumerate(["auc", "gap"]):
        ax = axes[panel_index]
        positions = []
        labels = []
        data = []
        colors = []
        pos = 1
        for model_label in model_order:
            for scheme in scheme_order:
                subset = frame.loc[
                    (frame["model_label"] == model_label) & (frame["validation_scheme"] == scheme),
                    metric,
                ].dropna()
                if subset.empty:
                    continue
                positions.append(pos)
                labels.append(_format_distribution_tick_label(model_label, scheme))
                data.append(subset.to_numpy())
                colors.append(SCHEME_COLOR_MAP.get(scheme, "#999999"))
                pos += 1
            pos += 0.4

        if data:
            box = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True, showfliers=False)
            for patch, color in zip(box["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.75)
            for median in box["medians"]:
                median.set_color("#222222")
                median.set_linewidth(1.3)
            ax.set_xticks(positions)
            ax.set_xticklabels(labels, rotation=15, ha="right")
            ax.tick_params(axis="x", labelsize=7.5, pad=6)
            ax.grid(axis="y", alpha=0.25, linestyle="--")
        else:
            ax.text(0.5, 0.5, "No completed splits available", ha="center", va="center")
            ax.set_axis_off()
        ax.set_title("Split-level AUC" if metric == "auc" else "Split-level train-test gap")
        ax.set_ylabel("AUC" if metric == "auc" else "Gap")

    fig.suptitle("Figure F3. Self-validation split distributions")
    return _save_figure(fig, output_dir, "FigureF3_SelfValidation_Distribution")


def _plot_outphase_model_performance(outphase_summary: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    _apply_style()
    pivot = (
        outphase_summary.pivot_table(
            index=["experiment", "model_label"],
            columns="validation_scheme",
            values="mean_auc",
            aggfunc="first",
        )
        .reset_index()
    )
    pivot.columns.name = None
    grouped_scheme = _resolve_grouped_scheme_from_validation_summary(outphase_summary, outphase=True)

    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    value_columns = [("outphase_repeated_random_holdout", "outphase_repeated_random_holdout")]
    if grouped_scheme:
        value_columns.append((grouped_scheme, grouped_scheme))
    _draw_grouped_bars(
        ax=ax,
        frame=pivot,
        value_columns=value_columns,
        ylabel="Mean AUC",
        title="Figure F5. Internal temporal out-phase validation",
    )
    max_columns = ["outphase_repeated_random_holdout"]
    if grouped_scheme:
        max_columns.append(grouped_scheme)
    auc_max = _safe_frame_max(pivot, max_columns, default=0.7)
    ax.set_ylim(0.0, max(0.8, auc_max + 0.08))
    return _save_figure(fig, output_dir, "FigureF5_OutPhase_ModelPerformance")


def _plot_outphase_distribution(outphase_folds: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    _apply_style()
    frame = outphase_folds.loc[outphase_folds["status"] == "completed"].copy()
    frame["gap"] = frame["train_auc"].astype(float) - frame["auc"].astype(float)
    model_order = [
        label for label in ["clinical_baseline_main", "ultra_sparse_lipid", "compact_fusion"] if label in set(frame["model_label"])
    ]
    grouped_scheme = _resolve_grouped_scheme_from_validation_summary(frame, outphase=True)
    scheme_order = ["outphase_repeated_random_holdout"]
    if grouped_scheme:
        scheme_order.append(grouped_scheme)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.6), constrained_layout=True)
    for panel_index, metric in enumerate(["auc", "gap"]):
        ax = axes[panel_index]
        positions = []
        labels = []
        data = []
        colors = []
        pos = 1
        for model_label in model_order:
            for scheme in scheme_order:
                subset = frame.loc[
                    (frame["model_label"] == model_label) & (frame["validation_scheme"] == scheme),
                    metric,
                ].dropna()
                if subset.empty:
                    continue
                positions.append(pos)
                labels.append(_format_distribution_tick_label(model_label, scheme))
                data.append(subset.to_numpy())
                colors.append(SCHEME_COLOR_MAP.get(scheme, "#999999"))
                pos += 1
            pos += 0.4

        if data:
            box = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True, showfliers=False)
            for patch, color in zip(box["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.75)
            for median in box["medians"]:
                median.set_color("#222222")
                median.set_linewidth(1.3)
            ax.set_xticks(positions)
            ax.set_xticklabels(labels, rotation=15, ha="right")
            ax.tick_params(axis="x", labelsize=7.5, pad=6)
            ax.grid(axis="y", alpha=0.25, linestyle="--")
        else:
            ax.text(0.5, 0.5, "No completed out-phase splits", ha="center", va="center")
            ax.set_axis_off()
        ax.set_title("Out-phase split AUC" if metric == "auc" else "Out-phase train-test gap")
        ax.set_ylabel("AUC" if metric == "auc" else "Gap")

    fig.suptitle("Figure F6. Out-phase split distributions")
    return _save_figure(fig, output_dir, "FigureF6_OutPhase_Distribution")


def _parse_prefix_distribution(group_definition_audit: pd.DataFrame) -> pd.DataFrame:
    frame = group_definition_audit.loc[group_definition_audit["record_type"] == "id_prefix_distribution"].copy()
    if frame.empty:
        return pd.DataFrame(columns=["prefix", "response_n", "noresponse_n", "n"])

    frame["prefix"] = frame["key"].astype(str)

    def _extract_count(note: str, pattern: str) -> int:
        match = re.search(pattern, str(note))
        return int(match.group(1)) if match else 0

    frame["response_n"] = frame["note"].map(lambda x: _extract_count(x, r"response_n=(\d+)"))
    frame["noresponse_n"] = frame["note"].map(lambda x: _extract_count(x, r"noresponse_n=(\d+)"))
    frame["n"] = pd.to_numeric(frame["value"], errors="coerce").fillna(frame["response_n"] + frame["noresponse_n"])
    return frame[["prefix", "response_n", "noresponse_n", "n"]].sort_values("prefix").reset_index(drop=True)


def _plot_group_audit(
    baseline_balance_summary: pd.DataFrame,
    group_definition_audit: pd.DataFrame,
    output_dir: Path,
) -> dict[str, str]:
    _apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)

    balance = baseline_balance_summary.copy().sort_values("standardized_mean_difference")
    ax = axes[0]
    y = np.arange(len(balance))
    x = balance["standardized_mean_difference"].astype(float).to_numpy()
    ax.hlines(y=y, xmin=0, xmax=x, color="#4C78A8", linewidth=2)
    ax.plot(x, y, "o", color="#4C78A8")
    ax.axvline(0, color="#333333", linewidth=1)
    ax.axvline(0.1, color="#999999", linestyle=":", linewidth=1)
    ax.axvline(-0.1, color="#999999", linestyle=":", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(balance["variable"])
    ax.set_xlabel("Standardized mean difference")
    ax.set_title("Baseline balance audit")
    ax.grid(axis="x", alpha=0.25, linestyle="--")

    prefix = _parse_prefix_distribution(group_definition_audit)
    ax = axes[1]
    if not prefix.empty:
        x = np.arange(len(prefix))
        ax.bar(x, prefix["response_n"], color="#54A24B", label="response")
        ax.bar(x, prefix["noresponse_n"], bottom=prefix["response_n"], color="#E45756", label="noresponse")
        ax.set_xticks(x)
        ax.set_xticklabels(prefix["prefix"])
        ax.set_ylabel("Sample count")
        ax.set_title("ID prefix distribution (weak cohort/prefix proxy)")
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=0.25, linestyle="--")
    else:
        ax.text(0.5, 0.5, "No prefix distribution available", ha="center", va="center")
        ax.set_axis_off()

    fig.suptitle("Figure F4. Group audit: balance and prefix structure")
    return _save_figure(fig, output_dir, "FigureF4_GroupAudit")


def run_followup_figures(
    *,
    self_validation_summary_path: str | Path,
    self_validation_fold_metrics_path: str | Path,
    small_model_comparison_path: str | Path,
    baseline_balance_summary_path: str | Path,
    group_definition_audit_csv_path: str | Path,
    output_dir: str | Path,
    outphase_validation_summary_path: str | Path | None = None,
    outphase_validation_fold_metrics_path: str | Path | None = None,
) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    self_validation_summary = pd.read_csv(self_validation_summary_path)
    fold_metrics = pd.read_csv(self_validation_fold_metrics_path)
    small_model_comparison = pd.read_csv(small_model_comparison_path)
    baseline_balance_summary = pd.read_csv(baseline_balance_summary_path)
    group_definition_audit = pd.read_csv(group_definition_audit_csv_path)

    performance_paths = _plot_model_performance(small_model_comparison, output_path)
    gap_paths = _plot_generalization_gap(small_model_comparison, output_path)
    distribution_paths = _plot_self_validation_distribution(fold_metrics, output_path)
    audit_paths = _plot_group_audit(baseline_balance_summary, group_definition_audit, output_path)
    outphase_paths: dict[str, str] = {}
    if outphase_validation_summary_path and outphase_validation_fold_metrics_path:
        outphase_summary = pd.read_csv(outphase_validation_summary_path)
        outphase_folds = pd.read_csv(outphase_validation_fold_metrics_path)
        outphase_model_paths = _plot_outphase_model_performance(outphase_summary, output_path)
        outphase_distribution_paths = _plot_outphase_distribution(outphase_folds, output_path)
        outphase_paths = {
            "followup_figure_outphase_model_performance_png": outphase_model_paths["png"],
            "followup_figure_outphase_model_performance_pdf": outphase_model_paths["pdf"],
            "followup_figure_outphase_distribution_png": outphase_distribution_paths["png"],
            "followup_figure_outphase_distribution_pdf": outphase_distribution_paths["pdf"],
        }

    # Keep parameter read for interface symmetry and future expansion.
    _ = self_validation_summary

    return {
        "followup_figure_model_performance_png": performance_paths["png"],
        "followup_figure_model_performance_pdf": performance_paths["pdf"],
        "followup_figure_generalization_gap_png": gap_paths["png"],
        "followup_figure_generalization_gap_pdf": gap_paths["pdf"],
        "followup_figure_self_validation_distribution_png": distribution_paths["png"],
        "followup_figure_self_validation_distribution_pdf": distribution_paths["pdf"],
        "followup_figure_group_audit_png": audit_paths["png"],
        "followup_figure_group_audit_pdf": audit_paths["pdf"],
        **outphase_paths,
    }


def write_followup_alignment_note(
    *,
    discussion_note_path: str | Path,
    output_dir: str | Path,
    outphase_completed: bool = False,
) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    discussion_text = Path(discussion_note_path).read_text(encoding="utf-8", errors="ignore")
    _ = discussion_text

    path = output_path / "followup_plan_alignment.md"
    lines = [
        "# follow-up 分析结果与 2026-03-11 对接思路的对应关系",
        "",
        "> 本页不是新增结果，而是把 `docs/20260311_对接_新的分析思路.txt` 中的关键想法，映射到当前第一阶段 follow-up 已完成内容、部分完成内容和当前阻塞项。",
        "",
        "| 对接思路 | 当前状态 | 目前如何落地 |",
        "| --- | --- | --- |",
        "| 分组定义/差异先审清楚 | 部分完成 | 已完成当前 responder 标签证据链审计、基线平衡汇总、ID prefix 分布整理；但因为缺少原始连续终点文件，尚未完成真正的重定义或 alternative grouping sensitivity。 |",
        "| 小模型、稀疏模型、稳定特征 | 已完成 | 已完成 `clinical_baseline_main`、`ultra_sparse_lipid`、`compact_fusion` 的 strict vs repeated hold-out vs prefix-holdout 比较，并补出 follow-up 图组。 |",
        "| pseudo-external validation | 已完成 | 已实现并运行 leave-one-prefix-out，但明确只可写成 exploratory weak proxy，不可写成外部验证。 |",
        (
            "| out 的数据做验证 | 已完成 | 已接入 out / 干预后数据，完成基线训练 → out-phase 测试的内部时相验证；报告中明确写为 internal temporal validation，而不是外部验证。 |"
            if outphase_completed
            else "| out 的数据做验证 | 当前阻塞 | 思路已吸收进 follow-up 设计，但本地没有出组/干预后同批数据表，因此本轮只保留为 blocker。 |"
        ),
        "| 心血管相关表型 | 当前阻塞 | 已在 follow-up 汇总中保留机制桥接位置，但本地没有新增整理好的心血管表型表。 |",
        "",
        "## 三层汇报口径如何对应这份思路",
        "",
        "1. **正式主结果**：对应“当前先不要轻易推翻主分组，也不要只追求更高分”的思路，仍保持 strict nested CV 为主口径。",
        "2. **补充稳健性证据**：对应“可以先做随机抽样自我验证、pseudo-external、小模型/稀疏模型路线”的思路，这部分本轮已经落地。",
        (
            "3. **内部时相验证**：对应“out 数据做验证”的思路，本轮已经接入并完成，但仍严格不把它写成外部验证。"
            if outphase_completed
            else "3. **待数据到位后再执行**：对应“out 数据验证”“心血管表型机制桥接”“真正的 alternative grouping sensitivity”，这部分目前仍明确标为 blocker。"
        ),
        "",
        "## 给老师/合作者最顺的一句话",
        "",
        (
            "> 这轮 follow-up 不是为了把分数再做高，而是把 2026-03-11 对接中提出的关键方法学思路拆成三层：strict 主结果、补充稳健性证据、以及 out-phase 内部时相验证，同时继续明确哪些内容仍因数据缺失而暂缓。"
            if outphase_completed
            else "> 这轮 follow-up 不是为了把分数再做高，而是把 2026-03-11 对接中提出的几条关键方法学思路拆成三层：已经完成的、已经补证的、以及明确因数据缺失而暂缓的。"
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)
