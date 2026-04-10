# follow-up 分析结果与 2026-03-11 / 2026-03-12 新建议的对应关系

> 本页专门回答两个问题：**学校 / 社区 split 的新分析现在放在哪里**，以及**运动 protocol 的新版写法应该如何落地**。

## 1. 对接思路 → 当前落点

| 对接思路 | 当前状态 | 当前落地文件 |
| --- | --- | --- |
| 分组定义 / 差异先审清楚 | 部分完成 | 已完成 responder 标签证据链审计与基线平衡；学校映射已找到，但 responder 原始连续终点仍缺失 | 
| 小模型、稀疏模型、稳定特征 | 已完成 | `small_model_followup_comparison.csv`、`followup_summary.md`、Figure F1/F2/F3 |
| 学校 / 社区 split | 已完成（内部 grouped validation 层面） | `school_group_holdout_summary.csv`、`self_validation_summary.csv`、`outphase_validation_summary.csv` |
| out-phase 数据做验证 | 已完成 | `outphase_validation.md`、Figure F5/F6 |
| 运动 protocol 写法 | 已形成当前推荐口径 | 本页第 3 节 + `03_literature_followup_note.md` |
| 心血管相关表型 | 当前阻塞 | 仍缺整理好的表型表 |

## 2. 学校 / 社区 split 现在放在哪里

- 学校/强度映射：`id_school_intensity_mapping.csv`
- 学校级 grouped holdout 汇总：`school_group_holdout_summary.csv`
- 模型级 self-validation 汇总：`self_validation_summary.csv`
- 模型级 out-phase 汇总：`outphase_validation_summary.csv`
- 综合比较表：`small_model_followup_comparison.csv`
- 对接思路定位页：`followup_plan_alignment.md`
- 文献与 protocol 说明：`03_literature_followup_note.md`


### 2.1 当前应优先看的文件

1. `school_group_holdout_summary.csv`：看学校层面的样本量、response rate、强度和单校留一表现。
2. `self_validation_summary.csv`：看 3 个模型在 `leave_one_school_out` 下的均值表现。
3. `outphase_validation_summary.csv`：看 `outphase_leave_one_school_out` 的均值表现。
4. `03_literature_followup_note.md`：看文献启发如何对应到当前已完成分析。

### 2.2 关键术语边界

- `leave_one_school_out`：**内部 grouped validation**。
- `outphase_leave_one_school_out`：**内部时相 grouped validation**。
- `repeated_random_holdout`：**内部自我验证**。
- 以上都**不能**写成 `external validation`。

### 2.3 旧 prefix split 现在怎么处理

- 旧 `leave-one-prefix-out` 保留为早期 grouped weak proxy。
- 因为 `prefix != school`，它**不能**在学校映射补齐后回写成真正的学校 split。

## 3. 运动 protocol 的当前写法建议

### 主文建议保留到什么粒度

- 干预方案编号
- 周期
- 频次
- 总体执行框架

### 哪些内容先放补充材料 / 答审

- 学校 / 场地对应的运动强度分层
- 执行细节
- 依从性记录
- 如需对照，可引用 `id_school_intensity_mapping.csv`

## 4. 当前仍未闭环的内容

- `endpoint_source`：没有原始连续终点文件，就不做真正的 alternative grouping sensitivity。
- 心血管表型整理表：没有这张表，就不做机制桥接分析。

## 5. 一句话给老师 / 合作者

> 学校 / 社区 split 对应的新分析已经不再是“待做”，而是已经落在 `school_group_holdout_summary.csv`、`self_validation_summary.csv`、`outphase_validation_summary.csv` 和 `03_literature_followup_note.md` 里；当前更需要继续守住的边界，是这些都仍属于内部验证，不是 external validation，而运动 protocol 的主文写法可以先保持在方案编号、周期、频次这一级。
