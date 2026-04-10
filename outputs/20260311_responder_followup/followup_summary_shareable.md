# Responder follow-up 第一阶段图文汇报页（已接入 out-phase）

> 本页是给老师/合作者直接查看的 follow-up 图文版：**不改正式主结果，但现在已把 out / 干预后数据正式接入，补成“分组审计 + self-validation + out-phase 内部时相验证 + 小模型对照”的完整第一阶段结果页**。

**可直接发送：**

> 老师您好，我把 responder 第一阶段 follow-up 重新完整整理了一版。这次不改既有 strict nested CV 的正式主结果，但已经把新拿到的 out / 干预后数据正式接入，补成四层内容：当前 responder 分组证据链审计、self-validation、3 个小模型 follow-up 比较，以及 out-phase 内部时相验证。页内 repeated hold-out、prefix-holdout 和 out-phase 都明确只写成补充稳健性/内部时相证据，不写成外部验证。当前仍未完成的主要还有三块：真正 alternative grouping sensitivity、prefix↔school/community 映射、以及心血管桥接；等相应原始数据到位后再做。

## 一页结论

- **正式主结果不变**：严格嵌套 CV 仍是论文主口径，旧目录 `outputs/20260310_nested_cv` 保持只读引用。
- **本轮 follow-up 已补成 6 张图**：F1/F2/F3/F4 仍对应“小模型表现、generalization gap、self-validation、group audit”；新增 F5/F6 专门对应 out-phase 内部时相验证。
- **从稳健性角度看**：`clinical_baseline_main` 的 repeated hold-out gap 最小（0.0528），最稳；`compact_fusion` 的 repeated hold-out AUC 最高（0.5717），但泛化 gap 最大（0.1938）。
- **从 out-phase 角度看**：没有出现“明显强复制”，但 `ultra_sparse_lipid` 与 `compact_fusion` 在 out-phase 下仍维持约 0.50 左右 AUC，属于**边界说明型证据**；`clinical_baseline_main` 在 out-phase 下掉得更明显，提示时相迁移并不强。
- **本轮没有伪造缺失模块结果**：缺原始连续终点表，就不做真正 alternative grouping sensitivity；缺 prefix↔school/community 映射，就不把 leave-one-prefix-out 升级成 school/community split；缺心血管表型表，就不做桥接分析。

## 建议阅读顺序

1. 先看 **Figure F1**：小模型 follow-up 主图，快速把握“谁更稳、谁更高、谁更适合当主叙事”。
2. 再看 **Figure F2**：generalization gap，回答“为什么不能只看 AUC 最高”。
3. 再看 **Figure F3**：self-validation 分布，回答“结果是不是单次切分偶然所得”。
4. 再看 **Figure F5**：out-phase 主图，回答“新拿到的 out / 干预后数据接进来后，内部时相迁移表现如何”。
5. 再看 **Figure F6**：out-phase 分布图，回答“这种时相迁移是不是只出现在少数 split”。
6. 最后看 **Figure F4**：当前 responder 分组审计，交代当前标签来源与基线平衡边界。

> 如果老师希望把**既有基线主图 + 本轮 follow-up 6 图**按一套完整顺序看，请直接打开统一汇报包：`teacher_report_package/02_combined_report.html`。

## 正式主结果仍是主锚点（文本口径）

| experiment | mean_auc | std_auc | mean_train_auc |
| --- | --- | --- | --- |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 |

- 上表继续对应既有 strict nested CV 主结果。
- 本页下面的所有新图，定位都是：**补充稳健性证据 / 内部时相验证 / 标签审计**，不是推翻主结果。

## Figure F1. 小模型 follow-up 主图（最接近基线 Figure 6-4 的 follow-up 对应图）

![Figure F1：小模型 follow-up 主图](FigureF1_Followup_ModelPerformance.png)

图文件： [PNG](FigureF1_Followup_ModelPerformance.png) · [PDF](FigureF1_Followup_ModelPerformance.pdf)

### 这张图怎么读

