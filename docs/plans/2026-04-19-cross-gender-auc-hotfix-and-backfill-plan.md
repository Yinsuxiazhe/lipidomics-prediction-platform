# Cross-Gender AUC Hotfix and Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the website so missing cross-gender AUCs never display as fake zeros, then compute and ship the real M→F / F→M metrics for the 192-model multi-type release.

**Architecture:** Reuse the existing multi-type aligned cohort pipeline for clinical/lipid/fusion feature spaces, add a gender-transfer evaluation layer inside `multi_type_assets.py`, persist the results into `performance_summary.csv` and `model_metadata.json`, and make the Flask + frontend rendering treat absent values as null/— rather than `0`.

**Tech Stack:** Python, pandas, scikit-learn, xgboost, Flask, pytest, HTML/CSS/JS.

---

## File Map

- **Modify:** `src/multi_indicator_glm5/multi_type_assets.py`
  - Add reusable cross-gender evaluation helpers and persist cross-gender metrics into exported assets.
- **Modify:** `tests/multi_indicator_glm5/test_multi_type_assets.py`
  - Add tests for cross-gender metric computation and metadata export shape.
- **Modify:** `website/app.py`
  - Stop defaulting missing cross-gender metrics to `0`; propagate `None`/null instead.
- **Modify:** `website/templates/index.html`
  - Render missing cross-gender metrics as `—` and avoid false green/red styling on nulls.
- **Modify:** `tests/website/test_app_display_logic.py`
  - Add tests for null cross-gender metrics in API payloads.
- **Modify:** `tests/website/test_frontend_template_polish.py`
  - Add template assertions for null-safe rendering helpers.

---

### Task 1: Lock failing tests for null-safe display

**Files:**
- Modify: `tests/website/test_app_display_logic.py`
- Modify: `tests/website/test_frontend_template_polish.py`

- [ ] Add a backend test proving missing `m2f_auroc/f2m_auroc` stays `None` rather than `0`.
- [ ] Add a frontend test proving the template contains a null-safe formatter for AUC cells.
- [ ] Run `pytest tests/website/test_app_display_logic.py tests/website/test_frontend_template_polish.py -q` and confirm failure.

### Task 2: Lock failing tests for cross-gender export

**Files:**
- Modify: `tests/multi_indicator_glm5/test_multi_type_assets.py`

- [ ] Add a helper-level test for male→female / female→male metric computation.
- [ ] Add a metadata export test proving `build_metadata_entry()` includes `m2f_auroc`, `f2m_auroc`, and `cross_avg_auroc`.
- [ ] Run `pytest tests/multi_indicator_glm5/test_multi_type_assets.py -q` and confirm failure.

### Task 3: Implement the real fix

**Files:**
- Modify: `src/multi_indicator_glm5/multi_type_assets.py`
- Modify: `website/app.py`
- Modify: `website/templates/index.html`

- [ ] Implement null-preserving metric serialization in backend + frontend.
- [ ] Implement cross-gender evaluation on aligned multi-type subsets using `Gender` (0=male, 1=female).
- [ ] Persist cross-gender metrics into `performance_summary.csv`, `trained_models/model_metadata.json`, and website-synced metadata.
- [ ] Re-run the targeted pytest set until green.

### Task 4: Re-export, deploy, and verify

**Files:**
- Verify: `outputs/20260419_multi_type_glm5/*`
- Verify: `website/trained_models/model_metadata.json`
- Verify: live deployment

- [ ] Run the export pipeline and confirm 192 models remain present.
- [ ] Confirm representative models now have real `m2f_auroc/f2m_auroc` values (or null where scientifically uncomputable).
- [ ] Deploy to the server, restart the service, and verify the live API/UI no longer show fake zeros.
