# strict nested CV 正式说明

> 本文档为正式版综合说明，采用分点论证方式组织内容，用于结果汇报、协作讨论和项目留档。

**更新日期：2026-03-11 ｜ 分析者：Chenyu Fan ｜ 需求方：Shuxian Zhang**

![Figure 6-4：strict nested CV 主图](../01_主图与主结果/Figure6-4_Honest_NestedCV.png)

## 1. 本次正式结果的核心结论

1. 本次正式主结果应以 **strict nested CV** 为唯一正式口径。
2. 在 5 个主模型中，`Clinical + lipid fusion` 的 mean AUC 最高，为 **0.5364**，但仅略高于 `Clinical baseline`（**0.5297**）和 `Lipid-only`（**0.5338**）。
3. 更高维的 expanded 模型并未带来更好的外层测试表现，说明单纯增加变量数量并不能稳定提升泛化能力。
4. 当前结果更适合支持“**存在一定预测信号，但泛化增益有限**”这一表述，而不适合上升为“已经建立高性能稳定预测模型”的表述。

## 2. 为什么正式结果采用 strict nested CV

1. **方法学边界更清楚。** 特征筛选、标准化、参数调优均限定在训练折内完成，外层测试折仅用于最终评估。
2. **结果含义更接近真实泛化能力。** 外层测试折不参与建模决策，因此 AUC 更接近模型离开当前训练样本后的实际表现。
3. **可以显著降低乐观偏差。** 当筛特征和调参提前接触验证信息时，结果往往会被高估；strict nested CV 的核心价值正是避免这一问题。
4. **更适合作为论文主图和正式结论。** 对正式汇报和后续投稿而言，可信度比表面分数更重要。

## 3. 主结果数据与证据链

| 模型 | mean AUC | std AUC | mean train AUC | 训练-测试差值 | 每折特征数 | 结果解释 |
|---|---:|---:|---:|---:|---:|---|
| Clinical baseline | 0.5297 | 0.0640 | 0.6064 | 0.0767 | 5 | 固定 5 个临床锚点，作为最稳妥的基线参考。 |
| Expanded clinical | 0.5011 | 0.0742 | 0.7437 | 0.2426 | 19–27 | 扩展临床变量更多，但泛化表现未见改善，提示高维临床变量带来额外不稳定性。 |
| Lipid-only | 0.5338 | 0.0701 | 0.7895 | 0.2556 | 28–30 | 脂质组存在一定预测信号，但训练—测试差值较大，过拟合风险明显。 |
| Clinical + lipid fusion | 0.5364 | 0.0535 | 0.8055 | 0.2691 | 33–35 | 当前 mean AUC 最高，但仅为有限增益，更适合表述为“略优”而非“明显优于”。 |
| Expanded fusion | 0.5258 | 0.0450 | 0.8496 | 0.3239 | 49–57 | 变量规模最大，训练分数最高，但泛化没有同步提升，过拟合最明显。 |

### 3.1 对主结果的直接解释

1. `Clinical baseline` 虽然分数不高，但训练—测试差值最小，是当前最稳妥的参考基线。
2. `Lipid-only` 与 `Clinical + lipid fusion` 显示出一定增量信号，但两者的训练—测试差值均超过 **0.25**，提示现阶段仍存在明显过拟合压力。
3. `Expanded clinical` 和 `Expanded fusion` 在变量数明显增加后，并未换来更高的泛化 AUC，反而进一步扩大了训练—测试差值。
4. 因此，本轮结果的重点不应放在“再增加多少变量”，而应放在“怎样缩小训练—测试差值并提高跨折稳定性”。

### 3.2 训练 ROC 与泛化差距补充图（方法学辅助，不作正式性能声明）

> 以下图件用于解释“模型在训练阶段已学到一定模式，但外层测试泛化增益有限”这一现象。**正式性能声明仍以上述 strict nested CV outer-test mean AUC 与 Figure 6-4 主图为准**，不以训练 ROC 单独定性模型优劣。

#### 3.2.1 训练 AUC vs 外层测试 AUC 的整体对照

![训练 AUC 与泛化差距组合图](../05_补充图_训练AUC与泛化差距/20260311_训练AUC与泛化差距_组合图.png)

