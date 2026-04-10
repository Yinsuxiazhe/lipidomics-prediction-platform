# Figure 6-4 Honest Nested CV Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/fig6-4最终.R` so it generates a strict nested-CV, leakage-controlled Figure 6-4, and produce a Chinese briefing note that explains why the old figure looked better but was less reliable.

**Architecture:** Keep strict model training and scoring inside the existing Python nested-CV pipeline, then export additional report-ready artifacts for honest plotting. Rewrite the R script as a reporting layer that reads those strict artifacts and renders a multi-panel figure with ROC, generalization gap, and feature stability panels instead of re-running leakage-prone full-data selection in R.

**Tech Stack:** Python, pytest, pandas, scikit-learn, R, ggplot2, patchwork, jsonlite.

### Task 1: Define the honest reporting payload

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/reports/make_tables.py`
- Test: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/reports/test_make_tables.py`

**Step 1: Write the failing test**
- Add a test asserting the report layer exports:
  - `fold_metrics.csv` with `experiment`, `fold_index`, `auc`, `train_auc`, `selected_feature_count`
  - `feature_stability_summary.csv` with per-experiment ranked features and selection frequency proportion

**Step 2: Run test to verify it fails**
- Run: `python3 -m pytest tests/reports/test_make_tables.py -q`
- Expected: FAIL because the new files/columns do not exist yet.

**Step 3: Write minimal implementation**
- Extend `write_experiment_tables()` to emit the new CSVs from `results["results"][experiment]["fold_results"]` and `feature_frequency`.
- Keep existing outputs unchanged.

**Step 4: Run test to verify it passes**
- Run: `python3 -m pytest tests/reports/test_make_tables.py -q`
- Expected: PASS

### Task 2: Expose honest outputs through the pipeline

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/run_pipeline.py`
- Test: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/test_run_pipeline.py`

**Step 1: Write the failing test**
- Add assertions that `run_stage(stage="experiments", ...)` returns the new output file paths in `output_files`.

**Step 2: Run test to verify it fails**
- Run: `python3 -m pytest tests/test_run_pipeline.py -q`
- Expected: FAIL because the new keys are absent.

**Step 3: Write minimal implementation**
- Reuse the updated `write_experiment_tables()` return payload so `run_stage()` includes the new files automatically.

**Step 4: Run test to verify it passes**
- Run: `python3 -m pytest tests/test_run_pipeline.py -q`
- Expected: PASS

### Task 3: Rewrite the R figure script as an honest reporting layer

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/fig6-4最终.R`

**Step 1: Replace hard-coded remote paths with project-relative paths**
- The script must use the current project root and `outputs/20260310_nested_cv` as its data source.

**Step 2: Load strict nested-CV artifacts**
- Read `performance_summary.csv`, `roc_curve_points.csv`, `fold_metrics.csv`, `feature_stability_summary.csv`.
- Optionally trigger a pipeline rerun only if required artifacts are missing.

**Step 3: Build honest multi-panel figure**
- Panel A: clinical baseline comparison ROC.
- Panel B: lipid contribution ROC.
- Panel C: fusion vs fusion-full ROC.
- Panel D: fold-level train/test AUC gap summary.
- Panel E: top stable features summary for the strict fusion model.
- Add a subtitle/note that all ROC curves are aggregated outer-fold predictions from strict nested CV.

**Step 4: Save outputs locally**
- Save `.png` and `.pdf` into `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/`.

### Task 4: Generate real artifacts and briefing note

**Files:**
- Modify/Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/*`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`

**Step 1: Run strict experiments**
- Run: `python3 run_pipeline.py --stage experiments --config config/analysis.yaml`
- Expected: updated CSV/JSON outputs including the new honest-report files.

**Step 2: Run the R plotting script**
- Run: `Rscript fig6-4最终.R`
- Expected: honest figure `.png` and `.pdf` are generated.

**Step 3: Write the briefing note**
- Explain in easy report language:
  - old figure used full-data preprocessing/feature selection before validation
  - old ROC was internal CV display, not independent external testing
  - strict nested CV answers a harder but more reliable question
  - current lower AUC means the signal is weaker than the old figure suggested, not that the new analysis is wrong

### Task 5: Verification

**Files:**
- Verify only

**Step 1: Unit tests**
- Run: `python3 -m pytest tests/reports/test_make_tables.py tests/test_run_pipeline.py -q`

**Step 2: Full test suite**
- Run: `python3 -m pytest tests -q`

**Step 3: Artifact verification**
- Check existence of:
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv`
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`

**Step 4: Briefing note verification**
- Confirm the explanation file exists and includes a short conclusion plus 3-5 bullet proof points.
