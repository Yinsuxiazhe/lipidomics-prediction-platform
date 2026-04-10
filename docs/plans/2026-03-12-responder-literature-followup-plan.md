# Responder Literature Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于 2026-03-12 新对接建议与两篇参考文献，补一份可直接给内部沟通使用的 literature follow-up 分析说明，并把当前 teacher 包同步到最新口径，不无必要重跑模型。

**Architecture:** 本轮不改 strict nested CV 主锚点，不全量重跑 follow-up pipeline。直接复用已有 `self_validation`、`outphase_validation`、`group_definition_audit` 结果，新增一个“文献建议 → 当前数据可落地点 → 下一步阻塞”的局部分析说明，并只更新 teacher package 与相关 markdown/csv/zip。对外 formal package 保持不动，除非审计发现必须修复的口径问题。

**Tech Stack:** Python 3、pandas、现有 CSV/Markdown 产物、ai-results-html 渲染脚本、zip。

---

### Task 1: 审核建议与参考文献，固化本轮边界

**Files:**
- Read: `CLAUDE.md`
- Read: `docs/plans/2026-03-12-responder-followup-handoff.md`
- Read: `20260312_建议/20260312_新的对接建议.txt`
- Read: `20260312_建议/mmc2_港大徐爱民教授团队的另外一篇文章.md`
- Read: `20260312_建议/nature medicine_nature medicine的一篇，他们这个看起来没有分测试和验证.md`

**Step 1: 提炼文献与对接建议中的可执行点**

记录三条结论：
1. 是否支持“按学校/社区分组训练-测试”；
2. 当前项目里与其最接近的现有分析是什么；
3. 哪些缺口阻止我们把现有 prefix hold-out 直接写成 school/community validation。

**Step 2: 用已有输出核对当前最接近的分析对象**

Run:
```bash
python3 - <<'PY'
import pandas as pd
print(pd.read_csv('outputs/20260311_responder_followup/self_validation_summary.csv')[['model_label','validation_scheme','mean_auc']])
print(pd.read_csv('outputs/20260311_responder_followup/outphase_validation_summary.csv')[['model_label','validation_scheme','mean_auc']])
print(pd.read_csv('outputs/20260311_responder_followup/group_definition_audit.csv').query("record_type == 'id_prefix_distribution'"))
PY
```

Expected: 能看到 leave-one-prefix-out、outphase_leave_one_prefix_out 与 A-G prefix 分布，确认本轮无需重新训练即可先完成 literature-aligned explanation。

**Step 3: 结论写入本轮实施说明草稿**

结论要求：继续坚持 strict nested CV outer-test AUC≈0.50–0.54 为正式主结果；AUC≈0.8 仅指 mean_train_auc；prefix hold-out 仅是 grouped proxy，不能升级成外部验证。

**Step 4: Commit**

跳过；当前目录不是 git 仓库。

### Task 2: 生成 literature-aligned 内部分析资产

**Files:**
- Create: `outputs/20260311_responder_followup/prefix_group_holdout_summary.csv`
- Create: `outputs/20260311_responder_followup/literature_followup_note.md`
- Create: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md`
- Create: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`

**Step 1: 先生成汇总 CSV**

Run a Python snippet or reusable helper to merge:
- `group_definition_audit.csv` 中 A-G prefix 大小与 response rate
- `self_validation_fold_metrics.csv` 中 `leave_one_prefix_out` split AUC
- `outphase_validation_fold_metrics.csv` 中 `outphase_leave_one_prefix_out` split AUC

输出列至少包括：
- `model_label`
- `prefix`
- `baseline_n`
- `response_n`
- `noresponse_n`
- `response_rate`
- `self_auc`
- `outphase_auc`
- `self_train_auc`
- `outphase_train_auc`

**Step 2: 写 literature follow-up markdown**

Markdown 必须包含：
1. 新建议摘要；
2. 两篇参考文献的可借鉴点；
3. 当前数据最接近的现有设计（leave-one-prefix-out / out-phase prefix hold-out）；
4. 明确不能说成 external validation；
5. 下一步优先级与阻塞（尤其是 prefix↔school/community 映射与 endpoint source）。

**Step 3: 渲染 teacher package HTML**

