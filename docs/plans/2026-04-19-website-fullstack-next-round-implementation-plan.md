# Website Full-Stack Next-Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver real clinical-only, lipid-only, and fusion training assets plus true website integration for dynamic inputs, model comparison, calibration, DCA, and algorithm tables.

**Architecture:** Reuse the existing GLM5 multi-indicator label pipeline and lipid feature selection, add a new multi-type training/export layer on the aligned cohort, then extend the Flask backend and single-page frontend to consume richer metadata-driven assets. Keep scientific wording fixed around delta targets and extreme-group definitions.

**Tech Stack:** Python, pandas, scikit-learn, xgboost, Flask, pytest, HTML/CSS/JS.

---

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

- [ ] **Step 1: Write failing tests for aligned cohort assembly and feature-space splitting**
- [ ] **Step 2: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py -q` and confirm failure**
- [ ] **Step 3: Implement minimal aligned-data and schema helpers in `src/multi_indicator_glm5/multi_type_assets.py`**
- [ ] **Step 4: Re-run the targeted tests and confirm pass**

### Task 2: Add failing tests for best-model ranking and metadata export rules

**Files:**
- Modify: `tests/multi_indicator_glm5/test_multi_type_assets.py`
- Modify: `src/multi_indicator_glm5/multi_type_assets.py`

- [ ] **Step 1: Add failing tests for best-within-type ranking and fusion-priority rule**
- [ ] **Step 2: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py -q` and confirm failure**
- [ ] **Step 3: Implement ranking/export helpers producing `best_models.json` and `model_metadata.json`**
- [ ] **Step 4: Re-run the targeted tests and confirm pass**

### Task 3: Implement real training/export pipeline

**Files:**
- Modify: `src/multi_indicator_glm5/multi_type_assets.py`

- [ ] **Step 1: Build reusable model registry and nested-CV evaluation with OOF probabilities**
- [ ] **Step 2: Reuse existing phase1 labels and phase2 lipid feature files to assemble clinical/lipid/fusion matrices**
- [ ] **Step 3: Export `performance_summary.csv`, `algorithm_comparison.csv`, `trained_models/*.pkl`, `trained_models/model_metadata.json`**
- [ ] **Step 4: Generate calibration and DCA payloads for each model**
- [ ] **Step 5: Run a focused smoke script on one indicator/group and then the full export script**

### Task 4: Add failing backend tests for new website API shape

**Files:**
- Modify: `tests/website/test_app_display_logic.py`
- Modify: `website/app.py`

- [ ] **Step 1: Add failing tests for `/api/models` exposing `model_type`, `input_schema`, and best-model flags**
- [ ] **Step 2: Add failing tests for `/api/predict` accepting clinical-only and fusion inputs**
- [ ] **Step 3: Add failing tests for `/api/comparison` and `/api/model_family_summary`**
- [ ] **Step 4: Run `pytest tests/website/test_app_display_logic.py -q` and confirm failure**
- [ ] **Step 5: Implement minimal backend changes in `website/app.py`**
- [ ] **Step 6: Re-run the targeted tests and confirm pass**

### Task 5: Extend frontend for dynamic input UI and comparison views

**Files:**
- Modify: `website/templates/index.html`
- Modify: `tests/website/test_frontend_template_polish.py`

- [ ] **Step 1: Add failing tests for model-type selector, clinical input section, and comparison cards presence**
- [ ] **Step 2: Run `pytest tests/website/test_frontend_template_polish.py -q` and confirm failure**
- [ ] **Step 3: Implement metadata-driven rendering for clinical/lipid/fusion inputs**
- [ ] **Step 4: Implement algorithm-comparison, calibration, and DCA panels**
- [ ] **Step 5: Re-run the targeted frontend tests and confirm pass**

### Task 6: Sync trained assets into website runtime directory

**Files:**
- Verify/Create: `website/trained_models/`

- [ ] **Step 1: Copy or sync the exported `.pkl` files and `model_metadata.json` into `website/trained_models/`**
- [ ] **Step 2: Smoke-test Flask model loading against the new metadata structure**
- [ ] **Step 3: Confirm clinical / lipid / fusion model counts are non-zero**

### Task 7: Backfill the project-facing suggestion docs only after functionality is real

**Files:**
- Modify: `20260417_张淑贤_关于网站建议/20260418_网站展示逻辑清单.md`
- Modify: `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`
- Modify: `20260417_张淑贤_关于网站建议/20260418_张淑贤建议.txt`

- [ ] **Step 1: Replace “下一轮待做” items with truthful “本轮已完成” status where implemented**
- [ ] **Step 2: Keep any still-unfinished item explicitly marked as unfinished instead of overclaiming**
- [ ] **Step 3: Record the final fusion selection rule as “best fusion algorithm within the same validation frame”**

### Task 8: Verification

**Files:**
- Verify: training script outputs, `website/app.py`, `website/templates/index.html`, updated tests, updated docs

- [ ] **Step 1: Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py tests/website/test_app_display_logic.py tests/website/test_frontend_template_polish.py -q`**
- [ ] **Step 2: Run a Flask smoke script hitting `/api/models`, `/api/comparison`, `/api/model_family_summary`, `/api/model_detail/<key>`**
- [ ] **Step 3: Review the actual exported model counts and representative metrics from `outputs/20260419_multi_type_glm5/performance_summary.csv`**
- [ ] **Step 4: Only then report completion status, remaining gaps, and whether docs were fully backfilled**
