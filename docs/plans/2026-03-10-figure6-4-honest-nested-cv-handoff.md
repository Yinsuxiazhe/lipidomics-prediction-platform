# Figure 6-4 Honest Nested CV Handoff

## 0. 当前状态

当前项目的 strict nested CV 主结果、正式说明包、代码审计和 ROC 图件整理工作均已完成一轮，适合在新会话继续接力。

### 已完成事项
1. 已完成 strict nested CV 主结果管线与 Figure 6-4 主图生成。
   - 主图 PNG：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
   - 主图 PDF：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
2. 已导出 strict nested CV 的关键结果表。
   - `performance_summary.csv`
   - `fold_metrics.csv`
   - `feature_stability_summary.csv`
   - `feature_frequency.csv`
   - `roc_curve_points.csv`
3. 已完成“诚实口径”中文说明文档与单页发送版说明。
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.md`
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`
4. 已将原“给淑贤说明包”重构为**正式版说明包**，去除过程性沟通记录、对接话术和非正式说明。
   - 文件夹：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包`
   - 压缩包：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包.zip`
5. 已新增正式版总说明与方法定位说明。
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.md`
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.html`
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_strict_nested_cv结果定位说明.md`
6. 已完成**代码完整性审计**。
   - 审计 Markdown：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_正式说明包代码完整性审计.md`
   - 审计 HTML：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_正式说明包代码完整性审计.html`
7. 已生成训练 AUC 与泛化差距相关补充图。
   - 条形图、dumbbell 图、气泡图、组合图均在：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距`
8. 已为 **5 个主模型** 分别生成 publication-style 单图 ROC（Training ROC + Outer-test ROC + AUC values）。
   - `20260311_ROC_clinical_baseline_publication.png/pdf`
   - `20260311_ROC_expanded_clinical_publication.png/pdf`
   - `20260311_ROC_lipid_only_publication.png/pdf`
   - `20260311_ROC_clinical_lipid_fusion_publication.png/pdf`
   - `20260311_ROC_expanded_fusion_publication.png/pdf`
9. 已生成 5 图总览拼图，专门用于视觉排版检查。
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png`
10. 已额外生成“训练结果最强模型”的简洁单图 ROC。
   - `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_BestTrainingModel_English_ROC_singlepanel_publication.png`
11. 已将正式说明 HTML 重构为 **aging-analysis / tutorial 风格**页面，并补入补充图、快捷按钮、固定目录与顶部元信息。
   - HTML：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.html`
   - 当前页面已包含：主图、训练 AUC 与泛化差距组合图、ROC contact sheet、5 张 publication-style 单图 ROC。
12. 已继续微调正式说明页可读性。
   - 顶部前 3 张大图已缩小，避免正文必须整体缩放后才可阅读。
   - 顶部信息已调整为两行样式：`更新日期：2026-03-11` / `分析者：Chenyu Fan ｜ 需求方：Shuxian Zhang`。
13. 已重新打包最新 zip，并验证 zip 内 HTML 与本地 HTML 同步。

### 当前关键结果
当前 strict nested CV 口径下：
- Clinical baseline：0.530
- Expanded clinical：0.501
- Lipid-only：0.534
- Clinical + lipid fusion：0.536
- Expanded fusion：0.526

### 当前最重要的结论边界
1. 主结果必须继续沿用 strict nested CV 口径。
2. 当前可以支持的正式结论是：**存在一定预测信号，但泛化增益有限**。
3. 训练 ROC 可以作为“模型在训练阶段已学到较强模式”的补充展示，但**不能单独包装成正式性能声明**。
4. 正式说明包中的 `03_关键代码与配置/` 当前应定位为“关键实现证据”，**不是**完整复现包。

### 验收 / 校验证据
1. 测试证据（历史主工程）：
   - `python3 -m pytest tests -q`
   - 结果：`14 passed in 2.41s`
2. 正式说明包清理检查：
   - 对新包执行 `rg '给淑贤|给老师|handoff|发给|问答|Q&A|session_report|内部'`，结果为空。
   - 对新包执行 `rg 'file:///'`，结果为空。
3. 代码完整性验证（负向证据，已写入审计）：
   - 运行包内 `run_pipeline.py --dry-run`，报错：`ModuleNotFoundError: No module named 'src.data'`
   - 运行包内 `fig6-4最终.R`，同样因缺失本地模块而失败。
4. 图件视觉检查：
   - 已查看 `20260311_ROC_publication_contact_sheet.png`
   - 已查看 `20260311_ROC_clinical_lipid_fusion_publication.png`
   - 当前未见明显标题、legend 与曲线重叠。