Run:
```bash
python3 /Users/angus/.claude/skills/ai-results-html/scripts/render_review_html.py \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html \
  --title "Responder 文献跟进与下一步分析计划" \
  --subtitle "2026-03-12 新建议 / grouped split 可行性 / 当前阻塞" \
  --badge "内部 follow-up" \
  --meta-pill "strict nested CV 仍为主结果" \
  --meta-pill "prefix hold-out 不是 external validation" \
  --nav-link "统一汇报包|02_combined_report.html" \
  --toolbar-link "prefix 汇总 CSV|../prefix_group_holdout_summary.csv" \
  --footer-link "teacher 包 README|README.md"
```

Expected: 生成一个新的 teacher package HTML 页面，可直接点开查看。

**Step 4: Commit**

跳过；当前目录不是 git 仓库。

### Task 3: 局部更新 teacher package 与阻塞说明

**Files:**
- Modify: `outputs/20260311_responder_followup/blocked_items.md`
- Modify: `outputs/20260311_responder_followup/followup_plan_alignment.md`
- Modify: `outputs/20260311_responder_followup/followup_summary.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/blocked_items.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/followup_plan_alignment.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/README.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.md`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.html`
- Modify: `outputs/20260311_responder_followup/teacher_report_package/index.html`

**Step 1: 在阻塞项与 alignment 文本中加入新缺口**

新增一条：缺少 prefix↔school/community 映射表，因此当前 leave-one-prefix-out 只能作为 grouped proxy，不能直接升级成“不同学校训练/测试”。

**Step 2: 在统一汇报包中加入新 section 和新链接**

新增一节，说明：
- Xu 团队论文是 discovery vs validation community；
- Nature Medicine 论文是 repeated CV；
- 我们当前最接近的是 prefix hold-out；
- 下一步应先补元数据映射，再决定是否做 school/community split headline。

**Step 3: 重渲染或局部同步 HTML**

如果只改 markdown 且已有稳定 HTML 渲染链，优先重渲染 `02_combined_report.html`，再复制到 `index.html`。

**Step 4: 重新打 teacher zip**

Run:
```bash
cd outputs/20260311_responder_followup && zip -rqX 20260311_responder_teacher_report_package.zip teacher_report_package
```

Expected: 新 zip 时间戳晚于修改前，且包含新增 `03_literature_followup_note.html`。

**Step 5: Commit**

跳过；当前目录不是 git 仓库。

### Task 4: 验证局部更新没有破坏当前口径

**Files:**
- Verify: `outputs/20260311_responder_followup/teacher_report_package/README.md`
- Verify: `outputs/20260311_responder_followup/teacher_report_package/02_combined_report.html`
- Verify: `outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.html`
- Verify: `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

**Step 1: 文字边界检查**

Run:
```bash
rg -n "external validation|AUC≈0.8|mean_train_auc|school|community|prefix" \
  outputs/20260311_responder_followup/teacher_report_package/README.md \
  outputs/20260311_responder_followup/teacher_report_package/02_combined_report.md \
  outputs/20260311_responder_followup/teacher_report_package/03_literature_followup_note.md
```

Expected: 能看到对 `AUC≈0.8 = mean_train_auc` 的边界、对 prefix/grouped proxy 的谨慎表述、以及“不能写成 external validation”的提醒。

**Step 2: HTML 标题和链接检查**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
from bs4 import BeautifulSoup
for name in ['02_combined_report.html','03_literature_followup_note.html','index.html']:
    p = Path('outputs/20260311_responder_followup/teacher_report_package') / name
    soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    print(name, soup.title.get_text(' ', strip=True) if soup.title else '', soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else '')
PY
```

Expected: 页面标题正常，`index.html` 与 `02_combined_report.html` 同步。

**Step 3: zip 内容检查**

Run:
```bash
python3 - <<'PY'
import zipfile
zf = zipfile.ZipFile('outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip')
for name in ['teacher_report_package/03_literature_followup_note.html','teacher_report_package/02_combined_report.html','teacher_report_package/README.md']:
    print(name, name in zf.namelist())
PY
```

Expected: 三个文件都在 zip 内。

**Step 4: Commit**

跳过；当前目录不是 git 仓库。
