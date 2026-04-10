# Figure 6-4 Honest Nested CV Handoff

## 0. 当前状态

本轮已完成 7 个任务，并已暂停，适合在新会话继续接力。

### 本轮已完成事项
1. 新建并落地了 Figure 6-4 诚实口径实施计划：
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv.md`
2. 按 TDD 先写失败测试，再补实现：
   - 新增约束报表层必须导出 `fold_metrics.csv` 和 `feature_stability_summary.csv`
3. 更新 Python 报表导出逻辑：
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/reports/make_tables.py`
4. 重写了 `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/fig6-4最终.R`：
   - 不再在 R 中做全样本插补/筛选/建模
   - 改为直接消费 strict nested CV 输出
5. 已重新运行真实 experiments stage，生成 strict nested CV 结果
6. 已成功生成新的“诚实口径” Figure 6-4：
   - PNG：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
   - PDF：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
7. 已写好给老师/淑贤的中文说明文档：
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`

### 本轮关键结果
当前 strict nested CV 口径下：
- Clinical baseline：0.530
- Expanded clinical：0.501
- Lipid-only：0.534
- Clinical + lipid fusion：0.536
- Expanded fusion：0.526

### 验收证据
- 全量测试通过：`python3 -m pytest tests -q`
  - 结果：`14 passed in 2.41s`
- 新图已成功导出：
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
- 新增诚实口径中间产物：
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv`
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`

### 本轮追加更新（发送 / 发文口径）
8. 已将中文说明文档整理为**可直接发送/汇报的单页版 Markdown**：
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.md`
9. 已用 `ai-results-html` 渲染生成**可转发 HTML 汇报页**：
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`
10. 已完成 HTML 结构级检查：
   - `nav` / `hero` / `sidebar-toc` / `mobile-toc` / `footer` / `copy-example-btn` 均存在
   - 已确认页面内嵌 Honest Figure 6-4 PNG 链接
11. 已补充“发文章如何表述”的口径判断：
   - **strict nested CV 结果应作为论文主结果 / 主图 / 最终性能声明**
   - 旧版更高分结果**最多**作为 exploratory / development-stage internal validation 放入补充材料或 Discussion/Limitations，不建议作为主结果

### 新增验收证据（本轮追加）
- 新增可发送 Markdown：
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.md`
- 新增 HTML 汇报页：
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`
- HTML 结构检查结果：
  - `class="nav": OK`
  - `class="hero": OK`
  - `sidebar-toc: OK`
  - `mobile-toc: OK`
  - `class="footer": OK`
  - `copy-example-btn: OK`
  - `Figure6-4_Honest_NestedCV.png: OK`
- 说明：曾尝试用 Playwright 做浏览器级点击验证，但受本机 Chrome 现有会话启动问题影响未完成；当前已完成静态结构校验。

## 1. 本地工作区注意事项

### 当前会话明确修改过的文件（下一会话可以继续碰）
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/reports/make_tables.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/reports/test_make_tables.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/tests/test_run_pipeline.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/fig6-4最终.R`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`

### 输出产物（谨慎覆盖）
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_frequency.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/roc_curve_points.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`

### 工作区边界提醒
- 该目录**不是 git 仓库**，无法用 `git status` 判断脏改动。
- 下一会话请以“上面列出的已修改文件 + outputs/20260310_nested_cv 下的本任务产物”为工作边界，不要扩散修改范围。

## 2. 当前轮统一模板 / 方法

### 已固定的方法学口径
- 训练、特征筛选、标准化、调参：全部在 strict nested CV 的训练折内完成
- 绘图脚本只负责读取严格输出并可视化，不重新建模
- 新 Figure 6-4 的设计为：
  - A：Clinical baseline ROC
  - B：Added lipidomics ROC
  - C：Fusion comparison ROC
  - D：Fold-level train/test AUC gap
  - E：Expanded fusion 稳定特征选择率

### 输出风格
- 优先“诚实口径”而非“更高分数”
- 汇报语气偏解释性、避免纯代码术语
- 说明文档已按“老师版 / 淑贤版”分层表达

## 3. 下一步计划

建议下一会话从下面 3 个方向里选 1 个继续：

### 方向 A：把说明文档转成可发送版本
- 目标：生成 Word / HTML / 微信可发版
- 输入：
  - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`
- 适合场景：要马上发给老师或组会汇报

### 方向 B：做“旧图 vs 新图”对照页
- 目标：做一页专门解释为什么旧图更高但不更可靠
- 可以产出：单页 PNG / HTML / Markdown 汇报页
- 适合场景：组会答辩、老师追问方法口径

### 方向 C：继续优化严格模型
- 目标：在 strict nested CV 口径下，继续探索是否能提升泛化能力
- 建议子方向：
  - 稳定特征精简
  - 更强的特征筛选约束
  - 控制过拟合
  - 做 top-k / 模型家族的系统比较

### 方向 D：转成论文口径
- 目标：把当前 strict nested CV 结果改写成适合文章的 Results / Discussion / Limitations 表述
- 核心约束：
  - 主结果必须沿用 strict nested CV
  - 旧版高分结果若保留，只能作为 exploratory / development-stage internal validation
  - 不要把旧版作为最终性能声明
- 适合场景：准备投稿、写摘要、写讨论部分、应对审稿人方法学质疑

## 4. 已知异常 / 历史坑

### 坑 1：Rscript 直接运行会报编码相关错误
原因：环境变量 `SCRCPY_SERVER_PATH` 含异常编码字符，普通 `Rscript` 会在启动阶段报错。

### 正确运行方式
必须这样运行：

```bash
cd '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型'
python3 run_pipeline.py --stage experiments --config config/analysis.yaml
env -u SCRCPY_SERVER_PATH Rscript --vanilla 'fig6-4最终.R'
```

### 坑 2：`fig6-4最终.R` 原文件一开始是只读权限
本轮已经处理过一次（加写权限后重写）。
如果下轮再次遇到覆盖失败，先看权限：

```bash
ls -l 'fig6-4最终.R'
chmod u+w 'fig6-4最终.R'
```

### 坑 3：这个项目不是 git 仓库
不要依赖 `git status` 做范围判断；用 handoff 里列出的文件清单作为边界。

## 5. 执行流程

### 重新跑严格结果
```bash
cd '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型'
python3 run_pipeline.py --stage experiments --config config/analysis.yaml
```

### 重新生成诚实口径 Figure 6-4
```bash
env -u SCRCPY_SERVER_PATH Rscript --vanilla 'fig6-4最终.R'
```

### 验证测试
```bash
python3 -m pytest tests -q
```

### 快速检查关键产物
```bash
ls -l \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf'
```

## 6. 新会话建议开场 prompt

请先阅读 `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`，然后继续当前任务。当前已完成 strict nested CV 版 Figure 6-4、中文说明文档，以及可直接发送的单页 HTML 汇报页：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`。请继续沿用“诚实口径优先”的方法学，不要回退到全样本先筛特征再验证的旧流程，也不要扩散修改范围。下一步优先做二选一：1）把当前结果改写成适合论文 Results / Discussion / Limitations 的正式表述；或 2）在 strict nested CV 口径下，基于稳定特征和更小模型继续探索能否提升泛化表现。若讨论旧版高分结果，请仅把它作为 exploratory / development-stage internal validation 或局限性讨论，不要把它当作主结果。若需要重跑图，请使用 `env -u SCRCPY_SERVER_PATH Rscript --vanilla 'fig6-4最终.R'`。
