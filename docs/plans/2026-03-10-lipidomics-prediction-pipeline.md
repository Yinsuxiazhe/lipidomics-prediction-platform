# Lipidomics Prediction Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a reproducible end-to-end pipeline that ingests the 281-label cohort, lipidomics matrix, and clinical tables; constructs aligned analysis cohorts; runs leakage-safe nested cross-validation experiments; and exports model results, figures, and tables for the lipidomics response-prediction study.

**Architecture:** The pipeline is organized as a linear but modular flow: raw input loading and validation, cohort building, training-fold-only preprocessing and feature screening, nested-CV model execution, and report generation. The first implementation milestone focuses on a stable scaffold with explicit config, deterministic file paths, validated cohort assembly, and an experiment registry so later modeling logic can be added without rewriting the orchestration layer.

**Tech Stack:** Python 3, pandas, numpy, PyYAML, pytest, scikit-learn (planned runtime dependency), pathlib, dataclasses.

---

### Task 1: Define configuration and pipeline entrypoint

**Files:**
- Create: `config/analysis.yaml`
- Create: `run_pipeline.py`
- Test: `tests/test_run_pipeline.py`

**Step 1: Write the failing test**

```python
def test_loads_default_pipeline_config(tmp_path):
    config_path = tmp_path / "analysis.yaml"
    config_path.write_text("project_name: lipidomics\n")

    config = load_pipeline_config(config_path)

    assert config["project_name"] == "lipidomics"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_run_pipeline.py -v`
Expected: FAIL with `ImportError` or `NameError` because `load_pipeline_config` does not exist yet.

**Step 3: Write minimal implementation**

```python
def load_pipeline_config(config_path):
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
```

Add a simple CLI entrypoint in `run_pipeline.py` that loads YAML config and supports a `--stage` argument.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_run_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add config/analysis.yaml run_pipeline.py tests/test_run_pipeline.py
git commit -m "feat: add pipeline config entrypoint"
```

### Task 2: Build raw input loading layer

**Files:**
- Create: `src/io/__init__.py`
- Create: `src/io/load_data.py`
- Test: `tests/io/test_load_data.py`

**Step 1: Write the failing test**

```python
def test_load_project_tables_standardizes_key_ids(tmp_path):
    group = tmp_path / "group.csv"
    group.write_text("ID,Group\nA001,response\n")
    lipid = tmp_path / "lipid.csv"
    lipid.write_text("NAME,L1\nA001,1.0\n")
    clinical = tmp_path / "clinical.csv"
    clinical.write_text("ID,age_enroll\nA001,10\n")

    data = load_project_tables(...)

    assert list(data.group.columns) == ["ID", "Group"]
    assert data.lipid["NAME"].dtype == object
    assert data.clinical_full["ID"].dtype == object
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/io/test_load_data.py -v`
Expected: FAIL because `load_project_tables` does not exist.

**Step 3: Write minimal implementation**

Create a `RawProjectTables` dataclass plus `load_project_tables()` that reads CSV files, coerces ID columns to string, and returns standardized tables.

**Step 4: Run test to verify it passes**

Run: `pytest tests/io/test_load_data.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/io/__init__.py src/io/load_data.py tests/io/test_load_data.py
git commit -m "feat: add raw data loader"
```

### Task 3: Validate inputs and build aligned cohorts

**Files:**
- Create: `src/io/validate_inputs.py`
- Create: `src/data/__init__.py`
- Create: `src/data/build_cohort.py`
- Test: `tests/data/test_build_cohort.py`

**Step 1: Write the failing test**

```python
def test_build_analysis_cohorts_keeps_overlap_only():
    raw = RawProjectTables(...)

    cohorts = build_analysis_cohorts(raw)

    assert cohorts.group_lipid.shape[0] == 2
    assert cohorts.group_clinical_slim.shape[0] == 2
    assert cohorts.group_fusion.shape[0] == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_build_cohort.py -v`
Expected: FAIL because `build_analysis_cohorts` does not exist.

**Step 3: Write minimal implementation**

Implement:
- duplicate-ID validation
- overlap-ID intersection
- slim clinical selection
- fusion table generation
- cohort summary metadata

**Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_build_cohort.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/io/validate_inputs.py src/data/__init__.py src/data/build_cohort.py tests/data/test_build_cohort.py
git commit -m "feat: add cohort builder"
```

### Task 4: Define experiment registry and nested-CV scaffold

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/run_nested_cv.py`
- Test: `tests/models/test_run_nested_cv.py`

**Step 1: Write the failing test**

```python
def test_default_experiment_registry_contains_core_models():
    registry = build_default_experiment_registry()

    assert set(registry) >= {
        "clinical_slim_logistic",
        "lipid_elastic_net",
        "clinical_full_elastic_net",
        "fusion_elastic_net",
    }
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_run_nested_cv.py -v`
Expected: FAIL because registry builder is missing.

**Step 3: Write minimal implementation**

Create dataclasses for experiment specification and a scaffolded `run_experiments()` function that validates requested cohorts/stages and returns a structured execution manifest. Defer full scikit-learn fitting to the next milestone, but make the public API stable now.

**Step 4: Run test to verify it passes**

Run: `pytest tests/models/test_run_nested_cv.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/__init__.py src/models/run_nested_cv.py tests/models/test_run_nested_cv.py
git commit -m "feat: add experiment registry scaffold"
```

### Task 5: Wire the stage runner for dry-run execution

**Files:**
- Modify: `run_pipeline.py`
- Test: `tests/test_run_pipeline.py`

**Step 1: Write the failing test**

```python
def test_pipeline_dry_run_returns_selected_stage_manifest(tmp_path):
    manifest = run_stage(stage="cohort", config_path=tmp_path / "analysis.yaml", dry_run=True)
    assert manifest["stage"] == "cohort"
    assert manifest["status"] == "dry_run"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_run_pipeline.py -v`
Expected: FAIL because `run_stage` or dry-run support is missing.

**Step 3: Write minimal implementation**

Add `run_stage()` and stage dispatch for `validate`, `cohort`, and `experiments` dry-run paths.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_run_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add run_pipeline.py tests/test_run_pipeline.py
git commit -m "feat: add pipeline stage dispatcher"
```

### Task 6: Prepare second-wave modeling tasks (next session)

**Files:**
- Create: `src/preprocess/lipid_transform.py`
- Create: `src/preprocess/clinical_filter.py`
- Create: `src/features/univariate_screen.py`
- Create: `src/features/correlation_prune.py`
- Create: `src/models/fit_final_model.py`
- Create: `src/eval/metrics.py`
- Create: `src/eval/calibration.py`
- Create: `src/reports/make_tables.py`
- Create: `src/reports/make_figures.py`
- Test: `tests/...`

**Step 1: Write the failing tests**

Write targeted tests for each fold-safe preprocessing component before adding production code.

**Step 2: Run tests to verify they fail**

Run: `pytest tests -v`
Expected: FAIL for the new modules.

**Step 3: Write minimal implementation**

Implement one module at a time with leakage-safe train-fold fitting and serializable outputs.

**Step 4: Run tests to verify they pass**

Run: `pytest tests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/preprocess src/features src/eval src/reports src/models/fit_final_model.py tests
git commit -m "feat: add fold-safe preprocessing and reporting modules"
```
