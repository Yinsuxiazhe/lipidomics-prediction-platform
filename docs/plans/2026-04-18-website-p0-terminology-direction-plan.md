# Website P0 Terminology & Direction Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current lipid-only Flask website scientifically consistent by exposing delta-style indicator naming, explicit Q/T grouping display, and direction-correct response explanations without pretending clinical/fusion models are already integrated.

**Architecture:** Keep scope tight to the active `website/` Flask app. Normalize model metadata in the backend first, then switch the template to consume those normalized display fields, and finally update the display-logic checklist doc so the current round and next-round work are clearly separated.

**Tech Stack:** Flask, plain HTML/CSS/JS, pytest, existing `website/models/*.pkl` metadata.

---

## File Map

- **Modify:** `website/app.py`
  - Add helper functions for normalized indicator/group display metadata and response-interpretation text.
  - Make `/api/models`, `/api/model_detail/<key>`, and prediction output expose normalized fields.
- **Modify:** `website/templates/index.html`
  - Replace mixed indicator/group rendering with separate delta indicator + explicit Q/T strategy display.
  - Use backend-provided response detail text instead of generic hardcoded text.
  - Update help text, glossary rendering, selected-model bar, batch selector, and performance table wording.
- **Modify:** `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.md`
  - Append final execution status and clarify this round vs next round.
- **Modify:** `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`
  - Sync the same content if feasible after markdown update.
- **Create:** `tests/website/test_app_display_logic.py`
  - Cover normalized metadata exposure and direction-aware interpretation.

---

### Task 1: Add failing backend tests for normalized display metadata

**Files:**
- Create: `tests/website/test_app_display_logic.py`
- Test: `tests/website/test_app_display_logic.py`

- [ ] **Step 1: Write failing test for `/api/models` normalized fields**
- [ ] **Step 2: Run `pytest tests/website/test_app_display_logic.py -q` and confirm failure**
- [ ] **Step 3: Implement backend metadata helpers in `website/app.py`**
- [ ] **Step 4: Re-run the targeted test and confirm pass**

### Task 2: Add failing backend tests for direction-aware response explanations

**Files:**
- Modify: `tests/website/test_app_display_logic.py`
- Modify: `website/app.py`

- [ ] **Step 1: Add failing tests for negative-direction indicators (BMI/PBF/WHR) and positive-direction indicator (PSM)**
- [ ] **Step 2: Run `pytest tests/website/test_app_display_logic.py -q` and confirm failure**
- [ ] **Step 3: Implement minimal response-detail generation using normalized display names and direction fallback**
- [ ] **Step 4: Re-run the targeted test and confirm pass**

### Task 3: Update frontend rendering to consume normalized fields

**Files:**
- Modify: `website/templates/index.html`

- [ ] **Step 1: Replace indicator/group mixed labels with separate delta indicator and explicit Q/T grouping display**
- [ ] **Step 2: Update selected-model summary, batch model summary, performance table, and feature-importance title to use normalized fields**
- [ ] **Step 3: Replace generic hardcoded result-detail text with API-returned detail text**
- [ ] **Step 4: Update help/glossary/i18n strings to explain `Δ = outroll - enroll`, `Q = Q1 vs Q4`, `T = T1 vs T3`, and direction differences**

### Task 4: Update the website display-logic checklist documents

**Files:**
- Modify: `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.md`
- Modify: `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`

- [ ] **Step 1: Add a “本轮已执行 / 下一轮待执行” split**
- [ ] **Step 2: Record final naming rule: indicator column only uses unified delta naming, grouping displayed separately as `Q（Q1 vs Q4）` or `T（T1 vs T3）`**
- [ ] **Step 3: Record next-phase fusion rule: choose the higher-accuracy fusion model within the same validation frame, without forcing fusion as a universal winner**

### Task 5: Verification

**Files:**
- Verify: `website/app.py`, `website/templates/index.html`, `tests/website/test_app_display_logic.py`, related docs

- [ ] **Step 1: Run `pytest tests/website/test_app_display_logic.py -q`**
- [ ] **Step 2: Run `python3 - <<'PY' ...` smoke checks against Flask test client for `/api/models`, `/api/model_detail/<key>`, `/api/glossary`**
- [ ] **Step 3: Review `git diff --stat` and `git diff -- website/app.py website/templates/index.html tests/website/test_app_display_logic.py`**
- [ ] **Step 4: Report exactly what changed, what is still intentionally deferred (clinical-only/fusion UI integration), and any follow-up needed**
