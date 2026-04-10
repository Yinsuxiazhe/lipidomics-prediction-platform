# Responder follow-up handoff Handoff

> 日期：2026-03-12
> 主题 slug：`responder-followup`
> 说明：这是当前 responder follow-up、out-phase 验证、正式包整理状态的会话接力文档，后续新会话默认从这里继续，不要杜撰未完成内容。

## 0. 接手前必须知道的上下文

### 已完成事项
- 已在 `config/analysis.yaml` 与 `run_pipeline.py` 中完成 follow-up stage 接入。
- 已基于本地 baseline 数据完成：group audit、self-validation、small-model follow-up。
- 在收到 out-phase 数据后，已完成 baseline → out-phase 的内部时相验证。
- 已完成对外正式包 `sequencing_company_formal_report_package`：
  - 新增 1 分钟封面说明页；
  - 加入 strict nested CV 中 AUC≈0.8 的来源解释；
  - 加入 `strict_nested_cv_key_metrics.csv`；
  - 已补 “需求方：Shuxian Zhang / 分析提供方：Chenyu Fan”。
- 已修复 F6（out-phase distribution）横坐标标签重叠问题，并同步到正式包与 teacher 包。

### 已上线 / 已部署内容
- 没有远端部署；当前交付均为本地 HTML / Markdown / ZIP 包。
- 当前可直接发送的本地对外 ZIP：
  - `outputs/20260311_responder_followup/20260312_responder_sequencing_company_formal_report_package.zip`
- 当前可直接发送的本地内部 ZIP：
  - `outputs/20260311_responder_followup/20260311_responder_teacher_report_package.zip`

### 已写入的更新日志 / 记录 ID
- 当前没有独立 updates.json / 远端发布 ID。
- 主要证据保存在本地输出目录与本 handoff 中。

### 远端部署备份时间戳
- 不适用；本轮无远端部署。

