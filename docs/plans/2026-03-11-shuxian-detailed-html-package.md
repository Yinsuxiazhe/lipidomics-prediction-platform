# Shuxian Detailed HTML Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成一份面向淑贤的详细分析汇报 HTML，并把主图、主结果、小模型补充结果、关键代码与文件说明一起打包成可直接发送的压缩包。

**Architecture:** 保持 strict nested CV 主结果不变，不改动主实验逻辑；只在 `outputs/20260310_nested_cv/` 下新增面向汇报与打包的 Markdown、HTML、README、manifest 和 zip 文件。HTML 用 `ai-results-html` 渲染，压缩包用独立临时目录组装后再 zip，确保目录结构清晰、说明完整。

**Tech Stack:** Markdown, Python 3, shell zip/unzip, ai-results-html renderer, 本地 CSV/HTML/PNG/PDF/代码文件

### Task 1: 汇总需要打包的主结果、补充结果和代码文件

**Files:**
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/models/run_nested_cv.py`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/fig6-4最终.R`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/config/analysis.yaml`

**Step 1:** 确定主结果文件列表。

**Step 2:** 确定本轮补充小模型与标签审计文件列表。

**Step 3:** 确定需要给淑贤看的关键代码位置与解释。

### Task 2: 生成新的详细汇报 Markdown

**Files:**
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260311_给淑贤_详细分析汇报与打包说明.md`

**Step 1:** 直接汇报，不用问答体。

**Step 2:** 写清楚每个模型纳入变量、优化探索与结果解释。

**Step 3:** 给出正文与附件材料的推荐排布。

### Task 3: 渲染 HTML 并生成打包说明文件

**Files:**
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260311_给淑贤_详细分析汇报与打包说明.html`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260311_打包文件说明.md`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260311_打包文件清单.csv`

**Step 1:** 用 ai-results-html 渲染详细汇报页。

**Step 2:** 生成 README/说明，解释压缩包每类文件用途。

**Step 3:** 生成 manifest 清单。

### Task 4: 组装压缩包并验证

**Files:**
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_给淑贤_strict_nested_cv说明包/`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_给淑贤_strict_nested_cv说明包.zip`

**Step 1:** 建独立打包目录并拷贝文件。

**Step 2:** 压缩生成 zip。

**Step 3:** 用 `unzip -l` 校验压缩包内容。
