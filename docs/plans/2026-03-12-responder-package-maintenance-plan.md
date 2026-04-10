# Responder Package Maintenance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于 2026-03-12 最新对接建议与当前接力状态，完成 responder follow-up 内部包的最小范围维护：清理 teacher package 中残留的绝对路径/目录泄露、确认 formal package 无需改口径、并重打 zip。

**Architecture:** 本轮不重跑 strict nested CV 或 follow-up 建模，不改 `outputs/20260310_nested_cv` 主锚点。直接复用已经生成的 Markdown/HTML/CSV 资产，对 teacher package 做局部文本与链接修复；formal package 仅做敏感词和口径审计，除非发现问题，否则保持不动。

**Tech Stack:** Python 3、现有 Markdown/HTML 产物、`ai-results-html` 渲染脚本、zip、BeautifulSoup、ripgrep。

---

### Task 1: 审计本轮最小修改范围

**Files:**
- Read: `CLAUDE.md`
- Read: `docs/plans/2026-03-12-responder-followup-handoff.md`
- Read: `docs/plans/2026-03-12-responder-literature-followup-plan.md`
- Read: `20260312_建议/20260312_新的对接建议.txt`
- Verify: `outputs/20260311_responder_followup/teacher_report_package/*.html`
- Verify: `outputs/20260311_responder_followup/sequencing_company_formal_report_package/*.html`

**Step 1: 扫描 teacher package 中的绝对路径与目录泄露**

Run:
```bash
rg -n "file://|/Users/" outputs/20260311_responder_followup/teacher_report_package -g '*.html' -g '*.md'
```

Expected: 找到 footer note 与少量 Markdown 中的绝对路径残留，确认本轮只需局部修复。

**Step 2: 审计 formal package 是否需要改动**

Run:
```bash
rg -n "老师|淑贤|三剑客|teacher|blocked|blocked_items|followup_plan_alignment|/Users/|file:///|对接|内部" \
  outputs/20260311_responder_followup/sequencing_company_formal_report_package -g '!assets/**'
```

Expected: 无命中；formal package 保持不动。

**Step 3: 检查现有 teacher zip 是否已落后**

Run:
```bash
python3 - <<'PY'
import zipfile
zf = zipfile.ZipFile('outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip')
for name in [
    'teacher_report_package/03_literature_followup_note.html',
    'teacher_report_package/prefix_group_holdout_summary.csv',
]:
    print(name, name in zf.namelist())
PY
```

Expected: 至少一项缺失，说明必须重打 zip。

### Task 2: 修复 teacher package 的绝对路径与便携性问题

**Files:**
- Modify: `outputs/20260311_responder_followup/followup_summary.md`
- Modify: `outputs/20260311_responder_followup/group_definition_audit.md`
- Modify: `outputs/20260311_responder_followup/followup_summary_shareable.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/01_followup_report.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/followup_summary.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/group_definition_audit.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/01_followup_report.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/index.html`

**Step 1: 把 Markdown 中的绝对路径改成相对路径或描述性表述**

要求：
- `strict nested CV` 主锚点仅写成 `outputs/20260310_nested_cv`；
- teacher package 内部引用尽量使用相对路径，例如 `group_definition_audit.md`；
- 文献建议与会议纪要来源仅保留相对路径 `docs/...`。

**Step 2: 更新 HTML 中的 footer note**

要求：
- 去掉“当前目录：/Users/...”；
- 改为通用交付说明，例如“生成日期：2026-03-12 | 本页为 teacher package 本地交付页”。

**Step 3: 保持科学口径不变**

检查并确保以下表述不被改坏：
- strict nested CV outer-test AUC 约 0.50-0.54；
- AUC≈0.8 仅对应 `mean_train_auc`；
- repeated hold-out、leave-one-prefix-out、out-phase internal temporal validation 不能写成 external validation。

### Task 3: 重建 teacher zip 并做交付验证

**Files:**
- Verify: `outputs/20260311_responder_followup/teacher_report_package/index.html`
- Verify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.html`
- Verify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`
- Verify: `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

**Step 1: 重新打包**

Run:
```bash
cd outputs/20260311_responder_followup && zip -rqX 20260311_responder_teacher_report_package.zip teacher_report_package
```

Expected: zip 时间戳晚于本轮修复时间。

**Step 2: 验证 zip 内容**

Run:
```bash
python3 - <<'PY'
import zipfile
zf = zipfile.ZipFile('outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip')
for name in [
    'teacher_report_package/03_literature_followup_note.html',
    'teacher_report_package/prefix_group_holdout_summary.csv',
    'teacher_report_package/02_combined_report.html',
    'teacher_report_package/README.md',
]:
    print(name, name in zf.namelist())
PY
```

Expected: 全部为 `True`。

**Step 3: 验证页面标题、链接与绝对路径清理**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
from bs4 import BeautifulSoup
pkg = Path('outputs/20260311_responder_followup/teacher_report_package')
for name in ['index.html', '02_combined_report.html', '03_literature_followup_note.html']:
    p = pkg / name
    soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    print(name, soup.title.get_text(' ', strip=True) if soup.title else '', soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else '')
PY

rg -n "file://|/Users/" outputs/20260311_responder_followup/teacher_report_package -g '*.html' -g '*.md'
```

Expected: 标题正常，且 teacher package 不再包含绝对路径或 `file://`。

**Step 4: Commit**

跳过；当前目录不是 git 仓库。
