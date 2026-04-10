from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.data.build_cohort import AnalysisCohorts
from src.followup.group_audit import run_group_audit
from src.followup.make_figures import run_followup_figures, write_followup_alignment_note
from src.followup.outphase_validation import run_outphase_validation
from src.followup.self_validation import run_self_validation
from src.io.load_data import RawProjectTables


def _format_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "（空）"
    printable = frame.copy()
    for column in printable.columns:
        printable[column] = printable[column].map(
            lambda value: f"{value:.4f}" if isinstance(value, float) and pd.notna(value) else value
        )
    headers = [str(column) for column in printable.columns]
    rows = printable.astype(object).where(pd.notna(printable), "").values.tolist()
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _write_blocked_items(blockers: list[str], output_dir: Path) -> str:
    path = output_dir / "blocked_items.md"
    lines = ["# 当前阻塞项", ""]
    if not blockers:
        lines.append("- 当前未识别到阻塞项。")
    else:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _read_strict_performance(strict_outputs_dir: Path) -> pd.DataFrame:
    performance_path = strict_outputs_dir / "performance_summary.csv"
    if not performance_path.exists():
        return pd.DataFrame(
            columns=["experiment", "mean_auc", "std_auc", "mean_train_auc", "n_outer_folds"]
        )
    return pd.read_csv(performance_path)


def _build_small_model_followup_comparison(
    *,
    strict_outputs_dir: Path,
    self_validation_summary_path: str | Path,
    outphase_validation_summary_path: str | Path | None,
    output_dir: Path,
    model_configs: list[dict[str, Any]],
) -> str:
    strict_performance = _read_strict_performance(strict_outputs_dir)
    model_frame = pd.DataFrame(model_configs)
    merged = model_frame.merge(strict_performance, on="experiment", how="left")
    merged = merged.rename(
        columns={
            "mean_auc": "strict_mean_auc",
            "std_auc": "strict_std_auc",
            "mean_train_auc": "strict_mean_train_auc",
            "n_outer_folds": "strict_n_outer_folds",
        }
    )

    self_validation_summary = pd.read_csv(self_validation_summary_path)
    pivot = self_validation_summary.pivot_table(
        index=["experiment", "model_label"],
        columns="validation_scheme",
        values=["mean_auc", "mean_train_auc", "mean_gap", "n_completed", "n_skipped"],
        aggfunc="first",
    )
    if not pivot.empty:
        pivot.columns = [f"{scheme}_{metric}" for metric, scheme in pivot.columns]
        pivot = pivot.reset_index()
        merged = merged.merge(pivot, on=["experiment", "model_label"], how="left")

    if outphase_validation_summary_path and Path(outphase_validation_summary_path).exists():
        outphase_summary = pd.read_csv(outphase_validation_summary_path)
        outphase_pivot = outphase_summary.pivot_table(
            index=["experiment", "model_label"],
            columns="validation_scheme",
            values=["mean_auc", "mean_train_auc", "mean_gap", "n_completed", "n_skipped"],
            aggfunc="first",
        )
        if not outphase_pivot.empty:
            outphase_pivot.columns = [f"{scheme}_{metric}" for metric, scheme in outphase_pivot.columns]
            outphase_pivot = outphase_pivot.reset_index()
            merged = merged.merge(outphase_pivot, on=["experiment", "model_label"], how="left")

    comparison_path = output_dir / "small_model_followup_comparison.csv"
    merged.to_csv(comparison_path, index=False)
    return str(comparison_path)


