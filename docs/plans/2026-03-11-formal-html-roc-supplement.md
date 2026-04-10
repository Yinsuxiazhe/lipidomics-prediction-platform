# Formal HTML ROC Supplement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 publication-style ROC 单图与训练 AUC / 泛化差距补充图纳入正式说明页，并用“诚实口径优先”的方式补充解释，避免把训练 ROC 写成正式性能声明。

**Architecture:** 以 `/00_正式说明/20260311_strict_nested_cv正式说明.md` 作为单一内容源，在其中新增“训练 ROC 与泛化差距补充图”章节、单图 gallery 和解释文字，再用 Pandoc 重新渲染同名 HTML。只改正式说明页及其实现计划，不改主结果表、补充图源文件或 strict nested CV 输出。

**Tech Stack:** Markdown, Pandoc HTML rendering, local PNG/PDF assets, shell backup/verification

### Task 1: 明确插图策略与插入位置

**Files:**
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.md`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/`

**Step 1:** 选择纳入 HTML 的图件组合：组合图 + contact sheet + 5 张单图。

**Step 2:** 确定新增章节放在主结果解释之后、稳定特征线索之前。

**Step 3:** 明确解释边界：训练 ROC 仅作“已学到模式但泛化有限”的辅助证据，不作为正式性能声明。

### Task 2: 更新 Markdown 正式说明源文件

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.md`

**Step 1:** 先备份现有 Markdown 与 HTML。

**Step 2:** 插入新增章节、图注、单图 gallery 和解释文字。

**Step 3:** 顺带把“补充材料排布建议/优先打开文件”中与新增图件相关的条目补全。

### Task 3: 重新渲染并验证 HTML

**Files:**
- Modify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.html`

**Step 1:** 用 Pandoc 从更新后的 Markdown 重生成 HTML。

**Step 2:** 检查 HTML 中是否包含新增图件相对路径与解释文字。

**Step 3:** 进行一次本地视觉抽查，确认页面中图件引用存在、核心表述仍保持“诚实口径优先”。