### 已生成的验收产物
- 正式包目录：`outputs/20260311_responder_followup/sequencing_company_formal_report_package`
- teacher 包目录：`outputs/20260311_responder_followup/teacher_report_package`
- strict nested CV 指标解释文件：
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/strict_nested_cv_key_metrics.csv`
- F6 修复后的正式包图件：
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/assets/07_followup_f6_outphase_distribution.png`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/assets/07_followup_f6_outphase_distribution.pdf`

## 1. 本地工作区注意事项

### 与当前任务无关的脏改动提醒
- 当前目录不是 git 仓库，无法用 git 状态区分脏改动。
- 后续新会话应尽量只围绕 `src/`、`tests/`、`outputs/20260311_responder_followup/`、`docs/plans/` 下与 follow-up 直接相关文件工作。

### 本任务应尽量只触碰
- `src/followup/*`
- `tests/followup/*`
- `outputs/20260311_responder_followup/*`
- `config/analysis.yaml`
- `run_pipeline.py`
- `CLAUDE.md`
- `docs/plans/2026-03-12-responder-followup-handoff.md`

### 当前和本任务直接相关的主要文件
- 方案文档：`docs/plans/2026-03-11-responder-new-analysis-strategy.md`
- 项目级提示：`CLAUDE.md`
- 主要输出目录：`outputs/20260311_responder_followup`
- 对外正式包：`outputs/20260311_responder_followup/sequencing_company_formal_report_package`
- 内部包：`outputs/20260311_responder_followup/teacher_report_package`
- 主要代码：
  - `src/followup/make_figures.py`
  - `src/followup/run_followup.py`
  - `src/followup/outphase_validation.py`
  - `run_pipeline.py`
  - `config/analysis.yaml`

## 2. 本轮统一工作方法

### 页面 / 功能增强原则
- 优先保持“正式主结果 / 补充稳健性证据 / 当前结论边界”三层结构。
- 对外正式包优先去内部化；内部包可以保留更多过程信息。
- 若只改单张图或单个 HTML，优先局部修复，不要无必要全量重跑。
- 更新共享图件后，记得同步到 package 目录并重新打 ZIP。

### 输出风格
- 中文汇报
- 给出可执行下一步
- 不要写空泛总结
- 对科学口径要明确写“什么能说、什么不能说”

### 尽量不要做的事
- 不要覆盖 `outputs/20260310_nested_cv` 里的正式主结果。
- 不要把 `AUC≈0.8` 写成 outer-test 或 external validation AUC。
- 不要把 repeated hold-out、leave-one-prefix-out、out-phase internal temporal validation 写成 external validation。
- 不要在对外正式包中重新引入内部措辞（如老师、内部、对接、三剑客等）。

## 3. 下一批 / 下一步计划

### 下一步文件列表
- 若继续扩展分析：
  - `src/followup/outphase_validation.py`
  - `src/followup/make_figures.py`
  - `outputs/20260311_responder_followup/outphase_validation_summary.csv`
  - `outputs/20260311_responder_followup/outphase_validation_fold_metrics.csv`
- 若继续改正式包：
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/index.html`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/00_cover_note.html`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/01_formal_report.html`
  - `outputs/20260311_responder_followup/sequencing_company_formal_report_package/README.md`

### 每个文件建议补的结构或目标
- `make_figures.py`：继续维持 publication-friendly、非拥挤标签、可复用的紧凑刻度逻辑。
- `outphase_validation.py`：如果继续增强 out-phase 分析，优先补真正有解释价值的 summary，而不是只加模型。
- 正式包 HTML：保持封面说明 → 完整报告的顺序，不要把封面页改回全文入口。

### 关键强调点
- 当前最重要的对外混淆点仍是：**0.53 vs 0.8**。任何后续改动都不能把这个边界写糊。
- 当前最重要的方法学边界仍是：**补充验证 ≠ 外部验证**。

## 4. 已知异常 / 历史坑
- 当前目录不是 git 仓库，不能依赖 git diff 做边界管理。
- F6 分布图的横坐标此前出现过重叠；现在已经通过 compact tick labels 修复，后续不要回退。
- 对外正式包在之前曾出现“目录已更新但 zip 未重打”的情况；后续每次改 package 内容后都要重新生成 zip 并核验 zip 内文件。

## 5. 执行流程

### Task A：审计
```bash
python3 - <<'PY'
from pathlib import Path
pkg = Path('outputs/20260311_responder_followup/sequencing_company_formal_report_package')
for name in ['index.html', '00_cover_note.html', '01_formal_report.html', 'README.md']:
    p = pkg / name
    print(name, p.exists(), p)
PY

pytest -q tests/followup/test_outphase_make_figures.py -q
```

### Task B：修改
- 图件修改：先改 `src/followup/make_figures.py`，再重绘，再同步 package 资产。
- 正式包文案修改：优先改 `index.html` / `00_cover_note.html` / `01_formal_report.html` / `README.md`。
- 若改外部包，要再次扫描敏感词与本地绝对路径。

### Task C：更新日志
```bash
python3 - <<'PY'
from pathlib import Path
for p in Path('outputs/20260311_responder_followup').glob('*.csv'):
    print(p.name, p.stat().st_size)
PY
```

### Task D：部署
```bash
# 当前无远端部署；如只是本地交付，重打 zip 即可
cd outputs/20260311_responder_followup && \
zip -rqX 20260312_responder_sequencing_company_formal_report_package.zip sequencing_company_formal_report_package && \
zip -rqX 20260311_responder_teacher_report_package.zip teacher_report_package
```

### Task E：验收
```bash
python3 - <<'PY'
from pathlib import Path
from bs4 import BeautifulSoup
pkg = Path('outputs/20260311_responder_followup/sequencing_company_formal_report_package')
for name in ['index.html', '00_cover_note.html', '01_formal_report.html']:
    p = pkg / name
    soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    print(name, soup.title.get_text(' ', strip=True) if soup.title else '', soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else '')
PY
```

## 6. 新会话建议开场 prompt

```text
请先阅读 `CLAUDE.md` 和 `docs/plans/2026-03-12-responder-followup-handoff.md`，然后继续当前 responder follow-up 与正式包维护任务。优先沿用当前科学口径：strict nested CV outer-test AUC 约 0.50–0.54，AUC≈0.8 仅指 mean_train_auc；repeated hold-out、leave-one-prefix-out、out-phase internal temporal validation 都不能写成 external validation。若只改单张图或单个 HTML，请局部修复、同步 package、重新打 zip，不要无必要全量重跑。
```

## 7. 成功标准
- 写清当前已完成结果与下一步范围
- 保留 strict nested CV 与 follow-up 的口径边界
- 修改 package 后同步 zip
- 修改共享图件后同步 teacher / formal 两个 package
- 给下一会话一条可直接复制的开场 prompt
