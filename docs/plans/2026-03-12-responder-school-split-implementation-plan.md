# Responder School Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于 `运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx` 中 `运动强度分组_401人` sheet 的 `ID -> school -> intensity` 映射，补做真正的学校分组 grouped validation，并把结果以最小改动方式接入当前 responder follow-up 内部输出与 teacher package。

**Architecture:** 不改 strict nested CV 主锚点，不重跑全部主分析；在现有 `self_validation` / `outphase_validation` 流程中增加可配置的 grouped split 解析层，使 `pseudo_external.group_by` 既支持既有 `id_prefix`，也支持新的 `school`。新增映射导出、学校级汇总 CSV、学校 split 说明 Markdown；对外 formal package 默认不动，仅更新内部结果与 teacher package。

**Tech Stack:** Python 3、pandas、openpyxl、pytest、现有 follow-up pipeline、zip、ai-results-html 渲染脚本。

---

### Task 1: 固化学校映射与最小设计边界

**Files:**
- Create: `docs/plans/2026-03-12-responder-school-split-implementation-plan.md`
- Read: `运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx`
- Read: `src/followup/self_validation.py`
- Read: `src/followup/outphase_validation.py`
- Read: `outputs/20260311_responder_followup/literature_followup_note.md`

**Step 1: 明确新 grouped split 的唯一可信来源**

Run:
```bash
python3 - <<'PY'
import pandas as pd
p='运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx'
df=pd.read_excel(p, sheet_name='运动强度分组_401人')
print(df.columns.tolist())
print(df.head().to_dict(orient='records')[:3])
PY
```

Expected: 明确只使用 `school / ID / intensity` 三列作为映射来源。

**Step 2: 确认 prefix 不等于 school，避免错误改名**

Run:
```bash
python3 - <<'PY'
import pandas as pd
mapping=pd.read_excel('运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx', sheet_name='运动强度分组_401人')
group=pd.read_csv('281_new_grouped.csv', dtype={'ID':str})
merged=group.merge(mapping, on='ID', how='left')
merged['prefix']=merged['ID'].astype(str).str[0]
print(pd.crosstab(merged['prefix'], merged['school']))
PY
```

Expected: 看到 `C` 同时对应 `本部 + 六里屯`，因此旧 `leave-one-prefix-out` 不能改名成学校 split。

**Step 3: 明确本轮最小交付**

交付仅包含：
- `id_school_intensity_mapping.csv`
- 学校级 self/out-phase grouped holdout CSV
- 学校 split 说明 Markdown
- teacher package 同步与 zip 重打

不做：
- strict nested CV 重跑
- formal package 改口径
- 新图全量重绘（除非必须）

---

### Task 2: 先写失败测试，定义学校 split 行为

**Files:**
- Create: `tests/followup/test_school_split.py`
- Modify: `tests/followup/test_self_validation.py`
- Modify: `tests/followup/test_outphase_validation.py`

**Step 1: 写映射读取测试**

测试内容：
- 能从 Excel sheet 读取 `ID/school/intensity`
- 会把 ID 规范成字符串
- 能导出去重后的 mapping frame

**Step 2: 写 self-validation 学校 split 测试**

测试内容：
- `pseudo_external.group_by: school` 时新增 `leave_one_school_out`
- `holdout_group` 为学校名
- 汇总表包含 `leave_one_school_out`
- 映射 CSV 和学校汇总 CSV 被导出

**Step 3: 写 out-phase 学校 split 测试**

测试内容：
- `pseudo_external.group_by: school` 时新增 `outphase_leave_one_school_out`
- `train_phase=baseline / test_phase=outphase` 不变
- 报告文案明确这是 school grouped internal validation，不是 external validation

**Step 4: 跑测试确认失败**

Run:
```bash
pytest -q tests/followup/test_school_split.py tests/followup/test_self_validation.py tests/followup/test_outphase_validation.py
```

Expected: 因缺少学校 split 实现与新导出文件而失败。

---

### Task 3: 实现学校映射与 grouped split 解析层

**Files:**
- Create: `src/followup/school_split.py`
- Modify: `src/followup/self_validation.py`
- Modify: `src/followup/outphase_validation.py`

**Step 1: 新增学校映射工具模块**

实现最小函数：
```python
def load_school_mapping(mapping_path, sheet_name='运动强度分组_401人') -> pd.DataFrame: ...
def attach_school_mapping(frame, mapping_frame) -> pd.DataFrame: ...
def resolve_group_series(frame, group_by, mapping_path=None, mapping_sheet_name='运动强度分组_401人') -> tuple[pd.Series, dict]: ...
```

要求：
- `group_by='id_prefix'` 继续返回前缀
- `group_by='school'` 时基于 Excel 映射返回学校名
- 返回 metadata 供后续导出和文案使用

**Step 2: self-validation 改成可配置 grouped split**

要求：
- 保留既有 `leave_one_prefix_out`
- 新增 `leave_one_school_out`
- 通过统一 helper 实现 leave-one-group-out
- 若 `group_by='school'`，输出：
  - `id_school_intensity_mapping.csv`
  - `school_group_holdout_summary.csv`

**Step 3: outphase-validation 改成可配置 grouped split**

要求：
- 保留既有 `outphase_leave_one_prefix_out`
- 新增 `outphase_leave_one_school_out`
- baseline / out-phase 的学校分组都使用同一 ID 映射
- 报告中加入“school grouped split 已接入，但仍属内部 grouped validation / internal temporal validation”语句

---

### Task 4: 让测试转绿并补 pipeline 兼容

**Files:**
- Modify: `tests/test_run_pipeline.py`
- Modify: `config/analysis.yaml`
- Modify: `src/followup/run_followup.py`