1. `Clinical baseline` 的训练—测试差值最小（**0.0767**），虽然绝对 AUC 不高，但说明其作为锚点基线最稳。
2. `Lipid-only` 与 `Clinical + lipid fusion` 的 outer-test AUC 略高于基线，但训练—测试差值都在 **0.25** 左右，提示当前增益仍伴随明显过拟合压力。
3. `Expanded clinical` 与 `Expanded fusion` 的训练 AUC 明显更高，但外层测试表现并未同步改善，支持“增加变量规模不等于提升泛化能力”的判断。
4. 因此，这组图更适合支撑“**模型学到了模式，但模式尚未稳定转化为强泛化性能**”这一解释，而不是支持更激进的性能表述。

#### 3.2.2 5 个主模型 publication-style ROC 总览

![5 个主模型 publication-style ROC 总览](../05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png)

1. 该总览图便于横向比较 5 个主模型的训练 ROC 与 outer-test ROC 之间的相对分离程度。
2. 从排版角度看，当前 legend 统一下置，未见明显文字重叠，可直接作为补充审阅图件。
3. 但从解释角度看，仍应把它理解为**方法学辅助图**：它说明训练阶段的分离模式与泛化之间存在落差，而不是新的正式主结果。
4. 本页不单独突出“训练结果最强模型”的训练单图，以避免训练表现被误读为正式性能声明。

#### 3.2.3 5 个主模型单图（便于逐张阅读）

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin:1.2em 0;">
  <figure style="margin:0;border:1px solid #dddddd;border-radius:8px;padding:14px;background:#ffffff;">
    <img src="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_baseline_publication.png" alt="Clinical baseline publication-style ROC" />
    <figcaption>
      <strong>Clinical baseline</strong><br />
      训练 AUC = 0.606；外层测试 AUC = 0.530；差值 = 0.077。<br />
      当前最稳妥的锚点基线：分数不高，但训练与外层测试之间的落差最小。<br />
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_baseline_publication.png">PNG</a> /
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_baseline_publication.pdf">PDF</a>
    </figcaption>
  </figure>
  <figure style="margin:0;border:1px solid #dddddd;border-radius:8px;padding:14px;background:#ffffff;">
    <img src="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_clinical_publication.png" alt="Expanded clinical publication-style ROC" />
    <figcaption>
      <strong>Expanded clinical</strong><br />
      训练 AUC = 0.744；外层测试 AUC = 0.501；差值 = 0.243。<br />
      扩展临床变量数量增加后，训练分离增强，但泛化没有随之改善。<br />
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_clinical_publication.png">PNG</a> /
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_clinical_publication.pdf">PDF</a>
    </figcaption>
  </figure>
  <figure style="margin:0;border:1px solid #dddddd;border-radius:8px;padding:14px;background:#ffffff;">
    <img src="../05_补充图_训练AUC与泛化差距/20260311_ROC_lipid_only_publication.png" alt="Lipid-only publication-style ROC" />
    <figcaption>
      <strong>Lipid-only</strong><br />
      训练 AUC = 0.789；外层测试 AUC = 0.534；差值 = 0.256。<br />
      说明脂质组中存在一定可学习信号，但过拟合压力仍然明显。<br />
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_lipid_only_publication.png">PNG</a> /
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_lipid_only_publication.pdf">PDF</a>
    </figcaption>
  </figure>
  <figure style="margin:0;border:1px solid #dddddd;border-radius:8px;padding:14px;background:#ffffff;">
    <img src="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_lipid_fusion_publication.png" alt="Clinical plus lipid fusion publication-style ROC" />
    <figcaption>
      <strong>Clinical + lipid fusion</strong><br />
      训练 AUC = 0.806；外层测试 AUC = 0.536；差值 = 0.269。<br />
      当前 5 个主模型中 outer-test mean AUC 最高，但优势幅度有限，不宜夸大为显著提升。<br />
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_lipid_fusion_publication.png">PNG</a> /
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_clinical_lipid_fusion_publication.pdf">PDF</a>
    </figcaption>
  </figure>
  <figure style="margin:0;border:1px solid #dddddd;border-radius:8px;padding:14px;background:#ffffff;">
    <img src="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_fusion_publication.png" alt="Expanded fusion publication-style ROC" />
    <figcaption>
      <strong>Expanded fusion</strong><br />
      训练 AUC = 0.850；外层测试 AUC = 0.526；差值 = 0.324。<br />
      变量规模最大、训练分数最高，但训练与外层测试的落差也最大，过拟合最明显。<br />
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_fusion_publication.png">PNG</a> /
      <a href="../05_补充图_训练AUC与泛化差距/20260311_ROC_expanded_fusion_publication.pdf">PDF</a>
    </figcaption>
  </figure>