5. 文件存在性校验：
   - 已用 `ls -l` 确认新的正式说明包 zip、代码审计文档、publication ROC 图和 contact sheet 均已实际落盘。
6. 额外视觉/样式验证（本轮新增）：
   - 已将正式说明 HTML 改为 aging-analysis 风格，并做顶部截图检查。
   - 已确认无 `file:///` 泄漏。
   - 已验证前 3 张大图缩小后仍可正常显示。
   - 已验证顶部元信息两行样式已写入 HTML / Markdown / zip。

## 1. 本地工作区注意事项

### 当前会话明确修改过的关键文件（下一会话可以继续碰）
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/README_正式版.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_strict_nested_cv正式说明.html`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_strict_nested_cv结果定位说明.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_正式说明包代码完整性审计.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/plot_train_auc_gap.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/plot_best_training_model_roc_english.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/plot_best_training_model_roc_publication_singlepanel.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/plot_all_models_publication_roc.py`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/00_正式说明/20260311_文件清单_正式版.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包.zip`

### 重要输出产物（谨慎覆盖）
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包.zip`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_baseline_publication.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_clinical_publication.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_lipid_only_publication.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_lipid_fusion_publication.png`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_fusion_publication.png`

### 工作区边界提醒
- 该目录**不是 git 仓库**，无法用 `git status` 判断脏改动。
- 下一会话请以 `docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md` 中列出的文件和 `outputs/20260310_nested_cv/` 下的相关产物为边界，不要扩散修改范围。

## 2. 当前轮统一模板 / 方法

### 已固定的方法学口径
- 训练、特征筛选、标准化、调参：全部在 strict nested CV 的训练折内完成。
- 绘图脚本只负责读取严格输出并可视化，不在图件阶段重新建模。
- 所有正式结论优先以 outer-test / strict nested CV 结果为准。

### 图件输出风格
- publication-style 单图 ROC：白底、简洁坐标轴、对角参考线、图外 legend。
- legend 统一下置，避免文字压住 ROC 曲线。
- 标题避免使用机械化词语（如 “English”），直接写自然模型标题。
- 若是训练表现强调图，也必须同时保留 outer-test ROC 作为参照。

### 代码目录定位
- `03_关键代码与配置/` 当前统一定位为“关键实现证据”。
- 不要误写为“完整复现代码包”。

## 3. 下一步计划

建议下一会话优先从以下方向中选 1 个继续：

### 方向 A：做 A–E 多面板 Supplement figure
- 目标：把 5 张 publication-style 单图 ROC 整合成一张标准多面板补充图。
- 输入：`05_补充图_训练AUC与泛化差距/20260311_ROC_*_publication.png`
- 适合场景：正式投稿附件、补充材料统一排版。

### 方向 B：继续做期刊极简版 ROC 图
- 目标：去掉标题、缩短 legend、统一版式，让单图更接近期刊补充图原稿。
- 适合场景：supplementary figure / figure legend 分离提交。

### 方向 C：升级正式说明包为最小可运行复现包
- 目标：让 `03_关键代码与配置/` 从“关键实现证据”升级成“最小可运行复现包”。
- 关键缺口：`src.data` / `src.io` / `src.features` / `src.preprocess` 模块缺失，且 `analysis.yaml` 仍为绝对路径。

### 方向 D：继续优化严格模型
- 目标：在 strict nested CV 口径下，继续探索是否能提升泛化能力。
- 建议方向：稳定特征精简、更强特征筛选约束、控制过拟合、做 top-k / 模型家族系统比较。

### 方向 E：转成论文口径 Results / Discussion
- 目标：把当前 strict nested CV 结果与正式说明包内容进一步改写成适合论文正文和补充材料的表述。

### 方向 F：优先回到标签定义 / 分组策略审查
- 目标：重新确认 responder / non-responder 的原始定义、时间窗、阈值和灰区样本处理，判断是否需要 **重新分组或剔除边界样本**。
- 当前建议：**需要优先做**，但不是机械地“重新分组”，而是先回到临床定义核查，再决定是否重标记。
- 推荐动作：
  1. 追溯原始结局定义（response / noresponse 的判定标准、随访时间点、阈值）；
  2. 统计 responder 与 non-responder 在关键临床变量和候选脂质上的差异；
  3. 标记灰区样本（接近阈值、缺失随访、定义不稳定者），评估三种口径：原始二分类 / 更严格二分类 / 排除灰区；
  4. 仅在临床上讲得通的前提下，再进入新一轮 strict nested CV。
- 判断标准：若更严格分组后 AUC 与训练—测试差值同时改善，说明当前标签噪声/异质性很可能是主要瓶颈。

