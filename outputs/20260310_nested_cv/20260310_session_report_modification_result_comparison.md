# strict nested CV 本次会话报告 / 修改对比清单 / 运算结果比对

> 本页用于把**上一轮已经完成的 strict nested CV 主结果**与**本轮补充完成的小模型改进与标签/队列审计**合并成一个可转发 HTML 汇报页。

> 核心边界：本页所有主结果继续沿用 **strict nested CV / 诚实口径优先**；本轮没有回退到“全样本先筛特征再验证”的旧流程，也没有把 exploratory 小模型升级成主结果。

## 一页摘要

- **上一轮已经完成、并且现在作为主结果使用的那一版结果**：strict nested CV 版 Figure 6-4、中文说明文档、可直接发送的单页 HTML 汇报页均已生成。
- **上一轮主结果的核心结论**：当前主结果中 `Clinical + lipid fusion` 数值最高，mean AUC = **0.536**，但只比 `Clinical baseline`（**0.530**）与 `Lipid-only`（**0.534**）略高。
- **本次新增的改进方向**：不是继续堆模型，而是在 strict nested CV 下做**预定义小模型压缩**和**结构级标签/队列审计**。
- **本次新增的最好补充结果**：`ultra_sparse_lipid` mean AUC = **0.540**，mean gap = **0.155**；`compact_fusion` mean AUC = **0.538**，mean gap = **0.224**。
- **当前最稳妥的总判断**：存在一定预测信号，但泛化增益仍有限；现阶段最值得强调的是**结果更可信、模型更简、边界更清楚**，而不是分数显著升高。

## 先前运行已完成的核心产物

### 1. 主图与主结果

### 1.1 这里说的“上一轮主结果”具体是指什么

这里的“上一轮主结果”不是泛指以前所有分析，而是特指**上一轮已经完成并定稿的 strict nested CV 主分析产物**，也就是下面这一批文件：

- `Figure6-4_Honest_NestedCV.png`
- `Figure6-4_Honest_NestedCV.pdf`
- `20260310_figure6-4_honest_sendable_report.md`
- `20260310_figure6-4_honest_sendable_report.html`
- `performance_summary.csv`
- `fold_metrics.csv`
- `feature_stability_summary.csv`

换句话说，本页里凡是写“上一轮主结果”“当前主结果”，说的都是**这一版已经完成、已经出图、也已经有发送版 HTML 的 strict nested CV 结果**，不是更早那套宽松口径的旧高分结果。

<div style="text-align:center; margin: 1.25rem 0 1.75rem;">
  <img src="file:///Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png" alt="strict nested CV 版 Figure 6-4" style="width:60%; min-width:320px; max-width:720px; height:auto; border-radius:12px; box-shadow:0 10px 30px rgba(15,23,42,0.12);" />
</div>

> 图像已按当前页面重新缩小显示；这里只是调整展示尺寸，不改变原始 PNG 文件本身。

上一轮已经完成并固定为主结果口径的文件：

- Honest Figure PNG：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.png`
- Honest Figure PDF：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/Figure6-4_Honest_NestedCV.pdf`
- 中文说明文档：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/给老师和淑贤的_Figure6-4诚实口径说明_2026-03-10.md`
- 已有发送版 HTML：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`

### 2. 先前主模型结果（strict nested CV）

| 主结果地位 | 模型 | mean AUC | mean train AUC | train-test gap | 解释 |
|---|---|---:|---:|---:|---|
| 主结果第 1 | Clinical + lipid fusion | 0.5364 | 0.8055 | 0.2691 | 当前数值最高，但领先幅度很小 |
| 主结果第 2 | Lipid-only | 0.5338 | 0.7895 | 0.2556 | 脂质组有信号，但过拟合风险明显 |
| 主结果第 3 | Clinical baseline | 0.5297 | 0.6064 | 0.0767 | 最稳但最弱的基线模型 |
| 主结果第 4 | Expanded fusion | 0.5258 | 0.8496 | 0.3239 | 复杂度更高，但泛化未改善 |
| 主结果第 5 | Expanded clinical | 0.5011 | 0.7437 | 0.2426 | 扩展临床变量没有带来稳定收益 |

### 2.1 各主模型实际纳入了什么变量

> 这里需要先说明一个 strict nested CV 的关键点：**不存在一个“全局唯一、一次性固定”的入模变量列表**。因为每个外层 fold 都是在各自训练折内完成筛选、相关性剪枝和调参，所以真正严谨的写法应该是：固定写清楚“模型的变量来源与规则”，再补充“每折大致入模数量”和“跨折最稳定出现的变量”。

