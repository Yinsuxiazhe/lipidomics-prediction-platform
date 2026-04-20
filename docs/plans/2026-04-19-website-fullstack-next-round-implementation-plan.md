# Website Full-Stack Next-Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver real clinical-only, lipid-only, and fusion training assets plus true website integration for dynamic inputs, model comparison, calibration, DCA, and algorithm tables.

**Architecture:** Reuse the existing GLM5 multi-indicator label pipeline and lipid feature selection, add a new multi-type training/export layer on the aligned cohort, then extend the Flask backend and single-page frontend to consume richer metadata-driven assets. Keep scientific wording fixed around delta targets and extreme-group definitions.

**Tech Stack:** Python, pandas, scikit-learn, xgboost, Flask, pytest, HTML/CSS/JS.

---

## 2026-04-19 / 2026-04-20 Execution Status

- **Status:** Implemented, live, and post-launch hotfixed.
- **Training/export result:** `outputs/20260419_multi_type_glm5/` contains the full 192-model bundle for `clinical / lipid / fusion`.
- **Website integration result:** `website/` now consumes metadata-driven multi-type assets, dynamic input schemas, comparison panels, algorithm tables, calibration, and DCA payloads.
- **2026-04-19 deployment result:** `https://lipid-predict.medaibox.com` served the first full 192-model multi-type release `20260419-184105`.
- **2026-04-20 follow-up hotfix:** `Use Example` no longer shows decimal `Gender`; exporter now uses discrete mode for `Gender`, backend normalizes legacy metadata, and runtime/output metadata have both been backfilled.
- **Current live release:** `20260420-141552`
- **Fresh verification:**
  - `pytest tests/multi_indicator_glm5/test_multi_type_assets.py tests/website/test_app_display_logic.py -q` → `25 passed`
  - live `https://lipid-predict.medaibox.com/api/sample_data/BMI_Q_fusion_RF` → `sample_values.Gender = 0`
  - live `/api/models` remains `192`
  - representative live cross-gender metrics are still no longer fake zeros.
- **Notes for future sessions:** this file is now both the historical execution plan and the completion record for the 2026-04-19 full-stack website round plus the 2026-04-20 sample-value hotfix. `Gender` is categorical and must stay discrete `0/1`; do not compute example/sample display values via arithmetic mean again.

## File Map

- **Create:** `src/multi_indicator_glm5/multi_type_assets.py`
  - Build aligned clinical/lipid/fusion feature spaces, run evaluation, export models + metadata + comparison artifacts.
- **Create:** `tests/multi_indicator_glm5/test_multi_type_assets.py`
  - Cover feature-space assembly, best-model selection, metadata structure, calibration/DCA output shape.
- **Modify:** `website/app.py`
  - Load multi-type metadata, support dynamic schema, prediction, comparison, algorithm-summary APIs.
- **Modify:** `website/templates/index.html`
  - Add model-type UI, dynamic clinical/lipid input blocks, comparison table, calibration/DCA views.
- **Modify:** `tests/website/test_app_display_logic.py`
  - Cover new metadata fields, predict input handling, comparison/model-family endpoints.
- **Modify:** `tests/website/test_frontend_template_polish.py`
  - Cover new UI copy and dynamic-sections hooks.
- **Modify:** `20260417_张淑贤_关于网站建议/20260418_网站展示逻辑清单.md`
- **Modify:** `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`
- **Modify:** `20260417_张淑贤_关于网站建议/20260418_张淑贤建议.txt`

---

### Task 1: Add failing tests for multi-type training asset generation

**Files:**
- Create: `tests/multi_indicator_glm5/test_multi_type_assets.py`
- Test: `tests/multi_indicator_glm5/test_multi_type_assets.py`

- [x] **Step 1: Write failing tests for aligned cohort assembly and feature-space splitting**
- [x] **Step 2: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py -q` and confirm failure**
- [x] **Step 3: Implement minimal aligned-data and schema helpers in `src/multi_indicator_glm5/multi_type_assets.py`**
- [x] **Step 4: Re-run the targeted tests and confirm pass**

### Task 2: Add failing tests for best-model ranking and metadata export rules

**Files:**
- Modify: `tests/multi_indicator_glm5/test_multi_type_assets.py`
- Modify: `src/multi_indicator_glm5/multi_type_assets.py`

- [x] **Step 1: Add failing tests for best-within-type ranking and fusion-priority rule**
- [x] **Step 2: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py -q` and confirm failure**
- [x] **Step 3: Implement ranking/export helpers producing `best_models.json` and `model_metadata.json`**
- [x] **Step 4: Re-run the targeted tests and confirm pass**

