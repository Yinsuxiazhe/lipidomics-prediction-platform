# 补充说明与下一步建议

> 本页补充说明本次整理过程中的结果比对、材料清单与下一步建议，不改变正式主结果锚点。

## 项目角色

- 需求方：`Shuxian Zhang`
- 分析提供方：`Chenyu Fan`

## 1. 本次整理完成事项

| 模块 | 已完成内容 |
| --- | --- |
| 论文审查 | 确认 Nature 论文涉及 UK Biobank、Estonian Biobank、THL Biobank |
| supplement 审查 | 确认 `Age + sex + metabolomics` 模型对应 36 个 biomarker |
| 本地可接入性核查 | 检查 baseline / out-phase 临床与脂质组字段是否足以构建 overlap route |
| 结果边界校正 | 明确 AUC≈0.8 仅对应 `mean_train_auc` |
| HTML 交付 | 完成补充说明页与正式报告页 |
| 正式报告包 | 形成可直接阅读的正式报告包 |

## 2. 运算结果比对

| 路线 | 当前状态 | 是否可称 strict external validation |
| --- | --- | --- |
| strict nested CV 主结果 | 已存在正式结果 | 否 |
| repeated hold-out / leave-one-school-out | 已存在稳健性结果 | 否 |
| baseline -> out-phase | 已存在队列内时相验证 | 否 |
| transport_core_8 / transport_extended_12 | 当前为设计草案 | 否 |
| UKB / EBB / THL proxy 申请或合作 | 尚未启动正式外部执行 | 否 |

## 3. 当前最值得推进的动作

1. 直接运行 `transport_core_8` / `transport_extended_12` 的本地 strict nested CV。
2. 输出 reduced model 与现有主结果的对照表。
3. 如结果仍有一定信息量，再决定是否推进 UKB feasibility 或合作代跑。

## 4. 材料清单

### 根目录文件

- `index.html`
- `01_biobank_external_proxy_formal_report.html`
- `02_supplementary_note.html`
- `overlap_feature_mapping.csv`
- `reduced_external_proxy_model_feature_set.csv`
- `strict_nested_cv_performance_summary.csv`

### 复现支持目录

- `analysis_code/`
- `analysis_data/`

## 5. 当前边界再次强调

- 当前材料支持：**external-proxy / transportability feasibility**。
- 当前材料不支持：**将三 biobanks 直接写成当前 responder 模型的严格外部验证**。
- 若后续产生 reduced model 实测结果，也仍需区分：**本地内部验证** 与 **外部 proxy 验证**。