| 模型 | 变量来源 | 每折实际入模数量 | 变量展开说明 |
|---|---|---:|---|
| Clinical baseline | `287_enroll_data_predict.csv` | 固定 5 个 | 5 个变量是固定的：`age_enroll`、`bmi_z_enroll`、`SFT`、`Gender`、`BMI` |
| Lipid-only | `281_merge_lipids_enroll.csv` | 28–30 个 | 从约 1600 个脂质特征里，在训练折内做单变量排序 + 相关性剪枝后留下的脂质；最稳定的包括 `PA(28:0)`、`PC(38:7e)`、`Cer(d19:1_24:1)`、`Hex1Cer(d18:0_20:4)`、`Hex2Cer(d18:2_16:0)`、`PC(26:3e)`、`PC(32:1_22:4)`、`FA(20:4)`、`FA(22:5)` |
| Clinical + lipid fusion | `287_enroll_data_predict.csv` + `281_merge_lipids_enroll.csv` | 33–35 个 | 固定的 5 个临床变量（`age_enroll`、`bmi_z_enroll`、`SFT`、`Gender`、`BMI`）+ 每折再选出的 28–30 个脂质；因此它本质上是“5 个固定临床锚点 + 训练折筛出的脂质子集” |
| Expanded clinical | `287_enroll_data_clean.csv` | 19–27 个 | 从约 400+ 扩展临床变量中，在训练折内依次做缺失率过滤、单变量排序、相关性剪枝后留下；稳定示例包括 `whole_blood_LYMPH_count`、`AV_sub`、`HAD`、`HARI`、`HRI`、`Inbody_122_BFM._of_Left_Leg`、`Inbody_207_Growth_Score`、`SFT`、`SWE`、`FENO_CV.` |
| Expanded fusion | `287_enroll_data_clean.csv` + `281_merge_lipids_enroll.csv` | 49–57 个 | 扩展临床筛选后变量 + 训练折内脂质筛选后变量；稳定示例包括 `whole_blood_LYMPH_count`、`AV_sub`、`HAD`、`HARI`、`HRI`，以及 `PA(28:0)`、`PC(38:7e)`、`Cer(d19:1_24:1)`、`Hex1Cer(d18:0_20:4)`、`Hex2Cer(d18:2_16:0)` |

### 2.2 为什么这里不能给出一个“唯一固定的大名单”

因为一旦把所有 281 例样本放在一起先筛出一个固定变量表，再去汇报性能，就会重新回到我们现在明确避免的旧流程。因此本页采用的更诚实写法是：

1. 先讲**每个模型来自哪张表、规则是什么**；
2. 再讲**每折通常会留下多少变量**；
3. 最后讲**哪些变量跨 fold 最稳定**。

这种写法虽然不如“贴一个全局最终名单”看起来简单，但方法学上更稳。

### 3. 先前主结果最值得保留的解释

1. Figure 6-4 现在问的是“模型在未参与训练与调参的外层测试折中还能剩下多少性能”，而不是开发期内部拟合有多好看。
2. `fusion_elastic_net` 虽然是主结果中数值最高模型，但它对 `clinical_slim_logistic` 和 `lipid_elastic_net` 的增益幅度都很小。
3. `expanded_fusion` 的训练集 AUC 很高，但外层测试 AUC 没有同步提高，说明加变量数并没有自然换来更好泛化。
4. 因此主结果更适合表述为：**在严格内部验证下观察到有限但可检测的预测信号**。

## 本次运行的改进方式（本轮新增）

### 本次没有做什么

- 没有回退到旧版宽松评估流程
- 没有新增随机森林 / XGBoost / 更深搜索空间
- 没有修改 Figure 6-4 主图口径
- 没有扩散到 handoff 以外的大范围源码重构

### 本次实际做了什么

#### 改进方式 1：继续压缩模型复杂度，而不是继续加变量

本轮在**同一 strict nested CV 框架**下，重跑了两个预定义小模型：

| 本次补充模型 | 继承自 | 具体设置 | 设计目的 |
|---|---|---|---|
| `ultra_sparse_lipid` | `lipid_elastic_net` | `lipid_top_k=5`，`clinical_top_k=5`，`correlation_threshold=0.80` | 看能否用约 5 个脂质换取更低过拟合 |
| `compact_fusion` | `fusion_elastic_net` | `lipid_top_k=15`，`clinical_top_k=10`，`correlation_threshold=0.90` | 看能否在保留融合信息时压缩复杂度 |

#### 这两个补充模型实际纳入了什么变量

