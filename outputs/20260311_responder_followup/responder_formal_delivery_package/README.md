# responder formal delivery package

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan

## 建议阅读顺序

1. 先打开 `index.html`：这是总览页，按“正式主结果 → school split follow-up → out-phase temporal validation → protocol / 写作边界”组织。
2. 如需单看 follow-up 解释层，打开 `01_followup_formal_report.html`。
3. 如需单看 school / community split 与 protocol 写法，打开 `03_school_split_protocol_note.html`。
4. 如需单看固定校区 train/test 组合与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。

## 包内主要页面

- `index.html`
- `01_followup_formal_report.html`
- `02_combined_formal_report.html`
- `03_school_split_protocol_note.html`
- `04_fixed_school_combo_note.html`

## 代码与数据

- `analysis_code/`：本次报告包对应的分析代码。
- `analysis_data/`：本次报告包对应的主要分析输入数据。

## 当前必须坚持的科学边界

- 正式主结果仍是 strict nested CV 的 outer-test AUC，约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- `repeated hold-out`、`leave-one-school-out`、固定校区组合版 split、`outphase_leave_one_school_out` 均属于补充验证证据链，不能写成 `external validation`。
- 当前 package 支持的是“边界更清楚、解释更完整、材料更完整”，不支持“强跨校区泛化已被证明”。

## 主要清单

- `strict_nested_cv_key_metrics.csv`
- `school_group_holdout_summary.csv`
- `self_validation_summary.csv`
- `outphase_validation_summary.csv`
- `fixed_school_combo_result_comparison.csv`
- `fixed_school_combo_scheme_design.csv`
- `id_school_intensity_mapping.csv`
- `analysis_code/`
- `analysis_data/`
- `assets/`