**Step 1: 补 followup toy pipeline 对 `group_by: school` 的兼容测试**

测试内容：
- config 中允许：
  - `pseudo_external.group_by: school`
  - `pseudo_external.mapping_path`
  - `pseudo_external.mapping_sheet_name`
- 运行后生成学校相关输出

**Step 2: 更新 run_followup 汇总文案**

要求：
- 如果学校 split 已启用，`followup_summary.md` 中新增一段：
  - 真实学校 grouped split 已完成
  - 旧 prefix split 仍保留为弱 proxy，不可回溯改名
- `blocked_items.md` 删除“缺少 prefix↔school/community 映射表”这一阻塞，改成 endpoint_source / 心血管表型仍阻塞

**Step 3: 运行相关测试**

Run:
```bash
pytest -q tests/followup/test_school_split.py tests/followup/test_self_validation.py tests/followup/test_outphase_validation.py tests/test_run_pipeline.py
```

Expected: 全部通过。

---

### Task 5: 在真实数据上最小重跑学校 split 结果

**Files:**
- Output: `outputs/20260311_responder_followup/id_school_intensity_mapping.csv`
- Output: `outputs/20260311_responder_followup/school_group_holdout_summary.csv`
- Output: `outputs/20260311_responder_followup/self_validation_summary.csv`
- Output: `outputs/20260311_responder_followup/self_validation_fold_metrics.csv`
- Output: `outputs/20260311_responder_followup/outphase_validation_summary.csv`
- Output: `outputs/20260311_responder_followup/outphase_validation_fold_metrics.csv`
- Output: `outputs/20260311_responder_followup/followup_summary.md`

**Step 1: 在当前 follow-up 配置中接入 school split**

把 `config/analysis.yaml` 的 followup grouped split 改为：
```yaml
pseudo_external:
  enabled: true
  group_by: school
  mapping_path: /Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx
  mapping_sheet_name: 运动强度分组_401人
```

**Step 2: 仅重跑 followup stage**

Run:
```bash
python3 run_pipeline.py --stage followup --config config/analysis.yaml
```

Expected: 只更新 `outputs/20260311_responder_followup/`，不触碰 `outputs/20260310_nested_cv/`。

**Step 3: 核验学校结果是否生成**

Run:
```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path
base=Path('outputs/20260311_responder_followup')
for name in ['id_school_intensity_mapping.csv','school_group_holdout_summary.csv','self_validation_summary.csv','outphase_validation_summary.csv']:
    p=base/name
    print(name, p.exists(), p.stat().st_size if p.exists() else None)
if (base/'school_group_holdout_summary.csv').exists():
    print(pd.read_csv(base/'school_group_holdout_summary.csv').head(20).to_string())
PY
```

Expected: 看到学校级留一结果与学校/强度映射文件。

---

### Task 6: 更新内部说明、teacher package 与 zip

**Files:**
- Modify: `outputs/20260311_responder_followup/literature_followup_note.md`
- Modify: `outputs/20260311_responder_followup/blocked_items.md`
- Modify: `outputs/20260311_responder_followup/followup_summary.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/followup_summary.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/blocked_items.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/README.md`
- Create/Sync: `outputs/20260311_responder_followup/teacher_report_package/id_school_intensity_mapping.csv`
- Create/Sync: `outputs/20260311_responder_followup/teacher_report_package/school_group_holdout_summary.csv`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/index.html`
- Output: `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

**Step 1: 改文案边界**

要求：
- 文献 note 改为“学校映射现已找到，因此真实 school grouped split 已可实施并已补跑”
- 明确 `strict nested CV outer-test AUC ≈ 0.50–0.54` 仍是正式主结果
- 明确 `leave_one_school_out` / `outphase_leave_one_school_out` 也不能写成 `external validation`
- 对运动 protocol 写法补一句：主文可先写干预方案编号，强度细节放补充或答审

**Step 2: 用 ai-results-html 重渲 teacher HTML**

Run:
```bash
python3 /Users/angus/.claude/skills/ai-results-html/scripts/render_review_html.py \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html \
  --title "文献跟进：学校 split 与运动 protocol" \
  --toolbar-link "学校汇总 CSV|school_group_holdout_summary.csv" \
  --toolbar-link "学校映射 CSV|id_school_intensity_mapping.csv" \
  --toolbar-link "阻塞项|blocked_items.md"
```

**Step 3: 同步 teacher package 并重打 zip**

Run:
```bash
cd outputs/20260311_responder_followup && zip -rqX 20260311_responder_teacher_report_package.zip teacher_report_package
```

**Step 4: 做最终核验**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
import pandas as pd
import zipfile
base=Path('outputs/20260311_responder_followup')
for p in [
    base/'id_school_intensity_mapping.csv',
    base/'school_group_holdout_summary.csv',
    base/'teacher_report_package'/'03_literature_followup_note.html',
    base/'20260311_responder_teacher_report_package.zip',
]:
    print(p, p.exists())
if (base/'school_group_holdout_summary.csv').exists():
    df=pd.read_csv(base/'school_group_holdout_summary.csv')
    print(df[['model_label','holdout_group']].head(10).to_string(index=False))
with zipfile.ZipFile(base/'20260311_responder_teacher_report_package.zip') as zf:
    for name in [
        'teacher_report_package/id_school_intensity_mapping.csv',
        'teacher_report_package/school_group_holdout_summary.csv',
        'teacher_report_package/03_literature_followup_note.html',
    ]:
        print(name, name in zf.namelist())
PY
```

Expected: 文件存在、zip 包含新增学校 split 产物、teacher note 已更新。

**Step 5: Commit**

跳过；当前目录不是 git 仓库。