| 本次补充模型 | 每折变量数 | 变量构成展开 |
|---|---:|---|
| `ultra_sparse_lipid` | 4–5 个 | 完全来自脂质组表；不是固定同 5 个脂质，但最常出现的是 `LPC(16:0)`、`PC(32:1_22:4)`、`Hex2Cer(d18:2_16:0)`、`PC(38:7e)`、`Cer(d19:1_24:1)` |
| `compact_fusion` | 18–20 个 | 固定 5 个临床变量：`age_enroll`、`bmi_z_enroll`、`SFT`、`Gender`、`BMI`；再加上约 13–15 个脂质，较稳定的有 `Hex1Cer(d18:0_20:4)`、`PC(32:1_22:4)`、`PC(38:7e)`、`Cer(d19:1_24:1)`、`FA(22:5)`、`Hex2Cer(d18:2_16:0)`、`LPC(16:0)`、`PC(26:3e)` |

也就是说，本轮“改进方式”并不是用了新的算法名称去包装，而是把变量结构讲得更清楚：

- `ultra_sparse_lipid` = **极小脂质子集模型**
- `compact_fusion` = **5 个固定临床锚点 + 一个更小的脂质子集**

#### 改进方式 2：优先看稳定特征，而不是继续追求更多候选变量

本轮新增导出了两个小模型各自的：

- `feature_frequency.csv`
- `feature_stability_summary.csv`
- `fold_metrics.csv`
- `roc_curve_points.csv`
- `run_result.json`

重点不是“又筛出多少变量”，而是看：

- 哪些变量在外层 fold 中重复出现
- 压缩后 train-test gap 是否下降
- 提升是否来自更稳的泛化，而不是更高的训练集拟合

#### 改进方式 3：开始做标签 / 队列审计，而不是只盯着模型分数

本轮额外完成了结构级审计，确认：

- 287 → 281 的分析队列收敛路径是可追溯的
- 当前标签文件本地只有 `ID` 与 `Group`
- 本地现有表格里**没有直接可核验 response/noresponse 原始定义**的随访窗口或终点原值字段

这意味着：

> 现在已经可以做**结构级标签审计**，但还不能声称已经完成“结局真值口径审计”。

## 修改对比清单

| 对比项 | 本次会话前 | 本次会话后 | 影响 |
|---|---|---|---|
| Figure 6-4 主图 | 已完成 strict nested CV 版本 | 保持不变 | 主结果口径稳定，不受本轮补充分析影响 |
| 主结果说明文档 | 已存在 | 保持不变 | 继续作为对老师/淑贤的主说明材料 |
| 主模型结果 CSV | 已存在 | 保持不变 | 不覆盖既有主结果 |
| 小模型补充结果 | 无独立目录 | 新增 `predefined_small_models/ultra_sparse_lipid` 与 `predefined_small_models/compact_fusion` | 形成“更小更稳”的补充证据 |
| 结果对照汇总 | 只有主结果表 | 新增三模型对照表 `20260310_predefined_small_model_comparison.csv` | 更容易汇报“压缩复杂度是否值得” |
| 标签/队列审计 | 仅在讨论中提及 | 新增 `20260310_small_model_label_audit.md/csv` | 让 Limitations 与后续数据清理更有证据 |
| 源码 | 已有 strict nested CV 实现 | **本轮未改源码** | 本轮是窄范围补充运行与结果整理，不是重构 |

### 本次会话新增文件

- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/performance_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/feature_frequency.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/fold_metrics.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/feature_stability_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/roc_curve_points.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/run_result.json`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/performance_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/feature_frequency.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/fold_metrics.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/feature_stability_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/roc_curve_points.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/run_result.json`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_predefined_small_model_comparison.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_session_report_modification_result_comparison.md`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_session_report_modification_result_comparison.html`

## 运算结果比对

### 主结果 vs 本次补充小模型

| 结果类型 | 模型 | mean AUC | mean train AUC | mean gap | 平均特征数 | 当前解释 |
|---|---|---:|---:|---:|---:|---|
| 主结果 | Clinical baseline | 0.5297 | 0.6064 | 0.0767 | 5.0 | 最稳的锚点基线 |
| 主结果 | Lipid-only | 0.5338 | 0.7895 | 0.2556 | 29.4 | 脂质组有信号，但过拟合明显 |
| 主结果 | Clinical + lipid fusion | 0.5364 | 0.8055 | 0.2691 | 34.4 | 主结果中数值最高，但增益有限 |
| 本次补充 | ultra_sparse_lipid | 0.5396 | 0.6949 | 0.1554 | 4.6 | AUC 小幅提高，过拟合明显下降 |
| 本次补充 | compact_fusion | 0.5376 | 0.7621 | 0.2245 | 19.2 | 与主 fusion 几乎同分，但更稳 |

### 这张对照表说明了什么

