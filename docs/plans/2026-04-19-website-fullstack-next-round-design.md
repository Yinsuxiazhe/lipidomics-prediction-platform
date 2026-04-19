# Website Full-Stack Next-Round Design (Clinical + Lipid + Fusion)

## 1. Goal

在不伪装“已经完成”的前提下，真实补齐上一轮文档中标记为“下一轮待做”的核心能力：

1. 训练并导出 **clinical-only / lipid-only / fusion** 三类多指标模型；
2. 在网站中真实接入这三类模型，而不是只改文案；
3. 为每个 `indicator × grouping` 提供三层模型对比、算法比较、校准曲线与 DCA 展示；
4. 维持当前已经修正过的科学口径：
   - 指标均指 **变化量**（`Δ = outroll - enroll`）；
   - `Q / T` 指 **极端分组策略**，而非旧内部后缀本身；
   - 不把 strict nested CV 的训练 AUC 写成外部验证结果；
   - 不强行宣称 fusion 永远最优，而是在同一验证框架内客观筛选更优 fusion 模型。

## 2. 设计边界

### 2.1 本轮必须真实落地
- clinical-only 模型资产
- lipid-only 模型资产
- fusion 模型资产
- 网站的动态输入结构（临床项 / 脂质项按模型要求显示）
- `clinical-only / lipid-only / fusion` 三层对比
- 算法比较表
- calibration / DCA 数据与前端展示
- 文档从“待做”回填为“真实已完成”

### 2.2 本轮不扩张的范围
- 不新增 external validation 叙事
- 不把旧 strict nested CV 主结果目录覆盖掉
- 不把网站扩成 clinical_full / fusion_full 的多变体矩阵
- 不重构成全新技术栈；继续使用当前 Flask + 单页模板结构

## 3. 科学与产品约束

### 3.1 同一验证框架
clinical-only、lipid-only、fusion 的比较必须建立在 **同一批可对齐样本** 上，避免出现“clinical 用 287，lipid/fusion 用 281”导致的不公平对比。为此本轮统一使用：

- baseline clinical: `287_enroll_data_clean.csv`
- lipid baseline: `281_merge_lipids_enroll.csv`
- label source: `outputs/20260410_multi_indicator_glm5/phase1_labels.csv`
- aligned cohort: **有脂质数据且有标签的受试者子集**

这样 clinical-only 与 lipid-only / fusion 的网站展示口径保持同一验证框架。

### 3.2 目标定义
所有目标继续使用 Phase 1 已确认的定义：

- `delta = outroll - enroll`
- `Q`: Q1 vs Q4
- `T`: T1 vs T3
- `PSM` 方向为“越高越好”
- 其他当前 7 个指标方向默认按“下降更多为高响应”解释

### 3.3 fusion 默认展示原则
fusion 不是默认被写成“最好”，而是：

1. 在同一 `indicator × grouping × model_type=fusion` 下，先筛出 **best fusion algorithm**；
2. 排序优先级：
   - `mean_auroc` 降序
   - 若接近，再比较 `mean_auprc`
   - 再比较 `mean_sensitivity + mean_specificity`
   - 最后比较模型复杂度（更简洁者优先）
3. 网站在三层对比中客观展示 clinical / lipid / fusion，不把 fusion 写成 universal winner。

## 4. 特征空间设计

### 4.1 clinical-only
使用与既有 responder 分析一致的精简临床基线空间，优先采用以下字段：

- `age_enroll`
- `Gender`
- `BMI`
- `bmi_z_enroll`
- `SFT`

设计理由：
- 与既有 `clinical_slim_logistic` / `fusion` 思路连续；
- 输入成本低，适合网站动态表单；
- 避免把 400+ 临床列直接带入网站端。

### 4.2 lipid-only
沿用当前 GLM5 多指标流程已经筛出的脂质特征：

- 来源：`outputs/20260410_multi_indicator_glm5/phase2_selected_features/features_<indicator>_<cutoff>.csv`

这样可以最大化复用现有多指标网站资产逻辑，并保持脂质侧与上一轮结果的连续性。

### 4.3 fusion
将以下两部分直接拼接：

- clinical-only 的 5 个基础临床变量
- 对应 `indicator × cutoff` 的已筛选 lipid 特征

该方案满足：
- 真正实现“临床 + 脂质”融合；
- 输入层可拆成“Clinical Inputs” + “Lipid Inputs”；
- 不引入新的 clinical_full / fusion_full 复杂度。

## 5. 训练与评估设计

### 5.1 模型组合
每个 `indicator × cutoff × model_type` 评估以下 4 个算法：

- `EN_LR`
- `XGBoost`
- `RF`
- `LR_L2`

总组合数：
- 8 indicators × 2 groupings × 3 model types × 4 algorithms = **192 runs**

### 5.2 评估方式
使用与现有 GLM5 pipeline 一致的严格外层评估思路，保留：

- 5-fold stratified outer CV
- 每折 outer test 概率拼接成全体 OOF 预测