- 这张图仍是本轮 follow-up 最核心的“模型层面”图，对应你之前基线分析里“主性能图”的位置。
- `compact_fusion` 在 repeated hold-out 下均值 AUC 最高（0.5717），说明融合路线仍有一定性能上限。
- 但 `clinical_baseline_main` 更稳：strict nested CV、repeated hold-out、prefix-holdout 三条线更接近，没有明显“只在某一套切分里看起来好”的情况。
- 因此写作上更合理的口径仍是：**临床 5 锚点模型更稳，compact fusion 可作为增强路线，而不是唯一主叙事**。

## Figure F2. Generalization gap（强调不能只看 AUC）

![Figure F2：generalization gap](FigureF2_Followup_GeneralizationGap.png)

图文件： [PNG](FigureF2_Followup_GeneralizationGap.png) · [PDF](FigureF2_Followup_GeneralizationGap.pdf)

### 这张图怎么读

- `compact_fusion` 虽然 AUC 最高，但 repeated hold-out mean gap 约为 **0.1938**，prefix-holdout mean gap 约为 **0.2452**，说明训练-测试落差仍明显。
- `clinical_baseline_main` 的 repeated hold-out mean gap 仅 **0.0528**，prefix-holdout mean gap **0.0832**，是当前三条路线中最容易防守的一条。
- `ultra_sparse_lipid` 介于两者之间：说明“少量脂质即可支持预测”这一补充叙事可以保留，但不宜替代更稳的临床锚点模型。

## Figure F3. Self-validation 分布图（看稳定性，而不是只看均值）

![Figure F3：self-validation 分布图](FigureF3_SelfValidation_Distribution.png)

图文件： [PNG](FigureF3_SelfValidation_Distribution.png) · [PDF](FigureF3_SelfValidation_Distribution.pdf)

### 这张图怎么读

- 这张图把 repeated random hold-out 与 leave-one-prefix-out 各 split 的分布摆出来，避免只汇报一个均值。
- 它回答的是：**这些结果是不是单次切分碰巧得到的**。
- 当前 three-model 的分布中心都在 0.5 上方，但离“强预测”仍有距离；因此 follow-up 更像是“稳健性与边界说明”，而不是“性能显著跃升”。
- 这也支持当前三层叙事：正式主结果保留、补充稳健性证据补上、真正更强的验证等数据到位后再做。

## Figure F5. out-phase 内部时相验证主图（新增）

![Figure F5：out-phase 主图](FigureF5_OutPhase_ModelPerformance.png)

图文件： [PNG](FigureF5_OutPhase_ModelPerformance.png) · [PDF](FigureF5_OutPhase_ModelPerformance.pdf)

### 这张图怎么读

- 这张图是新拿到 out / 干预后数据后补出来的正式 out-phase 主图。
- 它的定位是：**基线训练 → out-phase 测试** 的内部时相验证，不是 external validation。
- 目前 best out-phase mean AUC 大约只在 **0.5073** 左右，说明 out-phase 下没有出现特别强的时相复制。
- 因此这张图更像是在帮我们**诚实划边界**：可以说“差异在 out-phase 下仍有一定残留信号”，但不能说“已经完成强验证”。

## Figure F6. out-phase 分布图（新增）

![Figure F6：out-phase 分布图](FigureF6_OutPhase_Distribution.png)

图文件： [PNG](FigureF6_OutPhase_Distribution.png) · [PDF](FigureF6_OutPhase_Distribution.pdf)

### 这张图怎么读

- 这张图把 out-phase repeated hold-out 与 out-phase prefix hold-out 的 split-level 分布摊开。
- 它回答的是：**out-phase 的结果是不是只被极少数 split 撑起来**。
- 目前 out-phase 分布整体比 self-validation 更靠近 0.5，说明时相迁移比同相切分更难，这本身是有价值的负结果/边界结果。
- 这也支持更谨慎的写法：**out-phase 已完成，但结论应写成 internal temporal validation with modest signal，而不是 strong replication**。

## Figure F4. 当前 responder 分组审计图（标签来源与基线平衡）

![Figure F4：当前 responder 分组审计图](FigureF4_GroupAudit.png)

