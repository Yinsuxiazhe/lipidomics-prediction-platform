# Follow-up Figure Pack and Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 responder follow-up 第一阶段新增可重复生成的图组，并补一份“分析思路 ↔ 当前结果/阻塞项”对应说明，方便与基线结果一起汇报。

**Architecture:** 在 follow-up pipeline 内新增独立的 figure/report 模块，直接消费已经生成的 `self_validation_summary.csv`、`self_validation_fold_metrics.csv`、`small_model_followup_comparison.csv`、`baseline_balance_summary.csv` 和 `group_definition_audit.csv`，避免重复建模。图形输出统一写入 follow-up 目录，并在 `run_followup.py` 中注册到输出清单。另写一份 alignment markdown，把 `docs/20260311_对接_新的分析思路.txt` 中的关键想法逐条映射到“已完成 / 已补图 / 当前阻塞”。

**Tech Stack:** Python、matplotlib、pandas、现有 follow-up CSV 结果、Markdown 报告。

---

### Task 1: 为 follow-up figure pack 写失败测试

**Files:**
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/followup/test_make_figures.py`
- Reference: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260311_responder_followup/*.csv`

**Step 1: Write the failing test**

写一个最小测试，构造 `self_validation_summary.csv`、`self_validation_fold_metrics.csv`、`small_model_followup_comparison.csv`、`baseline_balance_summary.csv`、`group_definition_audit.csv`，断言新的 `run_followup_figures(...)` 会导出至少以下文件：
- `FigureF1_Followup_ModelPerformance.png`
- `FigureF1_Followup_ModelPerformance.pdf`
- `FigureF2_Followup_GeneralizationGap.png`
- `FigureF3_SelfValidation_Distribution.png`
- `FigureF4_GroupAudit.png`

**Step 2: Run test to verify it fails**

Run: `pytest -q tests/followup/test_make_figures.py::test_run_followup_figures_exports_expected_files`
Expected: FAIL with `ModuleNotFoundError` or missing function.

**Step 3: Write minimal implementation**

新建 `src/followup/make_figures.py`，实现：
- 读取已有 CSV
- 画 4 张图
- 返回输出路径字典

**Step 4: Run test to verify it passes**

Run: `pytest -q tests/followup/test_make_figures.py::test_run_followup_figures_exports_expected_files`
Expected: PASS

### Task 2: 为思路对应说明写失败测试

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/followup/test_make_figures.py`
- Reference: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/20260311_对接_新的分析思路.txt`

**Step 1: Write the failing test**

新增测试，断言 `write_followup_alignment_note(...)` 会生成 markdown，并至少包含：
- “分组定义/差异先审清楚”
- “小模型、稀疏模型、稳定特征”
- “pseudo-external validation”
- “out 的数据做验证”
- “心血管相关表型”
- 对应状态关键词如“已完成”“部分完成”“当前阻塞”

**Step 2: Run test to verify it fails**

Run: `pytest -q tests/followup/test_make_figures.py::test_write_followup_alignment_note_maps_discussion_items`
Expected: FAIL with missing function.

**Step 3: Write minimal implementation**

在 `src/followup/make_figures.py` 或新的轻量报告模块中实现 `write_followup_alignment_note(...)`。

**Step 4: Run test to verify it passes**

Run: `pytest -q tests/followup/test_make_figures.py::test_write_followup_alignment_note_maps_discussion_items`
Expected: PASS

### Task 3: 将 figure pack 与 alignment 接入 follow-up pipeline

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/followup/run_followup.py`
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/test_run_pipeline.py`

**Step 1: Write the failing test**

扩展 pipeline 集成测试，断言 `run_followup_analysis(...)` 的 `output_files` 中新增：
- `followup_figure_model_performance_png`
- `followup_figure_generalization_gap_png`
- `followup_figure_self_validation_distribution_png`
- `followup_figure_group_audit_png`
- `followup_alignment_note`

**Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_run_pipeline.py::test_followup_stage_wires_output_files`
Expected: FAIL because output keys missing.

**Step 3: Write minimal implementation**

在 `run_followup.py` 中调用 figure/alignment 生成函数，并把路径注册进返回结果。

**Step 4: Run test to verify it passes**

Run: `pytest -q tests/test_run_pipeline.py::test_followup_stage_wires_output_files`
Expected: PASS

### Task 4: 全量验证并重跑真实 follow-up

**Files:**
- Verify only

**Step 1: Run focused tests**

Run: `pytest -q tests/followup/test_make_figures.py tests/test_run_pipeline.py`
Expected: PASS

**Step 2: Run full test suite**

Run: `pytest -q`
Expected: PASS

**Step 3: Run follow-up pipeline**

Run: `python run_pipeline.py --stage followup --config config/analysis.yaml`
Expected: exit 0 and new figure/alignment files appear under `outputs/20260311_responder_followup`

**Step 4: Manual artifact check**

核对新图是否存在、命名是否清楚、没有把 prefix-holdout 误写成外部验证。
