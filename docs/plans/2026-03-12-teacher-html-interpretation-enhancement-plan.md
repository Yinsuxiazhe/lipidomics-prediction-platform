# Teacher HTML Interpretation Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不重跑分析的前提下，为 teacher package 的主要 HTML 页面补充更强的结构化解读，让老师看到的不只是结果表和图，还能直接读到“这页怎么理解、能说明什么、不能过度说什么”。

**Architecture:** 仅修改 `teacher_report_package` 下现有 Markdown/HTML 交付物，不碰 strict nested CV 主锚点，不改 formal package。以现有 4 个内部页面（`01/02/03/04`）为主，为每页补统一风格的解释模块：`怎么读这页`、`结构性解读`、`不能过度宣称`。随后局部重渲染 HTML，并同步 `index.html` 与 zip。

**Tech Stack:** Markdown、现有 teacher package HTML 模板、pandoc、BeautifulSoup、zip、局部 Python 脚本。

---

### Task 1: 审计当前页面的解读缺口

**Files:**
- Read: `outputs/20260311_responder_followup/teacher_report_package/01_followup_report.md`
- Read: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.md`
- Read: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md`
- Read: `outputs/20260311_responder_followup/teacher_report_package/04_fixed_school_combo_note.md`

**Step 1: 判断每页缺的不是哪张图，而是哪类解释**

重点确认：
- 是否缺“这一页的阅读顺序”；
- 是否缺“结果之间如何串起来理解”；
- 是否缺“哪些结论能说、哪些不能说”。

**Step 2: 为 4 页定义统一的新增解释模块**

每页至少补 2 个模块，优先从以下模板里选：
- `怎么读这页`
- `结构性解读`
- `最稳妥的一句话`
- `不能过度宣称的点`
- `如果老师追问，可以怎么回答`

---

### Task 2: 修改 Markdown 源，补解释层

**Files:**
- Modify: `outputs/20260311_responder_followup/teacher_report_package/01_followup_report.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/04_fixed_school_combo_note.md`

**Step 1: 01 页补 follow-up 结果怎么读**

要求：
- 明确 repeated hold-out / leave-one-school-out / out-phase 的角色分工；
- 明确为什么这些结果是“补边界”，不是“抬主结论”；
- 给出 1 段最稳妥老师口径。

**Step 2: 02 页补统一汇报结构解读**

要求：
- 明确 7 张图在整个汇报里的逻辑顺序；
- 明确为什么先讲 strict nested CV，再讲 grouped split，再讲 out-phase；
- 明确不能把内部验证写成 external validation。

**Step 3: 03 页补文献建议与本项目落地之间的映射解释**

要求：
- 强化“文献启发 → 当前可做 → 当前不能做”的结构；
- 强化 protocol 写法为何要保守落在方案编号、周期、频次；
- 增加一个“如果老师追问”的答法段落。

**Step 4: 04 页补 fixed school combo 的比较解释**

要求：
- 明确为什么 B 是主方案、A 是 sensitivity；
- 明确 A/B 并行后的真正结论不是“选出更高分”，而是“切法变化不改变边界”；
- 给出一段能直接复制给老师的简短解释。

---

### Task 3: 重渲染 HTML 并同步入口页

**Files:**
- Modify: `outputs/20260311_responder_followup/teacher_report_package/01_followup_report.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/04_fixed_school_combo_note.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/index.html`

**Step 1: 保留现有 hero/nav/style，只替换正文内容**

要求：
- 不改当前 HTML 页面的主样式；
- 用 Markdown 源重新生成 main content；
- 重新生成 TOC。

**Step 2: 保持 02 与 index 同步**

要求：
- `index.html` 继续作为统一汇报入口；
- 与 `02_combined_report.html` 同步。

---

### Task 4: 重打包并核验

**Files:**
- Verify: `outputs/20260311_responder_followup/teacher_report_package/*.html`
- Verify: `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

**Step 1: 重打 zip**

Run:
```bash
cd outputs/20260311_responder_followup && zip -rqX 20260311_responder_teacher_report_package.zip teacher_report_package
```

**Step 2: 做页面与口径核验**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
from bs4 import BeautifulSoup
pkg = Path('outputs/20260311_responder_followup/teacher_report_package')
for name in ['01_followup_report.html','02_combined_report.html','03_literature_followup_note.html','04_fixed_school_combo_note.html','index.html']:
    p = pkg / name
    soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    print(name, soup.title.get_text(' ', strip=True) if soup.title else '', soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else '')
PY

rg -n "strict nested CV outer-test AUC|AUC≈0.8|mean_train_auc|external validation|不能过度宣称|怎么读这页|结构性解读" \
  outputs/20260311_responder_followup/teacher_report_package/01_followup_report.md \
  outputs/20260311_responder_followup/teacher_report_package/02_combined_report.md \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md \
  outputs/20260311_responder_followup/teacher_report_package/04_fixed_school_combo_note.md
```

Expected: 4 个主要页面都出现新增解释模块，且科学口径不变。
