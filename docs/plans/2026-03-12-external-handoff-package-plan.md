# External Handoff Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不重跑分析的前提下，把当前 teacher package 中更强的解释层转换成对外可交接、公司式正式口吻的新 HTML/ZIP 交付包。

**Architecture:** 复用现有 `teacher_report_package` 的页面结构与增强后的解释框架，但新建独立 `external_handoff_formal_package` 目录，统一替换内部口吻、老师称呼与内部说明，保留严格科学边界。新包不覆盖既有 teacher/internal 包，也不覆盖现有 sequencing company formal package。

**Tech Stack:** Markdown、HTML、Python 文本替换/模板复用、BeautifulSoup、zip。

---

### Task 1: 审计现有 package 并确定新包骨架

**Files:**
- Read: `outputs/20260311_responder_followup/teacher_report_package/*`
- Read: `outputs/20260311_responder_followup/sequencing_company_formal_report_package/*`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/`

**Step 1:** 确认新包沿用哪些页面（建议 01/02/03/04 + index + README + assets）。

**Step 2:** 明确必须去掉的内部措辞（如“老师您好”“内部”“老师追问”“blocked”等）。

### Task 2: 生成外部正式 package 内容

**Files:**
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/README.md`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/index.html`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/01_followup_formal_report.md`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/01_followup_formal_report.html`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/02_combined_formal_report.md`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/02_combined_formal_report.html`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/03_school_split_protocol_note.md`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/03_school_split_protocol_note.html`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/04_fixed_school_combo_note.md`
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/04_fixed_school_combo_note.html`

**Step 1:** 基于 teacher package 文本生成对外版 Markdown，保留解释结构，统一改成正式、中性、交接式口吻。

**Step 2:** 保留科学边界：strict nested CV outer-test AUC≈0.50–0.54；AUC≈0.8 仅指 mean_train_auc；所有 follow-up 均不得写成 external validation。

**Step 3:** 复用现有 HTML 样式，渲染新 HTML 页面并同步 `index.html` 到总页入口。

### Task 3: 复制必要资产并打包

**Files:**
- Create: `outputs/20260311_responder_followup/external_handoff_formal_package/assets/`
- Create: `outputs/20260311_responder_followup/20260312_responder_external_handoff_formal_package.zip`

**Step 1:** 复制新包页面实际引用到的图片/PDF/CSV/说明文件到新包或建立一致的相对路径。

**Step 2:** 打 zip，不影响既有 zip。

### Task 4: 验收

**Files:**
- Verify: `outputs/20260311_responder_followup/external_handoff_formal_package/*`
- Verify: `outputs/20260311_responder_followup/20260312_responder_external_handoff_formal_package.zip`

**Step 1:** 核验 HTML 标题、入口页、关键新章节存在。

**Step 2:** 扫描敏感词和口径错误，确保无“老师/内部/external validation误写”等问题。

**Step 3:** 确认 zip 内含主要 HTML 文件。
