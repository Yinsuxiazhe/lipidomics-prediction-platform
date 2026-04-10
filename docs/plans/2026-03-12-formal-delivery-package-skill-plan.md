# Formal Delivery Package Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 沉淀一个可复用的 `formal-delivery-package` skill，用于把现有分析结果整理成正式材料包，统一正式措辞，纳入分析代码与分析数据，并完成 ZIP 打包与交付前验收。

**Architecture:** 新建独立 skill，而不是硬改现有 handoff / HTML skill。SKILL.md 负责触发条件、核心流程与边界；`references/` 负责正式措辞与包结构清单；`scripts/` 提供通用 package 审计脚本，负责 forbidden terms、必备文件、HTML title/h1 与绝对路径检查。

**Tech Stack:** Markdown、YAML frontmatter、Python CLI、zip、grep-like 文本扫描。

---

### Task 1: 审查现有能力并确定 skill 边界

**Files:**
- Read: `/Users/angus/.codex/skills/.system/skill-creator/SKILL.md`
- Read: `/Users/angus/.codex/skills/.system/skill-creator/scripts/init_skill.py`
- Read: `tmp/build_neutral_formal_package_20260312.py`
- Read: `outputs/20260311_responder_followup/responder_formal_delivery_package/README.md`

**Step 1:** 确认现有 skill 中没有可直接覆盖“正式包 + 代码/数据 + ZIP 验收”的完整方案。

**Step 2:** 提炼需要沉淀进 skill 的通用规则：口吻、角色标注、文件纳入、局部修补优先、ZIP 验收。

### Task 2: 初始化并编写新 skill

**Files:**
- Create/Modify: `/Users/angus/.codex/skills/formal-delivery-package/SKILL.md`
- Create/Modify: `/Users/angus/.codex/skills/formal-delivery-package/agents/openai.yaml`
- Create/Modify: `/Users/angus/.codex/skills/formal-delivery-package/references/tone-and-structure.md`
- Create/Modify: `/Users/angus/.codex/skills/formal-delivery-package/references/package-checklist.md`

**Step 1:** 写清触发条件与不适用边界。

**Step 2:** 写清标准目录结构、README 要素、角色标注与正式措辞。

**Step 3:** 写清代码/数据纳入规则与“局部修改优先”的原则。

### Task 3: 增加通用验收脚本并验证

**Files:**
- Create/Modify: `/Users/angus/.codex/skills/formal-delivery-package/scripts/audit_formal_package.py`

**Step 1:** 支持扫描 required files、forbidden phrases、绝对路径泄露、HTML title/h1。

**Step 2:** 用 `quick_validate.py` 检查 skill 结构合法。

**Step 3:** 用脚本对当前 `responder_formal_delivery_package` 做一次本地演示性审计。
