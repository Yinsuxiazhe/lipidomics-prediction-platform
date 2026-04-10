# responder teacher report package

- 优先打开 `02_combined_report.html`：这是按“基线主结果 → school split follow-up → out-phase → 当前边界”排好的完整汇报页。
- 如只想看本轮 follow-up，打开 `01_followup_report.html`。
- 如要回答“学校/社区 split 的新分析放在哪里、运动 protocol 怎么写”，打开 `03_literature_followup_note.html`。
- 如要直接汇报“固定若干校区训练、另外若干校区测试”的两套方案与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。
- `assets/` 目录内含 7 张图的 PNG/PDF，可单独抽取发送。

## 本轮已新增并同步的关键文件

- `school_group_holdout_summary.csv`
- `id_school_intensity_mapping.csv`
- `self_validation_summary.csv`
- `outphase_validation_summary.csv`
- `small_model_followup_comparison.csv`
- `followup_plan_alignment.md`
- `04_fixed_school_combo_note.html`
- `fixed_school_combo_result_comparison.csv`
- `fixed_school_combo_scheme_design.csv`

## 当前必须坚持的科学口径

- 正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54。
- 用户记得的 AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`。
- `repeated_random_holdout`、`leave_one_school_out`、`leave_one-prefix-out`、`outphase_leave_one_school_out` 都不能写成 `external validation`。
- 旧 `leave-one-prefix-out` 只能保留为早期 grouped weak proxy，不能在学校映射补齐后回写成真正的学校 split。

## 当前仍未闭环的两项

- responder 定义源头核对 / alternative grouping sensitivity：仍缺原始连续终点文件（endpoint_source）
- 心血管表型桥接：仍缺整理后的心血管表型表

## 最稳妥的一句话

- 这是一套已经把真实学校 grouped split 与 out-phase internal temporal validation 补齐后的内部汇报包；它强化的是“边界与稳健性说明”，不是 external validation 或强泛化声明。