</div>

#### 3.2.4 这些补充图目前最能支持的解释

1. 训练 ROC 与 outer-test ROC 之间的落差，说明当前模型确实学到了一定分离模式，但其中相当一部分尚未稳定转化为跨折泛化能力。
2. 模型越复杂，训练分数通常越高，但外层测试 AUC 并未同步受益；这与主结果表中的训练—测试差值趋势一致。
3. 因此，脂质组与融合方向并非没有价值，而是更需要继续做**模型压缩、稳定特征筛选、标签/队列核查与外部验证**。
4. 这也是为什么本页把这些图放在“补充解释”位置，而不是把训练 ROC 独立包装成新的正式性能声明。

### 3.3 当前主模型的稳定特征线索

1. `Lipid-only` 中跨折更稳定的脂质主要包括：PA(28:0)、PC(38:7e)、Cer(d19:1_24:1)、Hex1Cer(d18:0_20:4)、Hex2Cer(d18:2_16:0)、PC(26:3e)、PC(32:1_22:4)。
2. `Expanded clinical` 中更稳定的扩展临床变量主要包括：whole_blood_LYMPH_count、AV_sub、HAD、HARI、HRI、Inbody_122_BFM._of_Left_Leg、Inbody_207_Growth_Score、SFT。
3. `Expanded fusion` 的高频变量同时混合了扩展临床与脂质特征，代表性变量包括：PA(28:0)、PC(38:7e)、whole_blood_LYMPH_count、AV_sub、Cer(d19:1_24:1)、HAD、HARI、HRI。
4. 这些稳定特征可作为后续压缩模型或补充生物学解释的候选线索，但在当前阶段仍不应被直接等同于“已定稿的生物标志物集合”。

## 4. 正式结果能够支持的判断边界

### 4.1 可以正式支持的判断

1. 目前数据中可以检测到一定预测信号。
2. 脂质组与融合模型相较单纯临床基线存在**有限增量**，但增幅较小。
3. 模型复杂度继续增大时，泛化性能并未同步提升，且过拟合迹象更明显。
4. strict nested CV 结果比开发阶段结果更适合承担主图、主结论和正式性能声明的角色。

### 4.2 当前不宜正式支持的判断

1. 不宜表述为“脂质组显著、大幅、稳定提升了预测性能”。
2. 不宜表述为“已经得到高性能、可直接临床转化的预测模型”。
3. 不宜用更早期的较高分结果替代 strict nested CV 结果充当正式主结果。

## 5. 补充小模型分析带来的新增信息

| 模型 | mean AUC | std AUC | mean train AUC | 训练-测试差值 | 平均特征数 | 结果解释 |
|---|---:|---:|---:|---:|---:|---|
| Clinical baseline（主基线） | 0.5297 | 0.0640 | 0.6064 | 0.0767 | 5.0 | 最稳但区分能力有限，是正式结果解释时的重要基线。 |
| ultra_sparse_lipid | 0.5396 | 0.0871 | 0.6949 | 0.1554 | 4.6 | 脂质特征压缩到约 5 个后，训练—测试差值明显下降，并出现小幅 AUC 改善。 |
| compact_fusion | 0.5376 | 0.0506 | 0.7621 | 0.2245 | 19.2 | 融合模型缩小后稳定性改善，但 AUC 增益仍非常有限。 |

### 5.1 补充分析的结论重点

1. 将脂质模型压缩到约 **5 个特征** 后，`ultra_sparse_lipid` 的 mean AUC 提升到 **0.5396**，同时训练—测试差值从主脂质模型的 **0.2556** 降到 **0.1554**，说明**压缩复杂度有助于提升稳定性**。
2. `compact_fusion` 的 mean AUC 为 **0.5376**，与主融合模型 **0.5364** 非常接近，但训练—测试差值下降到 **0.2245**，说明**较小的融合模型更稳，但收益仍然有限**。
3. 这组补充结果共同支持：当前更值得优先推进的是**模型压缩、稳定特征筛选和标签/队列核查**，而不是继续无边界扩展变量和算法。