def _build_school_group_holdout_summary(
    *,
    group_frame: pd.DataFrame,
    positive_label: str,
    mapping_csv_path: str | Path,
    self_validation_fold_metrics_path: str | Path,
    outphase_validation_fold_metrics_path: str | Path | None,
    output_dir: Path,
) -> str:
    mapping = pd.read_csv(mapping_csv_path)
    group = group_frame.merge(mapping, on="ID", how="inner")
    group["is_response"] = group["Group"].astype(str).eq(positive_label).astype(int)
    baseline_summary = (
        group.groupby("school", dropna=False)
        .agg(
            baseline_n=("ID", "size"),
            response_n=("is_response", "sum"),
            intensity=("intensity", lambda s: " | ".join(sorted(set(map(str, s.dropna()))))),
        )
        .reset_index()
        .rename(columns={"school": "holdout_group"})
    )
    baseline_summary["noresponse_n"] = baseline_summary["baseline_n"] - baseline_summary["response_n"]
    baseline_summary["response_rate"] = baseline_summary["response_n"] / baseline_summary["baseline_n"]

    self_folds = pd.read_csv(self_validation_fold_metrics_path)
    self_school = (
        self_folds.loc[self_folds["validation_scheme"] == "leave_one_school_out"]
        .rename(
            columns={
                "n_test": "self_test_n",
                "status": "self_status",
                "auc": "self_auc",
                "train_auc": "self_train_auc",
            }
        )[["model_label", "holdout_group", "self_test_n", "self_status", "self_auc", "self_train_auc"]]
        if "validation_scheme" in self_folds.columns
        else pd.DataFrame(columns=["model_label", "holdout_group", "self_test_n", "self_status", "self_auc", "self_train_auc"])
    )

    outphase_school = pd.DataFrame(
        columns=["model_label", "holdout_group", "outphase_test_n", "outphase_status", "outphase_auc", "outphase_train_auc"]
    )
    if outphase_validation_fold_metrics_path and Path(outphase_validation_fold_metrics_path).exists():
        outphase_folds = pd.read_csv(outphase_validation_fold_metrics_path)
        if "validation_scheme" in outphase_folds.columns:
            outphase_school = outphase_folds.loc[
                outphase_folds["validation_scheme"] == "outphase_leave_one_school_out"
            ].rename(
                columns={
                    "n_test": "outphase_test_n",
                    "status": "outphase_status",
                    "auc": "outphase_auc",
                    "train_auc": "outphase_train_auc",
                }
            )[
                ["model_label", "holdout_group", "outphase_test_n", "outphase_status", "outphase_auc", "outphase_train_auc"]
            ]

    if self_school.empty and outphase_school.empty:
        return ""

    model_labels = sorted(set(self_school.get("model_label", pd.Series(dtype=object))) | set(outphase_school.get("model_label", pd.Series(dtype=object))))
    grid = pd.MultiIndex.from_product(
        [model_labels, baseline_summary["holdout_group"].astype(str).tolist()],
        names=["model_label", "holdout_group"],
    ).to_frame(index=False)

    summary = (
        grid.merge(baseline_summary, on="holdout_group", how="left")
        .merge(self_school, on=["model_label", "holdout_group"], how="left")
        .merge(outphase_school, on=["model_label", "holdout_group"], how="left")
        .sort_values(["model_label", "holdout_group"])
        .reset_index(drop=True)
    )
    path = output_dir / "school_group_holdout_summary.csv"
    summary.to_csv(path, index=False)
    return str(path)


