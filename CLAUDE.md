# 项目级 CLAUDE.md

## 项目背景
- 项目主题：儿童运动干预脂质组学 responder / non-responder 预测与 follow-up 验证。
- 当前工作主线已经从“继续堆模型追更高训练 AUC”转为：
  1. **strict nested CV 正式主结果维护**；
  2. **follow-up 稳健性验证与小模型比较**；
  3. **out-phase（干预后 / 出组）内部时相验证**；
  4. **面向老师/内部沟通包与面向测序公司的对外正式包整理**。

## 截至 2026-03-12 的当前状态（后续对话默认承接这里）

### 1. 正式主结果锚点
- 正式 strict nested CV 主结果目录：`outputs/20260310_nested_cv`
- **该目录视为只读主锚点**，不要覆盖旧图、旧表、旧 zip。
- 当前必须保留的科学口径：
  - strict nested CV 的 **outer-test mean AUC 约 0.50–0.54**；
  - 用户记得的 **AUC≈0.8** 实际对应 strict nested CV 中的 **mean_train_auc**；
  - **不能**把 0.8 写成 outer-test AUC，也不能写成外部验证结果。
- 对应来源文件：
  - `outputs/20260310_nested_cv/performance_summary.csv`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/strict_nested_cv_key_metrics.csv`

### 2. follow-up 第一阶段已完成内容
当前 follow-up 结果目录：`outputs/20260311_responder_followup`

本轮已经基于本地现有数据完成：
- group audit（当前 responder 分组证据链审计）
- repeated hold-out / leave-one-prefix-out 自我验证
- 小模型 follow-up 比较
- out-phase 内部时相验证（在收到 out-phase 数据后补齐）
- teacher/internal 包与 sequencing company 对外正式包

关键结果文件包括：
- `outputs/20260311_responder_followup/group_definition_audit.md`
- `outputs/20260311_responder_followup/baseline_balance_summary.csv`
- `outputs/20260311_responder_followup/self_validation_summary.csv`
- `outputs/20260311_responder_followup/self_validation_fold_metrics.csv`
- `outputs/20260311_responder_followup/small_model_followup_comparison.csv`
- `outputs/20260311_responder_followup/outphase_validation_summary.csv`
- `outputs/20260311_responder_followup/outphase_validation_fold_metrics.csv`
- `outputs/20260311_responder_followup/followup_summary.md`

### 3. out-phase 数据已接入
当前本地已知数据文件：
- baseline / enroll：
  - `287_enroll_data_clean.csv`
  - `281_merge_lipids_enroll.csv`
  - `281_new_grouped.csv`
- out-phase：
  - `287_outroll_data_clean.csv`
  - `281_merge_lipids_out.csv`

因此，之前“出组数据缺失”的阻塞在本地已部分解除；当前已经完成 **baseline → out-phase 的内部时相验证**，但仍不能把它表述为 external validation。

### 4. 对外正式包现状
对外正式包目录：`outputs/20260311_responder_followup/sequencing_company_formal_report_package`

当前结构：
- `index.html`：默认入口，已改成 **1 分钟封面说明页**
- `00_cover_note.html`：同封面说明页
- `01_formal_report.html`：完整正式报告
- `README.md`
- `strict_nested_cv_key_metrics.csv`
- `assets/`：正式引用图件

当前对外包已完成的关键修订：
- 已纳入 strict nested CV 主结果
- 已单独解释 “AUC≈0.8 的来源”
- 已加入 `strict_nested_cv_key_metrics.csv`
- 已补“需求方 / 分析提供方”开头信息
- 已去内部化，不应出现内部沟通词汇

当前对外包中固定展示身份：
- **需求方：Shuxian Zhang**
- **分析提供方：Chenyu Fan**

当前对外 ZIP：
- `outputs/20260311_responder_followup/20260312_responder_sequencing_company_formal_report_package.zip`

### 5. 内部 teacher 包现状
内部沟通包目录：`outputs/20260311_responder_followup/teacher_report_package`

对应 ZIP：
- `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

### 6. 最新图形修复（很重要，后续不要回退）
- 已修复图：
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/assets/07_followup_f6_outphase_distribution.png`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/assets/07_followup_f6_outphase_distribution.pdf`
- 修复原因：原图横坐标标签过长，发生重叠。
- 当前修复已经写入代码：`src/followup/make_figures.py`
- 当前修复方式：
  - 分布图 x 轴使用更短的 compact tick labels；
  - 画布加宽；
  - tick label 角度、字号、padding 已微调。
- 已新增测试：`tests/followup/test_outphase_make_figures.py`
- 以后如果重绘 F6 / F3，**不要把长括号说明重新塞回 x 轴刻度**。

## 当前必须坚持的科学口径
- **正式主结果**：strict nested CV outer-test performance。
- **补充稳健性证据**：repeated hold-out、leave-one-prefix-out、小模型比较、out-phase internal temporal validation。
- **不能写成 external validation 的内容**：
  - repeated hold-out
  - leave-one-prefix-out
  - post-intervention / out-phase within-dataset temporal validation
- 如果用户继续问 “为什么我记得有 AUC≈0.8”：
  - 直接解释那是 `mean_train_auc`，不是 outer-test AUC。

## 对外正式包的文本边界
如果继续修改 `sequencing_company_formal_report_package`，要保持：
- 不出现这些词：
  - `老师`
  - `淑贤`
  - `三剑客`
  - `teacher`
  - `blocked`
  - `blocked_items`
  - `followup_plan_alignment`
  - `/Users/`
  - `file:///`
  - `对接`
  - `内部`
- 对外正式页应优先维持：
  - `index.html` / `00_cover_note.html` 先统一口径
  - `01_formal_report.html` 给完整结果

## 继续工作时优先查看的文件
- 方案母版：`docs/plans/2026-03-11-responder-new-analysis-strategy.md`
- 当前接力文档：`docs/plans/2026-03-12-responder-followup-handoff.md`
- 主要代码：
  - `src/followup/make_figures.py`
  - `src/followup/run_followup.py`
  - `src/followup/outphase_validation.py`
  - `run_pipeline.py`
  - `config/analysis.yaml`

## 后续对话的默认接续策略
- 如果用户说“继续这个项目 / 接着做”，默认从：
  - `outputs/20260311_responder_followup`
  - `sequencing_company_formal_report_package`
  - `teacher_report_package`
  - `src/followup/*`
  这些位置继续。
- 如果只是改某一张图或某个 HTML，不要全量重跑整个分析；优先做 **局部重绘 / 局部同步 / 重新打包**。
- 如果更新了 `assets/` 下的共享图件，记得同步到相关 package 并重新生成对应 zip。
- 当前目录 **不是 git 仓库**；不要假设可以用 git branch / commit / worktree。