## 6. 标签与队列审计目前能支持的结论

1. `287 → 281` 的分析样本收敛路径是可追溯的，四张核心表重叠后的最终分析样本量为 **281**。
2. 临床表中存在但未进入最终 281 分析队列的 6 个 ID 为：`C115`、`C316`、`E217`、`F249`、`F298`、`F303`。
3. 现有本地标签文件仅能支持 **结构级标签审计**，即可以确认 ID 与 `Group` 分布，但尚不足以完成 response / noresponse 原始定义、时间窗和阈值的原始核验。
4. 因此，当前最稳妥的正式写法是：**已完成结构级标签/队列审计，但结局真值定义仍需进一步核对。**

## 7. 正式材料与补充材料的排布建议

### 7.1 建议放入主文章正文或主汇报页的内容

1. `01_主图与主结果/Figure6-4_Honest_NestedCV.png` 与对应 PDF。
2. `01_主图与主结果/performance_summary.csv` 对应的 5 个主模型总体性能结果。
3. 对主结果的核心表述：
   - 融合模型数值最高，但领先幅度有限；
   - 扩展模型未改善泛化；
   - strict nested CV 下的结果更可信，应作为正式结论依据。

### 7.2 建议放入补充材料或方法附件的内容

1. `02_补充分析与审计/20260310_predefined_small_model_comparison.csv` 及其小模型目录。
2. `02_补充分析与审计/20260310_small_model_label_audit.md` 与对应 CSV。
3. `01_主图与主结果/fold_metrics.csv`、`feature_stability_summary.csv`、`feature_frequency.csv`、`roc_curve_points.csv`。
4. `03_关键代码与配置/` 中的关键实现脚本与配置文件。
5. `05_补充图_训练AUC与泛化差距/` 中的组合图、contact sheet 与 5 张 publication-style ROC 单图，可作为补充材料或方法学审阅附件。

## 8. 文件级阅读与使用建议

### 8.1 最值得优先打开的文件

1. `00_正式说明/20260311_strict_nested_cv正式说明.html`
2. `01_主图与主结果/Figure6-4_Honest_NestedCV.png`
3. `01_主图与主结果/performance_summary.csv`
4. `05_补充图_训练AUC与泛化差距/20260311_训练AUC与泛化差距_组合图.png`
5. `05_补充图_训练AUC与泛化差距/20260311_ROC_publication_contact_sheet.png`
6. `04_方法学说明/20260311_strict_nested_cv结果定位说明.md`

### 8.2 关键代码文件的作用分工

1. `03_关键代码与配置/run_pipeline.py`：主流程入口，负责串联主要分析阶段。
2. `03_关键代码与配置/config/analysis.yaml`：输入、标签、CV 参数和输出目录配置。
3. `03_关键代码与配置/src/models/run_nested_cv.py`：strict nested CV 的核心实现。
4. `03_关键代码与配置/src/reports/make_tables.py`：导出 performance、fold 与 stability 相关数据表。
5. `03_关键代码与配置/src/reports/make_figures.py`：导出 ROC 点位等绘图支撑数据。
6. `03_关键代码与配置/fig6-4最终.R`：读取 strict nested CV 输出并生成 Figure 6-4。

## 9. 当前阶段最稳妥的正式表述

1. **正式结论**：当前 strict nested CV 结果显示，模型存在一定预测信号，但泛化增益有限；融合模型虽为当前最优，但优势幅度较小。
2. **方法学结论**：正式结果应以 strict nested CV 为准，因为该口径更能反映真实泛化能力，并减少乐观偏差。
3. **工作重点**：后续优先方向应是标签定义核查、稳定特征提炼、模型压缩和外部验证，而不是继续无边界增加变量或更换更复杂算法。
4. **补充图定位**：训练 ROC 与训练—测试差值图可用于说明“已学到一定模式但泛化有限”，但它们不替代 outer-test 主结果，也不单独承担正式性能声明。