图文件： [PNG](FigureF4_GroupAudit.png) · [PDF](FigureF4_GroupAudit.pdf)

### 这张图怎么读

- 当前本地能回溯到的是**二分类标签 + 会议纪要级证据链**，不是原始连续终点真值表。
- 因此这张图的作用不是证明“当前分组就是真理”，而是把现阶段能说清楚的两件事摆出来：
  1. 当前标签来源于 ΔBMI 百分位变化及 tie-break 讨论的既有决策脉络；
  2. 至少在几个临床锚点上，没有看到完全失控的基线失衡。
- 这也是为什么本轮正确做法是“审计 + 标注边界”，而不是伪造一套 alternative grouping 结果。

## 小模型 follow-up 关键数字表

| model_label | strict_mean_auc | repeated_holdout_mean_auc | prefix_holdout_mean_auc | outphase_repeated_holdout_mean_auc | outphase_prefix_holdout_mean_auc | repeated_holdout_mean_gap | outphase_repeated_holdout_mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | 0.5297 | 0.5545 | 0.5223 | 0.3601 | 0.4255 | 0.0528 | 0.2472 |
| ultra_sparse_lipid | 0.5338 | 0.5410 | 0.5281 | 0.5034 | 0.5073 | 0.1423 | 0.1798 |
| compact_fusion | 0.5364 | 0.5717 | 0.5157 | 0.4986 | 0.4730 | 0.1938 | 0.2670 |

## 这轮结果如何对应 2026-03-11 的新分析思路

| 对接思路 | 当前状态 | 目前如何落地 |
| --- | --- | --- |
| 分组定义/差异先审清楚 | 部分完成 | 已完成当前 responder 标签证据链审计、基线平衡汇总、ID prefix 分布整理；但仍缺原始连续终点文件。 |
| 小模型、稀疏模型、稳定特征 | 已完成 | 已完成 `clinical_baseline_main`、`ultra_sparse_lipid`、`compact_fusion` 的 strict vs repeated hold-out vs prefix-holdout 比较，并补出 F1/F2/F3 图。 |
| pseudo-external validation | 已完成 | 已实现 leave-one-prefix-out，但明确只可写成 **exploratory weak proxy**；在没有 prefix↔school/community 映射前，不能升级成不同学校/社区验证。 |
| out 数据做验证 | 已完成 | 已接入 out / 干预后数据，完成基线训练 → out-phase 测试的内部时相验证；但结果强度有限，因此定位为边界说明型证据，而不是强复制。 |
| 心血管相关表型 | 当前阻塞 | 本地没有新增整理好的心血管表型表。 |

更完整文字说明见： [followup_plan_alignment.md](followup_plan_alignment.md)

## 当前阻塞项（明确写清，不伪造结果）

1. **alternative grouping sensitivity**：缺少原始连续终点文件（endpoint source）
2. **prefix↔school/community 映射**：当前 leave-one-prefix-out 只能作为 grouped prefix proxy，不能直接升级成不同学校/社区 train/test
3. **心血管表型桥接**：缺少新增整理后的心血管表型表

## 相关文件入口

- 主汇总： [followup_summary.md](followup_summary.md)
- 分组审计： [group_definition_audit.md](group_definition_audit.md)
- out-phase 汇总： [outphase_validation.md](outphase_validation.md)
- 阻塞项： [blocked_items.md](blocked_items.md)
- self-validation 汇总表： [self_validation_summary.csv](self_validation_summary.csv)
- out-phase 汇总表： [outphase_validation_summary.csv](outphase_validation_summary.csv)
- 小模型比较表： [small_model_followup_comparison.csv](small_model_followup_comparison.csv)
- 文献跟进说明： [teacher_report_package/03_literature_followup_note.html](teacher_report_package/03_literature_followup_note.html)
- grouped proxy 逐前缀汇总： [teacher_report_package/prefix_group_holdout_summary.csv](teacher_report_package/prefix_group_holdout_summary.csv)
- 统一汇报包： [teacher_report_package/02_combined_report.html](teacher_report_package/02_combined_report.html)