def _write_followup_summary(
    *,
    strict_outputs_dir: Path,
    group_audit_result: dict[str, Any],
    self_validation_result: dict[str, Any],
    outphase_result: dict[str, Any] | None,
    small_model_comparison_path: str,
    figure_outputs: dict[str, str],
    alignment_note_path: str,
    blocked_items: list[str],
    group_mapping_csv_path: str | None,
    school_group_holdout_summary_path: str | None,
    output_dir: Path,
) -> str:
    strict_performance = _read_strict_performance(strict_outputs_dir)
    self_validation_summary = pd.read_csv(self_validation_result["self_validation_summary_csv"])
    outphase_summary = (
        pd.read_csv(outphase_result["outphase_validation_summary_csv"])
        if outphase_result and outphase_result.get("status") == "completed"
        else pd.DataFrame()
    )
    small_model_comparison = pd.read_csv(small_model_comparison_path)
    has_school_split = "leave_one_school_out" in set(self_validation_summary.get("validation_scheme", pd.Series(dtype=object)).astype(str))

    path = output_dir / "followup_summary.md"
    lines = [
        "# responder follow-up 第一阶段汇总",
        "",
        "## 1. 正式主结果（只读引用既有 strict nested CV）",
        "",
        "以下内容继续以既有 strict nested CV 为主口径，不在本轮覆盖旧目录。",
        "",
        _format_markdown_table(strict_performance)
        if not strict_performance.empty
        else "- 未找到 strict nested CV performance_summary.csv。",
        "",
        "## 2. 补充稳健性证据（不是外部验证）",
        "",
        "- repeated random hold-out：作为内部自我验证。",
        (
            "- leave-one-school-out：本轮已接入**真实 school grouped split**，但仍属于内部 grouped validation，不得表述为 external validation。"
            if has_school_split
            else "- leave-one-prefix-out：仅作为 **exploratory weak proxy**，不得表述为外部验证。"
        ),
        (
            "- 旧的 leave-one-prefix-out 仍只能保留为早期 grouped weak proxy；由于 prefix 与 school 并非一一对应，**不能把旧的 leave-one-prefix-out 改名成学校 split**。"
            if has_school_split
            else ""
        ),
        "",
        _format_markdown_table(self_validation_summary),
        "",
        "## 3. 内部时相验证（out-phase，不是外部验证）",
        "",
        (
            _format_markdown_table(outphase_summary)
            if not outphase_summary.empty
            else "- 当前未执行 out-phase 验证。"
        ),
        "",
        "## 4. 小模型 follow-up 比较",
        "",
        _format_markdown_table(small_model_comparison),
        "",
    ]
    if has_school_split:
        lines.extend(
            [
                "## 5. 学校 grouped split 补充产物",
                "",
                f"- 学校/强度映射：`{group_mapping_csv_path}`" if group_mapping_csv_path else "- 学校/强度映射：未导出。",
                f"- 学校留一汇总：`{school_group_holdout_summary_path}`" if school_group_holdout_summary_path else "- 学校留一汇总：未导出。",
                "",
            ]
        )
    lines.extend(
        [
        "## 6. 当前分组证据链",
        "",
        f"- 分组审计：`{group_audit_result['group_definition_audit_markdown']}`",
        f"- 基线平衡表：`{group_audit_result['baseline_balance_summary_csv']}`",
        "- 当前分组来源仅能回溯到会议纪要级证据，不是原始真值表。",
        "",
        "## 7. 本轮新增 follow-up 图组",
        "",
        f"- 小模型 follow-up 主图：`{figure_outputs['followup_figure_model_performance_png']}`",
        f"- generalization gap 图：`{figure_outputs['followup_figure_generalization_gap_png']}`",
        f"- self-validation 分布图：`{figure_outputs['followup_figure_self_validation_distribution_png']}`",
        f"- 当前分组审计图：`{figure_outputs['followup_figure_group_audit_png']}`",
        ]
    )
    if figure_outputs.get("followup_figure_outphase_model_performance_png"):
        lines.extend(
            [
                f"- out-phase 主图：`{figure_outputs['followup_figure_outphase_model_performance_png']}`",
                f"- out-phase 分布图：`{figure_outputs['followup_figure_outphase_distribution_png']}`",
            ]
        )
    lines.extend(
        [
        f"- 分析思路对应说明：`{alignment_note_path}`",
        "",
        "## 8. 待数据到位后再执行",
        "",
        ]
    )
    if blocked_items:
        lines.extend(f"- {item}" for item in blocked_items)
    else:
        lines.append("- 当前未识别到待补数据项。")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def run_followup_analysis(
    *,
    raw_tables: RawProjectTables,
    cohorts: AnalysisCohorts,
    followup_config: dict[str, Any],
    positive_label: str,
) -> dict[str, Any]:
    output_dir = Path(followup_config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    group_audit_result = run_group_audit(
        raw_tables=raw_tables,
        meeting_note_paths=followup_config.get("discussion_paths", []),
        output_dir=output_dir,
        alternative_grouping_config=followup_config.get("alternative_grouping") or {},
    )

    self_validation_result = run_self_validation(
        cohorts=cohorts,
        positive_label=positive_label,
        output_dir=output_dir,
        model_configs=followup_config.get("models", []),
        self_validation_config=followup_config.get("self_validation") or {},
    )

    outphase_config = followup_config.get("outphase_validation") or {}
    outphase_result = run_outphase_validation(
        cohorts=cohorts,
        group_frame=raw_tables.group,
        positive_label=positive_label,
        output_dir=output_dir,
        model_configs=followup_config.get("models", []),
        outphase_config=outphase_config,
    )

    blockers = list(group_audit_result.get("blockers", []))
    if outphase_result.get("status") != "completed":
        blockers.extend(outphase_result.get("blockers", ["缺少出组/干预后同批数据表：本轮不执行出组验证"]))
    blockers.append("缺少心血管表型整理表：本轮不执行机制桥接分析")
    blocked_items_path = _write_blocked_items(blockers, output_dir)
    group_mapping_csv_path = self_validation_result.get("group_mapping_csv") or outphase_result.get("group_mapping_csv")

    comparison_path = _build_small_model_followup_comparison(
        strict_outputs_dir=Path(followup_config.get("strict_outputs_dir", output_dir)),
        self_validation_summary_path=self_validation_result["self_validation_summary_csv"],
        outphase_validation_summary_path=outphase_result.get("outphase_validation_summary_csv"),
        output_dir=output_dir,
        model_configs=followup_config.get("models", []),
    )
    school_group_holdout_summary_path = (
        _build_school_group_holdout_summary(
            group_frame=raw_tables.group,
            positive_label=positive_label,
            mapping_csv_path=group_mapping_csv_path,
            self_validation_fold_metrics_path=self_validation_result["self_validation_fold_metrics_csv"],
            outphase_validation_fold_metrics_path=outphase_result.get("outphase_validation_fold_metrics_csv"),
            output_dir=output_dir,
        )
        if group_mapping_csv_path
        else ""
    )
    figure_outputs = run_followup_figures(
        self_validation_summary_path=self_validation_result["self_validation_summary_csv"],
        self_validation_fold_metrics_path=self_validation_result["self_validation_fold_metrics_csv"],
        small_model_comparison_path=comparison_path,
        baseline_balance_summary_path=group_audit_result["baseline_balance_summary_csv"],
        group_definition_audit_csv_path=group_audit_result["group_definition_audit_csv"],
        output_dir=output_dir,
        outphase_validation_summary_path=outphase_result.get("outphase_validation_summary_csv"),
        outphase_validation_fold_metrics_path=outphase_result.get("outphase_validation_fold_metrics_csv"),
    )
    discussion_paths = [Path(path) for path in followup_config.get("discussion_paths", []) if Path(path).exists()]
    alignment_note_path = write_followup_alignment_note(
        discussion_note_path=discussion_paths[0] if discussion_paths else output_dir / "blocked_items.md",
        output_dir=output_dir,
        outphase_completed=outphase_result.get("status") == "completed",
    )
    summary_path = _write_followup_summary(
        strict_outputs_dir=Path(followup_config.get("strict_outputs_dir", output_dir)),
        group_audit_result=group_audit_result,
        self_validation_result=self_validation_result,
        outphase_result=outphase_result,
        small_model_comparison_path=comparison_path,
        figure_outputs=figure_outputs,
        alignment_note_path=alignment_note_path,
        blocked_items=blockers,
        group_mapping_csv_path=group_mapping_csv_path,
        school_group_holdout_summary_path=school_group_holdout_summary_path,
        output_dir=output_dir,
    )

    return {
        "status": "completed",
        "output_files": {
            "group_definition_audit_markdown": group_audit_result["group_definition_audit_markdown"],
            "group_definition_audit_csv": group_audit_result["group_definition_audit_csv"],
            "baseline_balance_summary": group_audit_result["baseline_balance_summary_csv"],
            "self_validation_summary": self_validation_result["self_validation_summary_csv"],
            "self_validation_fold_metrics": self_validation_result["self_validation_fold_metrics_csv"],
            **(
                {
                    "outphase_validation_summary": outphase_result["outphase_validation_summary_csv"],
                    "outphase_validation_fold_metrics": outphase_result["outphase_validation_fold_metrics_csv"],
                    "outphase_validation_markdown": outphase_result["outphase_validation_markdown"],
                }
                if outphase_result.get("status") == "completed"
                else {}
            ),
            "small_model_followup_comparison": comparison_path,
            "followup_summary": summary_path,
            "blocked_items": blocked_items_path,
            **({"group_mapping_csv": group_mapping_csv_path} if group_mapping_csv_path else {}),
            **({"school_group_holdout_summary": school_group_holdout_summary_path} if school_group_holdout_summary_path else {}),
            **figure_outputs,
            "followup_alignment_note": alignment_note_path,
        },
    }