1. **压缩模型复杂度是值得的。** 至少对 lipid-only 而言，特征数从约 29 个降到约 5 个以后，AUC 还略有改善，gap 明显下降。
2. **fusion 不需要继续堆很大的模型。** `compact_fusion` 与主 `fusion_elastic_net` 几乎同分，但训练-测试差值更小。
3. **这不是“模型飞跃”，而是“结果更可接受”。** 本轮最大的进步是更稳，而不是大幅更高。
4. **下一步瓶颈越来越像标签和队列，而不是算法不够多。**

## 稳定特征摘要（只作为补充证据）

### ultra_sparse_lipid 中最值得继续观察的候选脂质

| 特征 | selection_rate | 备注 |
|---|---:|---|
| LPC(16:0) | 0.6 | 小模型中重复出现频率最高之一 |
| PC(32:1_22:4) | 0.6 | 小模型中重复出现频率最高之一 |
| Hex2Cer(d18:2_16:0) | 0.4 | 单变量 exploratory AUC 相对更可看 |
| PC(38:7e) | 0.4 | 在主结果与本次补充里都反复出现 |
| Cer(d19:1_24:1) | 0.2 | 在多个口径中都出现，但稳定性尚不足 |

### compact_fusion 中 selection_rate ≥ 0.6 的变量

| 变量类型 | 特征 | selection_rate |
|---|---|---:|
| 临床锚点 | BMI | 1.0 |
| 临床锚点 | Gender | 1.0 |
| 临床锚点 | SFT | 1.0 |
| 临床锚点 | age_enroll | 1.0 |
| 临床锚点 | bmi_z_enroll | 1.0 |
| 脂质候选 | Hex1Cer(d18:0_20:4) | 0.8 |
| 脂质候选 | PC(32:1_22:4) | 0.8 |
| 脂质候选 | PC(38:7e) | 0.8 |
| 脂质候选 | Cer(d19:1_24:1) | 0.6 |
| 脂质候选 | FA(22:5) | 0.6 |
| 脂质候选 | Hex2Cer(d18:2_16:0) | 0.6 |
| 脂质候选 | LPC(16:0) | 0.6 |

> 解释重点：这些变量更适合写成 **recurrently selected candidate features**，而不是现在就写成已经定稿的 biomarker panel。

## 标签 / 队列审计本次新增结论

- 当前四张表最终重叠后分析样本量为 **281**，与 handoff 及会议纪要口径一致。
- 临床表中额外存在的 6 个 ID 已明确识别：`C115, C316, E217, F249, F298, F303`。
- 本地标签文件只有 `ID` + `Group`，没有原始结局判定字段。
- 因此本轮可以诚实地说：

> 我们已经做到了**结构级标签与队列审计**，但还没有完成“response/noresponse 真值定义”的原始口径核验。

## 当前最适合对老师 / 合作者怎么说

### 30 秒版

可直接发送：

> 上一轮已经完成、并且现在作为主结果使用的，是那一版 strict nested CV Figure 6-4 结果；它已经出了 PNG、PDF 和发送版 HTML。我们这次没有再回到旧流程，也没有盲目堆模型，而是继续在同一 strict nested CV 口径下试了更小的预定义模型。结果显示，脂质组压缩到约 5 个特征后，AUC 只有小幅改善，但过拟合明显下降；融合模型压缩后分数基本不变，但更稳。这说明下一步最值得做的不是继续加算法，而是继续做稳定特征和标签/队列审计。

### 论文式收束版

可直接发送：

> Within the same strict nested cross-validation framework, pre-defined smaller models reduced the train-test gap and yielded only modest numerical changes in AUC. These findings support a parsimonious, stability-oriented strategy rather than further unbounded expansion of variables or model families. At the same time, the current local data structure allows only structural auditing of the response labels, not full verification of the endpoint-definition ground truth, which remains an important limitation for subsequent interpretation.

## 本页最终结论

1. **主结果仍然是上一轮已经完成并出图的那套 Figure 6-4 strict nested CV 结果。**
2. **本次补充最有价值的进展是“小模型更稳”与“标签/队列边界更清楚”。**
3. **本次补充结果可以进 Discussion / Limitations / Supplement，但不应替代主结果。**
4. **如果接下来继续推进，最值钱的事情是拿到标签原始定义表，而不是继续堆更多模型。**

## 文件入口

- handoff：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`
- 已有发送版 HTML：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_figure6-4_honest_sendable_report.html`
- 本次补充三模型对照表：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_predefined_small_model_comparison.csv`
- 本次补充标签/队列审计：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.md`
- 主结果性能汇总：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
- 主结果 fold 指标：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/fold_metrics.csv`
- 主结果特征稳定性：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`
