from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.io.load_data import RawProjectTables

DEFAULT_BASELINE_COLUMNS = ["age_enroll", "bmi_z_enroll", "SFT", "Gender", "BMI"]


def _safe_standardized_mean_difference(response_values: pd.Series, noresponse_values: pd.Series) -> float:
    response_numeric = pd.to_numeric(response_values, errors="coerce").dropna()
    noresponse_numeric = pd.to_numeric(noresponse_values, errors="coerce").dropna()
    if response_numeric.empty or noresponse_numeric.empty:
        return float("nan")

    mean_diff = response_numeric.mean() - noresponse_numeric.mean()
    pooled = np.sqrt((response_numeric.var(ddof=0) + noresponse_numeric.var(ddof=0)) / 2)
    if np.isnan(pooled) or pooled == 0:
        return 0.0
    return float(mean_diff / pooled)


def _compute_baseline_balance(raw_tables: RawProjectTables) -> pd.DataFrame:
    clinical = raw_tables.clinical_slim.copy()
    merged = raw_tables.group.merge(clinical, on="ID", how="inner")

    rows: list[dict[str, Any]] = []
    for column in DEFAULT_BASELINE_COLUMNS:
        if column not in merged.columns:
            continue
        response_values = merged.loc[merged["Group"] == "response", column]
        noresponse_values = merged.loc[merged["Group"] == "noresponse", column]
        rows.append(
            {
                "variable": column,
                "response_mean": pd.to_numeric(response_values, errors="coerce").mean(),
                "noresponse_mean": pd.to_numeric(noresponse_values, errors="coerce").mean(),
                "response_median": pd.to_numeric(response_values, errors="coerce").median(),
                "noresponse_median": pd.to_numeric(noresponse_values, errors="coerce").median(),
                "response_n": int(response_values.notna().sum()),
                "noresponse_n": int(noresponse_values.notna().sum()),
                "standardized_mean_difference": _safe_standardized_mean_difference(response_values, noresponse_values),
            }
        )
    return pd.DataFrame(rows)


def _compute_prefix_distribution(group_frame: pd.DataFrame) -> pd.DataFrame:
    working = group_frame.copy()
    working["prefix"] = working["ID"].astype(str).str[0]
    summary = (
        working.assign(is_response=working["Group"].eq("response").astype(int))
        .groupby("prefix", dropna=False)
        .agg(
            n=("ID", "size"),
            response_n=("is_response", "sum"),
        )
        .reset_index()
    )
    summary["noresponse_n"] = summary["n"] - summary["response_n"]
    summary["response_rate"] = summary["response_n"] / summary["n"]
    return summary.sort_values("prefix").reset_index(drop=True)


