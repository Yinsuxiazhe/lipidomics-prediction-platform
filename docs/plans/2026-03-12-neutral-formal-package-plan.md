# Neutral Formal Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成一份不强调“对外/交接”措辞、但结构正式完整的中性正式报告包，并把需求方、分析提供方、分析代码、分析数据一起纳入。

**Architecture:** 复用当前已增强的正式说明页面与 HTML 样式，但新建独立 `responder_formal_delivery_package` 目录；统一去掉“对外正式交接页/外部正式交接包”等自我说明文案，补充 package-level README、analysis_code/、analysis_data/ 与项目角色说明。

**Tech Stack:** Markdown、HTML、Python 脚本、BeautifulSoup、zip、文件复制。

---

### Task 1: 确定新包结构与纳入文件

**Files:**
- Read: `outputs/20260311_responder_followup/external_handoff_formal_package/*`
- Read: `config/analysis.yaml`
- Read: `run_pipeline.py`
- Read: `src/followup/*.py`
- Read: `281_merge_lipids_enroll.csv`
- Read: `281_merge_lipids_out.csv`
- Read: `287_enroll_data_clean.csv`
- Read: `287_outroll_data_clean.csv`
- Read: `281_new_grouped.csv`

**Step 1:** 使用更中性的目录/zip 命名。

**Step 2:** 确定 `analysis_code/` 与 `analysis_data/` 中要打包的最小完整文件集。

### Task 2: 生成中性正式 package

**Files:**
- Create: `outputs/20260311_responder_followup/responder_formal_delivery_package/`
- Create: `outputs/20260311_responder_followup/responder_formal_delivery_package/analysis_code/`
- Create: `outputs/20260311_responder_followup/responder_formal_delivery_package/analysis_data/`
- Modify/Create: `tmp/build_neutral_formal_package_20260312.py`

**Step 1:** 生成 4 个中性标题的 Markdown/HTML 页面与 `index.html`。

**Step 2:** 在 README 中明确需求方、分析提供方、页面入口、代码目录、数据目录。

**Step 3:** 把分析代码与分析数据复制到新包中。

### Task 3: 打包与验收

**Files:**
- Create: `outputs/20260311_responder_followup/20260312_responder_formal_delivery_package.zip`

**Step 1:** 打 zip。

**Step 2:** 验收页面标题、敏感词、README、analysis_code、analysis_data、zip 内容。