### 当前建议排序（非常重要）
1. **第一优先级：标签与分组审查。** 目前最值得先做的不是继续堆模型，而是区分 responder / non-responder 的定义是否足够干净。
2. **第二优先级：做差异分析而不是盲目调参。** 先看两组在关键临床变量、脂质特征、缺失模式、批次/队列来源上到底差在哪。
3. **第三优先级：压缩模型复杂度。** 当前结果已提示小模型/稀疏模型更稳，应优先做 top-k、稳定特征约束、限制特征数，而不是继续扩展变量。
4. **第四优先级：做更接近外部验证的内部验证。** 如果暂时找不到完全匹配的外部脂质组数据集，就先做更严格的 pseudo-external 设计。

### 如何优化模型性能（当前最推荐的 5 条）
1. **先降标签噪声**：核查 response 定义、重做更严格二分类、必要时排除灰区样本。
2. **先降异质性**：如果样本来自不同治疗方案、病程阶段、批次或采血窗口，优先做分层或限制分析人群。
3. **先降特征复杂度**：优先尝试 ultra-sparse lipid、compact fusion、稳定特征 top-k，而不是 expanded 类模型。
4. **把临床锚点和脂质增量分开评估**：先确认 clinical baseline 的稳定性，再看脂质是否在严格分组后提供额外增量。
5. **不要把优化目标只盯在 AUC 提升**：同时看训练—测试差值、跨折稳定性、特征重现率和校准情况。

### 外部验证不足时的替代路线
1. **最理想**：找到同病种、同结局定义、相同或高度重叠脂质平台的数据集做真正外部验证。
2. **如果没有完全匹配脂质组数据**：
   - 做 **pseudo-external validation**：按中心/批次/入组时间/采血批次做留一组验证；
   - 做 **subset validation**：只验证共享的临床变量模型，或验证少数可映射/可定量复测的脂质特征；
   - 做 **targeted assay replication**：把当前最稳定的少数脂质做定向检测，再看 responder / non-responder 是否复现方向一致。
3. **因此当前不应被“没有现成外部脂质数据集”卡死。** 更现实的下一步是先做更严格的内部-外部近似验证，再为后续小面板定向复测创造条件。

## 4. 已知异常 / 历史坑

### 坑 1：Rscript 直接运行会报编码相关错误
原因：环境变量 `SCRCPY_SERVER_PATH` 含异常编码字符，普通 `Rscript` 会在启动阶段报错。

### 正确运行方式
```bash
cd '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型'
python3 run_pipeline.py --stage experiments --config config/analysis.yaml
env -u SCRCPY_SERVER_PATH Rscript --vanilla 'fig6-4最终.R'
```

### 坑 2：项目不是 git 仓库
不要依赖 `git status` 判断边界；以 handoff 中列出的文件清单为准。

### 坑 3：正式说明包里的代码目录不能独立运行
- 包内 `03_关键代码与配置/run_pipeline.py` 直接运行会报：`ModuleNotFoundError: No module named 'src.data'`。
- 包内 `03_关键代码与配置/fig6-4最终.R` 也会因为内部调用 `run_pipeline.py` 而失败。
- 如果用户下一轮要求“完整复现包”，必须先补齐缺失模块并处理绝对路径配置。

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

### 快速检查关键主结果
```bash
ls -l \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf'
```

### 检查正式说明包关键图件与审计文件
```bash
ls -l \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包.zip' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/04_方法学说明/20260311_正式说明包代码完整性审计.md' \
  '/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/packages/20260311_strict_nested_cv正式说明包/05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png'
```

## 6. 新会话建议开场 prompt

请先阅读 `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`，然后继续当前任务。当前 strict nested CV 正式说明页已经重构为 aging-analysis / tutorial 风格，补充图已嵌入，顶部前 3 张大图已缩小，顶部元信息为两行样式（更新日期 / 分析者 / 需求方），最新 zip 也已同步更新。请优先查看 `00_正式说明/20260311_strict_nested_cv正式说明.html`、`04_方法学说明/20260311_正式说明包代码完整性审计.md`、以及 `05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png`。方法学上继续沿用“诚实口径优先”：不要把训练 ROC 单独包装成正式性能声明。下一步优先级建议改为：1）先做 responder / non-responder 的原始定义、时间窗、阈值与灰区样本审查，判断是否需要更严格分组；2）在更干净标签口径下继续 strict nested CV，并优先尝试小模型/稀疏模型；3）若做验证，优先做 pseudo-external validation（按时间/批次/中心/平台留一组）或少数稳定脂质的 targeted replication，而不是等待完全匹配的外部脂质组数据集。