def _extract_discussion_evidence(meeting_note_paths: list[Path]) -> tuple[list[str], list[dict[str, str]]]:
    evidence_lines: list[str] = []
    evidence_rows: list[dict[str, str]] = []
    keywords = ("ΔBMI", "pdmi", "百分位", "灰区", "基线无显著差异", "多轮尝试")

    for path in meeting_note_paths:
        if not path.exists():
            evidence_rows.append(
                {
                    "record_type": "discussion_path",
                    "key": str(path),
                    "value": "missing",
                    "note": "讨论文件不存在，无法提取会议纪要级证据。",
                }
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        matched = [line.strip() for line in text.splitlines() if any(keyword in line for keyword in keywords)]
        snippet = matched[0] if matched else "未自动命中关键词，保留文件路径作为人工复核线索。"
        evidence_rows.append(
            {
                "record_type": "discussion_path",
                "key": str(path),
                "value": "available",
                "note": snippet,
            }
        )
        if matched:
            evidence_lines.append(f"- `{path}`：{matched[0]}")
        else:
            evidence_lines.append(f"- `{path}`：已纳入人工复核线索，但未自动命中关键词。")

    return evidence_lines, evidence_rows


def _build_group_definition_audit_rows(
    raw_tables: RawProjectTables,
    prefix_distribution: pd.DataFrame,
    discussion_rows: list[dict[str, str]],
    blockers: list[str],
) -> pd.DataFrame:
    label_counts = raw_tables.group["Group"].astype(str).value_counts().sort_index()
    rows: list[dict[str, Any]] = [
        {
            "record_type": "label_count",
            "key": label,
            "value": int(count),
            "note": "当前二分类标签文件中的样本数。",
        }
        for label, count in label_counts.items()
    ]
    rows.extend(discussion_rows)
    rows.extend(
        {
            "record_type": "id_prefix_distribution",
            "key": row.prefix,
            "value": int(row.n),
            "note": f"response_n={int(row.response_n)}, noresponse_n={int(row.noresponse_n)}, response_rate={row.response_rate:.4f}",
        }
        for row in prefix_distribution.itertuples(index=False)
    )
    rows.extend(
        {
            "record_type": "blocker",
            "key": f"blocker_{idx+1}",
            "value": blocker,
            "note": "当前只完成可接入化，不生成伪敏感性结果。",
        }
        for idx, blocker in enumerate(blockers)
    )
    return pd.DataFrame(rows)


def _format_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "（空）"
    printable = frame.copy()
    for column in printable.columns:
        printable[column] = printable[column].map(
            lambda value: f"{value:.4f}" if isinstance(value, (float, np.floating)) and pd.notna(value) else value
        )
    headers = [str(column) for column in printable.columns]
    rows = printable.astype(object).where(pd.notna(printable), "").values.tolist()
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def _write_blocked_items(blockers: list[str], path: Path) -> None:
    lines = ["# 当前阻塞项", ""]
    if not blockers:
        lines.append("- 当前未识别到阻塞项。")
    else:
        for blocker in blockers:
            lines.append(f"- {blocker}；当前只完成可接入化，不生成伪敏感性结果。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_group_audit(
    raw_tables: RawProjectTables,
    meeting_note_paths: list[str | Path],
    output_dir: str | Path,
    alternative_grouping_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    alt_cfg = alternative_grouping_config or {}
    blockers: list[str] = []
    if not alt_cfg.get("endpoint_source"):
        blockers.append("缺少 endpoint_source：本地没有用于重定义 responder 的原始连续终点文件")
    if alt_cfg.get("endpoint_source") and not Path(alt_cfg["endpoint_source"]).exists():
        blockers.append(f"endpoint_source 不存在：{alt_cfg['endpoint_source']}")
    if alt_cfg.get("endpoint_source") and not alt_cfg.get("endpoint_value_column"):
        blockers.append("缺少 endpoint_value_column：无法从原始终点表映射连续响应值")

    baseline_balance = _compute_baseline_balance(raw_tables)
    prefix_distribution = _compute_prefix_distribution(raw_tables.group)
    discussion_lines, discussion_rows = _extract_discussion_evidence([Path(path) for path in meeting_note_paths])
    audit_rows = _build_group_definition_audit_rows(raw_tables, prefix_distribution, discussion_rows, blockers)

    baseline_path = output_path / "baseline_balance_summary.csv"
    baseline_balance.to_csv(baseline_path, index=False)

    audit_csv_path = output_path / "group_definition_audit.csv"
    audit_rows.to_csv(audit_csv_path, index=False)

    blocked_items_path = output_path / "blocked_items.md"
    _write_blocked_items(blockers, blocked_items_path)

    label_counts = raw_tables.group["Group"].astype(str).value_counts().sort_index().to_dict()
    audit_markdown = output_path / "group_definition_audit.md"
    audit_markdown.write_text(
        "\n".join(
            [
                "# 当前 responder 分组证据链审计",
                "",
                "## 1. 当前标签文件概况",
                "",
                f"- 当前 `281_new_grouped.csv` 风格标签文件只提供二分类结果：{label_counts}。",
                "- 当前分组依据仅能回溯到会议纪要级证据，**不是原始真值表**。",
                "",
                "## 2. 会议纪要级证据",
                "",
                *(discussion_lines or ["- 未提供可读取的会议纪要路径。"]),
                "",
                "## 3. 基线平衡性（当前仅基于基线锚点变量）",
                "",
                _format_markdown_table(baseline_balance),
                "",
                "## 4. ID 前缀分布（仅作招募/波次弱线索）",
                "",
                _format_markdown_table(prefix_distribution),
                "",
                "## 5. alternative-grouping readiness",
                "",
                "- 若缺少原始连续终点文件，本轮只完成可接入化与阻塞项登记，不生成伪瀑布图、不跑伪敏感性结果。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "group_definition_audit_markdown": str(audit_markdown),
        "group_definition_audit_csv": str(audit_csv_path),
        "baseline_balance_summary_csv": str(baseline_path),
        "blocked_items_path": str(blocked_items_path),
        "blockers": blockers,
    }
