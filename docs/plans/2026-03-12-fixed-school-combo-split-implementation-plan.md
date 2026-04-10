# Fixed School Combo Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有真实学校映射基础上，设计 2 个固定校区 train/test 组合方案，并为其中 1 个方案增加最小代码支持与局部分析产物，且不改动 strict nested CV 主锚点。

**Architecture:** 复用现有 school grouped validation 流程，不重写模型或主 pipeline。仅在 `self_validation` / `outphase_validation` 中新增一个可选的 fixed school combo split 分支：在保留 repeated hold-out 与 leave-one-school-out 能力的同时，允许额外执行一个“固定 test 学校集合”的单次 grouped split。真实数据分析输出写入独立子目录，避免覆盖当前 teacher/formal package 主结果。

**Tech Stack:** Python 3、pandas、pytest、现有 follow-up pipeline、YAML 配置字典、局部脚本运行。

---

### Task 1: 固定校区方案设计与落盘

**Files:**
- Create: `docs/plans/2026-03-12-fixed-school-combo-split-implementation-plan.md`
- Create: `outputs/20260311_responder_followup/fixed_school_combo_design.md`
- Read: `outputs/20260311_responder_followup/school_group_holdout_summary.csv`

**Step 1: 基于学校分布计算候选组合**

Run:
```bash
python3 - <<'PY'
import itertools
import pandas as pd
meta = pd.read_csv('outputs/20260311_responder_followup/school_group_holdout_summary.csv')
meta = meta[meta['model_label']=='clinical_baseline_main'][['holdout_group','baseline_n','response_n','noresponse_n','response_rate','intensity']]
print(meta)
PY
```

Expected: 明确 7 个学校的 `baseline_n / response_rate / intensity` 分布。

**Step 2: 固化两个候选方案**

候选方案必须至少包含：
- 1 个 `5 校区 train + 2 校区 test`
- 1 个 `4 校区 train + 3 校区 test`

并写明每个方案的：
- train schools
- test schools
- train/test 样本量
- train/test response rate
- 是否同时覆盖三种 intensity
- 为什么合理

**Step 3: 选定实施方案**

优先选：
- test 集样本量不太小
- train/test response rate 差距较小
- train/test 都尽量覆盖多种 intensity
- 不需要重写 figures / teacher package

---

### Task 2: 先写失败测试，定义 fixed school combo 行为

**Files:**
- Modify: `tests/followup/test_school_split.py`
- Modify: `tests/followup/test_self_validation.py`
- Modify: `tests/followup/test_outphase_validation.py`

**Step 1: 写 fixed split 配置解析测试**

测试内容：
- 当 `pseudo_external.fixed_group_split.enabled=true` 且给定 `test_groups` 时，能解析出 fixed split 元数据
- `test_groups` 必须存在于当前 group values 中
- 能生成稳定的 `holdout_group_label`

**Step 2: 写 self-validation fixed school combo 测试**

测试内容：
- `group_by=school` 且启用 `fixed_group_split` 时，summary 新增 `fixed_school_combo_holdout`
- fold metrics 中该 scheme 恰好 1 条 split
- `holdout_group` 为指定学校组合字符串

**Step 3: 写 outphase fixed school combo 测试**

测试内容：
- `group_by=school` 且启用 `fixed_group_split` 时，summary 新增 `outphase_fixed_school_combo_holdout`
- report 继续写清楚“不是 external validation”
- fold metrics 中该 scheme 恰好 1 条 split

**Step 4: 跑测试确认失败**

Run:
```bash
pytest -q tests/followup/test_school_split.py tests/followup/test_self_validation.py tests/followup/test_outphase_validation.py
```

Expected: 因 fixed combo split 尚未实现而失败。

---

### Task 3: 最小实现 fixed school combo split

**Files:**
- Modify: `src/followup/school_split.py`
- Modify: `src/followup/self_validation.py`
- Modify: `src/followup/outphase_validation.py`

**Step 1: 在 `school_split.py` 增加 fixed split 元数据解析 helper**

新增最小函数：
```python
def resolve_fixed_group_split(group_values: pd.Series, *, group_meta: dict[str, Any], fixed_group_split_config: dict[str, Any] | None) -> dict[str, Any] | None: ...
```

要求：
- 未启用时返回 `None`
- 启用时校验 `test_groups`
- 返回 `test_groups`、`holdout_group_label`、`validation_scheme`
- school 场景下 scheme 命名为 `fixed_school_combo_holdout`

**Step 2: 在 `self_validation.py` 增加单次 fixed grouped split runner**

新增最小函数：
```python
def _run_fixed_group_split(...): ...
```

要求：
- 只生成 1 条 split
- train = 非 test_groups 的所有样本
- test = test_groups 的所有样本
- 继续复用 `_fit_and_score_split`

**Step 3: 在 `outphase_validation.py` 增加单次 outphase fixed grouped split runner**

要求：
- baseline train / outphase test 的 paired ID 逻辑不变
- 只新增 `outphase_fixed_school_combo_holdout`
- report 仍明确 internal temporal validation，而非 external validation

---

### Task 4: 跑绿测试并做局部真实数据分析

**Files:**
- Create: `outputs/20260311_responder_followup/fixed_school_combo_balanced_4train3test/`
- Create: `outputs/20260311_responder_followup/fixed_school_combo_design.md`
- Create: `outputs/20260311_responder_followup/fixed_school_combo_balanced_4train3test/fixed_school_combo_summary.md`

**Step 1: 运行 focused tests**

Run:
```bash
pytest -q tests/followup/test_school_split.py tests/followup/test_self_validation.py tests/followup/test_outphase_validation.py
```

Expected: 全部通过。

**Step 2: 运行真实数据的局部 fixed combo 分析**

用单独 Python 脚本调用：
- `run_self_validation(...)`
- `run_outphase_validation(...)`

输出目录设为：
`outputs/20260311_responder_followup/fixed_school_combo_balanced_4train3test`

固定 test schools 采用最终选定方案。

**Step 3: 生成说明 Markdown**

在 `fixed_school_combo_summary.md` 中写明：
- 两个候选方案
- 最终选择理由
- self-validation / outphase 结果
- 明确这不是 external validation

---

### Task 5: 最终核验

**Files:**
- Verify only

**Step 1: 核验关键产物存在**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
base = Path('outputs/20260311_responder_followup/fixed_school_combo_balanced_4train3test')
for name in [
    'self_validation_summary.csv',
    'self_validation_fold_metrics.csv',
    'outphase_validation_summary.csv',
    'outphase_validation_fold_metrics.csv',
    'fixed_school_combo_summary.md',
]:
    p = base / name
    print(name, p.exists(), p.stat().st_size if p.exists() else None)
PY
```

Expected: 全部存在。

**Step 2: 核验术语边界**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('outputs/20260311_responder_followup/fixed_school_combo_balanced_4train3test/fixed_school_combo_summary.md').read_text(encoding='utf-8')
for pat in ['external validation', 'mean_train_auc', 'strict nested CV outer-test AUC']:
    print(pat, pat in text)
PY
```

Expected:
- 出现 `external validation` 仅用于“不是 external validation”边界说明
- 出现 `mean_train_auc`
- 出现 `strict nested CV outer-test AUC`