输出：
- `mean_auroc`
- `std_auroc`
- `mean_auprc`
- `mean_sensitivity`
- `mean_specificity`
- `mean_accuracy`
- `mean_f1`
- `mean_brier`
- 全体 OOF `y_true / y_prob`

### 5.3 校准与 DCA
基于 OOF 预测生成：

- calibration curve（分箱预测概率 vs 实际阳性率）
- Brier score
- DCA net benefit 曲线：
  - all-model net benefit
  - treat-all
  - treat-none

这些结果仅作为 **当前训练集内 OOF 展示**，不写成 external validation。

### 5.4 部署模型
评估完成后，对每个组合在全量 aligned cohort 上重新拟合一个最终模型，用于网站在线预测。

## 6. 输出目录与文件结构

新建独立输出目录，避免覆盖旧结果：

- `outputs/20260419_multi_type_glm5/`

核心产物：
- `performance_summary.csv`
- `fold_metrics.csv`
- `algorithm_comparison.csv`
- `best_models.json`
- `comparison_index.json`
- `trained_models/*.pkl`
- `trained_models/model_metadata.json`
- `calibration/*.json`
- `dca/*.json`
- `roc/*.csv`

网站实际加载目录：
- `website/trained_models/`
  - 同步上述 `.pkl`
  - `model_metadata.json`

## 7. 元数据设计

每个模型 metadata 至少包含：

- `key`
- `indicator`
- `cutoff`
- `model_type` (`clinical`, `lipid`, `fusion`)
- `model_name`
- `features`
- `clinical_features`
- `lipid_features`
- `input_schema`
- `sample_values`
- `performance`
- `calibration`
- `dca`
- `roc_path` / `roc_points`
- `is_best_within_type`
- `is_best_overall`

其中 `input_schema` 要能直接驱动前端动态渲染。

## 8. 网站后端设计

继续使用 `website/app.py`，新增而不是推翻现有结构。

### 8.1 新增能力
- 统一加载 `website/trained_models/model_metadata.json`
- `/api/models` 返回 `model_type`、动态输入 schema、最佳模型标记
- `/api/model_detail/<key>` 返回 calibration / DCA / 特征拆分信息
- `/api/predict` 支持 clinical / lipid / fusion 混合输入
- `/api/comparison` 按 `indicator + group` 返回 clinical / lipid / fusion 三层 best model 对比
- `/api/model_family_summary` 返回某个 `indicator + group` 下全部算法结果，用于算法比较表

### 8.2 预测输入处理
后端统一按 metadata 中的 `features` 顺序组装特征向量；
`clinical_features` 与 `lipid_features` 仅用于前端展示与缺失提示，不改变预测顺序。

## 9. 前端设计

继续基于 `website/templates/index.html` 单页实现，新增以下展示层：

1. **Model Type Selector**
   - clinical-only
   - lipid-only
   - fusion

2. **Dynamic Input Sections**
   - clinical fields：结构化表单
   - lipid fields：按所选模型需要的脂质特征动态渲染
   - fusion：同时显示两块

3. **Comparison Panel**
   - 同一 `indicator × grouping` 下展示 best clinical / best lipid / best fusion
   - 关键指标：AUROC / AUPRC / Sens / Spec / Brier

4. **Algorithm Comparison Table**
   - 当前选定 `indicator × grouping × model_type` 下 4 种算法并排

5. **Calibration & DCA Cards**
   - 使用后端返回数据绘制简单 SVG / canvas 折线图

## 10. 文档回填规则

只有在以下条件满足后，才允许把现有文档里的“下一轮待做”改成“本轮已完成”：

- 真实模型资产已训练并导出
- 网站真实接入 clinical / lipid / fusion
- API 与前端交互可用
- 测试与 smoke verification 通过

届时回填：
- `20260417_张淑贤_关于网站建议/20260418_网站展示逻辑清单.md`
- `20260417_张淑贤_关于网站建议/20260417_网站建议整理与实施方案.html`
- `20260417_张淑贤_关于网站建议/20260418_张淑贤建议.txt`

## 11. 风险与应对

### 风险 1：192 个组合训练较慢
应对：
- 复用现有已筛 lipid features，避免重复做 Phase 2
- 单独写可重入脚本，允许断点复跑

### 风险 2：网站动态表单复杂度变高
应对：
- 把表单逻辑完全绑定到 metadata 的 `input_schema`
- 先保证可用，再做样式 polish

### 风险 3：fusion 并不总是最好
应对：
- 在 comparison 中按真实结果展示
- 只保证“best fusion algorithm 被优先展示”，不强行让 fusion 成为 overall best

## 12. 完成判定

本轮只有在以下事实同时成立时才算“真实全量完成”：

1. 新输出目录存在 clinical / lipid / fusion 三类已训练模型；
2. `website/trained_models/model_metadata.json` 含三类模型；
3. Flask API 能返回比较、校准、DCA、动态输入 schema；
4. 前端能切换 clinical / lipid / fusion 并完成预测；
5. 文档已由“待做”改为真实完成状态；
6. 验证命令有 fresh evidence。