### Task 3: Implement real training/export pipeline

**Files:**
- Modify: `src/multi_indicator_glm5/multi_type_assets.py`

- [x] **Step 1: Build reusable model registry and nested-CV evaluation with OOF probabilities**
- [x] **Step 2: Reuse existing phase1 labels and phase2 lipid feature files to assemble clinical/lipid/fusion matrices**
- [x] **Step 3: Export `performance_summary.csv`, `algorithm_comparison.csv`, `trained_models/*.pkl`, `trained_models/model_metadata.json`**
- [x] **Step 4: Generate calibration and DCA payloads for each model**
- [x] **Step 5: Run a focused smoke script on one indicator/group and then the full export script**

### Task 4: Add failing backend tests for new website API shape

**Files:**
- Modify: `tests/website/test_app_display_logic.py`
- Modify: `website/app.py`

- [x] **Step 1: Add failing tests for `/api/models` exposing `model_type`, `input_schema`, and best-model flags**
- [x] **Step 2: Add failing tests for `/api/predict` accepting clinical-only and fusion inputs**
- [x] **Step 3: Add failing tests for `/api/comparison` and `/api/model_family_summary`**
- [x] **Step 4: Run `pytest tests/website/test_app_display_logic.py -q` and confirm failure**
- [x] **Step 5: Implement minimal backend changes in `website/app.py`**
- [x] **Step 6: Re-run the targeted tests and confirm pass**

### Task 5: Extend frontend for dynamic input UI and comparison views

**Files:**
- Modify: `website/templates/index.html`
- Modify: `tests/website/test_frontend_template_polish.py`

- [x] **Step 1: Add failing tests for model-type selector, clinical input section, and comparison cards presence**
- [x] **Step 2: Run `pytest tests/website/test_frontend_template_polish.py -q` and confirm failure**
- [x] **Step 3: Implement metadata-driven rendering for clinical/lipid/fusion inputs**
- [x] **Step 4: Implement algorithm-comparison, calibration, and DCA panels**
- [x] **Step 5: Re-run the targeted frontend tests and confirm pass**

### Task 6: Sync trained assets into website runtime directory

**Files:**
- Verify/Create: `website/trained_models/`

- [x] **Step 1: Copy or sync the exported `.pkl` files and `model_metadata.json` into `website/trained_models/`**
- [x] **Step 2: Smoke-test Flask model loading against the new metadata structure**
- [x] **Step 3: Confirm clinical / lipid / fusion model counts are non-zero**

### Task 7: Backfill the project-facing suggestion docs only after functionality is real

**Files:**
- Modify: `20260417_张淑贤_关于网站建议/20260418_网站展示逻辑清单.md`
- Modify: `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`
- Modify: `20260417_张淑贤_关于网站建议/20260418_张淑贤建议.txt`

- [x] **Step 1: Replace “下一轮待做” items with truthful “本轮已完成” status where implemented**
- [x] **Step 2: Keep any still-unfinished item explicitly marked as unfinished instead of overclaiming**
- [x] **Step 3: Record the final fusion selection rule as “best fusion algorithm within the same validation frame”**

### Task 8: Verification

**Files:**
- Verify: training script outputs, `website/app.py`, `website/templates/index.html`, updated tests, updated docs

- [x] **Step 1: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py tests/website/test_app_display_logic.py tests/website/test_frontend_template_polish.py -q`**
- [x] **Step 2: Run a Flask smoke script hitting `/api/models`, `/api/comparison`, `/api/model_family_summary`, `/api/model_detail/<key>`**
- [x] **Step 3: Review the actual exported model counts and representative metrics from `outputs/20260419_multi_type_glm5/performance_summary.csv`**
- [x] **Step 4: Only then report completion status, remaining gaps, and whether docs were fully backfilled**
