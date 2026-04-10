from pathlib import Path

import pandas as pd


def test_loads_default_pipeline_config(tmp_path):
    from run_pipeline import load_pipeline_config

    config_path = tmp_path / "analysis.yaml"
    config_path.write_text("project_name: lipidomics\n", encoding="utf-8")

    config = load_pipeline_config(config_path)

    assert config["project_name"] == "lipidomics"


def test_pipeline_dry_run_returns_selected_stage_manifest(tmp_path):
    from run_pipeline import run_stage

    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: lipidomics",
                "paths:",
                "  group: group.csv",
                "  lipid: lipid.csv",
                "  clinical_full: clinical_full.csv",
                "  clinical_slim: clinical_slim.csv",
            ]
        ),
        encoding="utf-8",
    )

    manifest = run_stage(stage="cohort", config_path=config_path, dry_run=True)

    assert manifest["stage"] == "cohort"
    assert manifest["status"] == "dry_run"


def test_pipeline_experiments_stage_runs_on_toy_csv_inputs(tmp_path):
    from run_pipeline import run_stage

    group = tmp_path / "group.csv"
    group.write_text(
        "ID,Group\n"
        "A001,noresponse\nA002,noresponse\nA003,noresponse\nA004,noresponse\nA005,noresponse\nA006,noresponse\n"
        "A007,response\nA008,response\nA009,response\nA010,response\nA011,response\nA012,response\n",
        encoding="utf-8",
    )
    lipid = tmp_path / "lipid.csv"
    lipid.write_text(
        "NAME,lipid_signal,lipid_shadow\n"
        "A001,0.1,0.11\nA002,0.1,0.11\nA003,0.1,0.11\nA004,0.1,0.11\nA005,0.1,0.11\nA006,0.1,0.11\n"
        "A007,10.0,10.1\nA008,10.0,10.1\nA009,10.0,10.1\nA010,10.0,10.1\nA011,10.0,10.1\nA012,10.0,10.1\n",
        encoding="utf-8",
    )
    clinical_slim = tmp_path / "clinical_slim.csv"
    clinical_slim.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI\n"
        "A001,10,1.0,3.0,0,20\nA002,10,1.0,3.0,1,20\nA003,10,1.0,3.0,0,20\nA004,10,1.0,3.0,1,20\nA005,10,1.0,3.0,0,20\nA006,10,1.0,3.0,1,20\n"
        "A007,10,3.0,1.0,0,28\nA008,10,3.0,1.0,1,28\nA009,10,3.0,1.0,0,28\nA010,10,3.0,1.0,1,28\nA011,10,3.0,1.0,0,28\nA012,10,3.0,1.0,1,28\n",
        encoding="utf-8",
    )
    clinical_full = tmp_path / "clinical_full.csv"
    clinical_full.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10,1.0,3.0,0,20,1.0\nA002,10,1.0,3.0,1,20,1.0\nA003,10,1.0,3.0,0,20,1.0\nA004,10,1.0,3.0,1,20,1.0\nA005,10,1.0,3.0,0,20,1.0\nA006,10,1.0,3.0,1,20,1.0\n"
        "A007,10,3.0,1.0,0,28,3.0\nA008,10,3.0,1.0,1,28,3.0\nA009,10,3.0,1.0,0,28,3.0\nA010,10,3.0,1.0,1,28,3.0\nA011,10,3.0,1.0,0,28,3.0\nA012,10,3.0,1.0,1,28,3.0\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: toy_pipeline",
                "paths:",
                f"  group: {group}",
                f"  lipid: {lipid}",
                f"  clinical_full: {clinical_full}",
                f"  clinical_slim: {clinical_slim}",
                "experiments:",
                "  requested:",
                "    - clinical_slim_logistic",
                "    - lipid_elastic_net",
                "outputs:",
                f"  base_dir: {tmp_path / 'outputs'}",
                "  cv_config:",
                "    outer_splits: 3",
                "    outer_repeats: 1",
                "    inner_splits: 2",
                "    random_state: 42",
                "    lipid_top_k: 2",
                "    clinical_top_k: 5",
                "    correlation_threshold: 0.95",
                "    clinical_missing_threshold: 0.2",
            ]
        ),
        encoding="utf-8",
    )

    result = run_stage(stage="experiments", config_path=config_path, dry_run=False)

    assert result["status"] == "completed"
    assert "clinical_slim_logistic" in result["results"]
    assert "lipid_elastic_net" in result["results"]
    assert (tmp_path / "outputs" / "performance_summary.csv").exists()
    assert (tmp_path / "outputs" / "roc_curve_points.csv").exists()
    assert (tmp_path / "outputs" / "fold_metrics.csv").exists()
    assert (tmp_path / "outputs" / "feature_stability_summary.csv").exists()
    assert result["output_files"]["fold_metrics"].endswith("fold_metrics.csv")
    assert result["output_files"]["feature_stability_summary"].endswith("feature_stability_summary.csv")


def test_pipeline_followup_stage_runs_on_toy_csv_inputs(tmp_path):
    from run_pipeline import run_stage

    group = tmp_path / "group.csv"
    group.write_text(
        "ID,Group\n"
        "A001,noresponse\nA002,noresponse\nA003,noresponse\nA004,noresponse\nA005,noresponse\nA006,noresponse\n"
        "B001,response\nB002,response\nB003,response\nB004,response\nB005,response\nB006,response\n",
        encoding="utf-8",
    )
    lipid = tmp_path / "lipid.csv"
    lipid.write_text(
        "NAME,lipid_signal,lipid_shadow\n"
        "A001,0.1,0.11\nA002,0.1,0.11\nA003,0.1,0.11\nA004,0.1,0.11\nA005,0.1,0.11\nA006,0.1,0.11\n"
        "B001,10.0,10.1\nB002,10.0,10.1\nB003,10.0,10.1\nB004,10.0,10.1\nB005,10.0,10.1\nB006,10.0,10.1\n",
        encoding="utf-8",
    )
    clinical_slim = tmp_path / "clinical_slim.csv"
    clinical_slim.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI\n"
        "A001,10,1.0,3.0,0,20\nA002,10,1.0,3.0,1,20\nA003,10,1.0,3.0,0,20\nA004,10,1.0,3.0,1,20\nA005,10,1.0,3.0,0,20\nA006,10,1.0,3.0,1,20\n"
        "B001,10,3.0,1.0,0,28\nB002,10,3.0,1.0,1,28\nB003,10,3.0,1.0,0,28\nB004,10,3.0,1.0,1,28\nB005,10,3.0,1.0,0,28\nB006,10,3.0,1.0,1,28\n",
        encoding="utf-8",
    )
    clinical_full = tmp_path / "clinical_full.csv"
    clinical_full.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10,1.0,3.0,0,20,1.0\nA002,10,1.0,3.0,1,20,1.0\nA003,10,1.0,3.0,0,20,1.0\nA004,10,1.0,3.0,1,20,1.0\nA005,10,1.0,3.0,0,20,1.0\nA006,10,1.0,3.0,1,20,1.0\n"
        "B001,10,3.0,1.0,0,28,3.0\nB002,10,3.0,1.0,1,28,3.0\nB003,10,3.0,1.0,0,28,3.0\nB004,10,3.0,1.0,1,28,3.0\nB005,10,3.0,1.0,0,28,3.0\nB006,10,3.0,1.0,1,28,3.0\n",
        encoding="utf-8",
    )
    note = tmp_path / "discussion.txt"
    note.write_text("当前分组来自ΔBMI百分位变化讨论。", encoding="utf-8")
    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: toy_pipeline",
                "paths:",
                f"  group: {group}",
                f"  lipid: {lipid}",
                f"  clinical_full: {clinical_full}",
                f"  clinical_slim: {clinical_slim}",
                "followup:",
                f"  output_dir: {tmp_path / 'followup_outputs'}",
                f"  strict_outputs_dir: {tmp_path / 'strict_outputs'}",
                "  models:",
                "    - model_label: clinical_baseline_main",
                "      experiment: clinical_slim_logistic",
                "      cv_overrides: {}",
                "  discussion_paths:",
                f"    - {note}",
                "  alternative_grouping:",
                "    endpoint_source:",
                "    endpoint_value_column:",
                "    gray_zone_rule:",
                "  self_validation:",
                "    random_holdout_splits: 2",
                "    test_size: 0.25",
                "    random_state: 11",
                "    pseudo_external:",
                "      enabled: true",
                "      group_by: id_prefix",
                "    cv_config:",
                "      outer_splits: 3",
                "      outer_repeats: 1",
                "      inner_splits: 2",
                "      random_state: 42",
                "      lipid_top_k: 2",
                "      clinical_top_k: 5",
                "      correlation_threshold: 0.95",
                "      clinical_missing_threshold: 0.2",
            ]
        ),
        encoding="utf-8",
    )

    strict_output_dir = tmp_path / "strict_outputs"
    strict_output_dir.mkdir()
    (strict_output_dir / "performance_summary.csv").write_text(
        "experiment,mean_auc,std_auc,mean_train_auc,n_outer_folds\nclinical_slim_logistic,0.53,0.06,0.60,5\n",
        encoding="utf-8",
    )

    result = run_stage(stage="followup", config_path=config_path, dry_run=False)

    assert result["status"] == "completed"
    assert (tmp_path / "followup_outputs" / "group_definition_audit.md").exists()
    assert (tmp_path / "followup_outputs" / "baseline_balance_summary.csv").exists()
    assert (tmp_path / "followup_outputs" / "self_validation_summary.csv").exists()
    assert (tmp_path / "followup_outputs" / "self_validation_fold_metrics.csv").exists()
    assert (tmp_path / "followup_outputs" / "small_model_followup_comparison.csv").exists()
    assert (tmp_path / "followup_outputs" / "followup_summary.md").exists()
    assert (tmp_path / "followup_outputs" / "blocked_items.md").exists()
    assert (tmp_path / "followup_outputs" / "FigureF1_Followup_ModelPerformance.png").exists()
    assert (tmp_path / "followup_outputs" / "FigureF2_Followup_GeneralizationGap.png").exists()
    assert (tmp_path / "followup_outputs" / "FigureF3_SelfValidation_Distribution.png").exists()
    assert (tmp_path / "followup_outputs" / "FigureF4_GroupAudit.png").exists()
    assert (tmp_path / "followup_outputs" / "followup_plan_alignment.md").exists()
    assert result["output_files"]["followup_summary"].endswith("followup_summary.md")
    assert result["output_files"]["followup_figure_model_performance_png"].endswith(
        "FigureF1_Followup_ModelPerformance.png"
    )
    assert result["output_files"]["followup_figure_generalization_gap_png"].endswith(
        "FigureF2_Followup_GeneralizationGap.png"
    )
    assert result["output_files"]["followup_figure_self_validation_distribution_png"].endswith(
        "FigureF3_SelfValidation_Distribution.png"
    )
    assert result["output_files"]["followup_figure_group_audit_png"].endswith("FigureF4_GroupAudit.png")
    assert result["output_files"]["followup_alignment_note"].endswith("followup_plan_alignment.md")


def test_pipeline_followup_stage_runs_outphase_validation_when_paths_are_provided(tmp_path):
    from run_pipeline import run_stage

    group = tmp_path / "group.csv"
    group.write_text(
        "ID,Group\n"
        "A001,response\nA002,response\nA003,noresponse\n"
        "B001,response\nB002,response\nC001,noresponse\n",
        encoding="utf-8",
    )
    lipid = tmp_path / "lipid.csv"
    lipid.write_text(
        "NAME,lipid_signal,lipid_shadow\n"
        "A001,10.0,9.9\nA002,10.2,10.0\nA003,0.1,0.2\n"
        "B001,9.8,9.7\nB002,10.1,10.3\nC001,0.2,0.1\n",
        encoding="utf-8",
    )
    clinical_slim = tmp_path / "clinical_slim.csv"
    clinical_slim.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI\n"
        "A001,10,3.0,1.0,0,28\nA002,10,3.1,1.1,1,29\nA003,10,1.0,3.0,0,20\n"
        "B001,11,2.9,1.1,1,27.5\nB002,11,3.2,1.0,0,28.5\nC001,11,1.1,3.1,1,21\n",
        encoding="utf-8",
    )
    clinical_full = tmp_path / "clinical_full.csv"
    clinical_full.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10,3.0,1.0,0,28,3.0\nA002,10,3.1,1.1,1,29,3.1\nA003,10,1.0,3.0,0,20,1.0\n"
        "B001,11,2.9,1.1,1,27.5,3.2\nB002,11,3.2,1.0,0,28.5,3.0\nC001,11,1.1,3.1,1,21,1.1\n",
        encoding="utf-8",
    )
    out_lipid = tmp_path / "out_lipid.csv"
    out_lipid.write_text(
        "NAME,Group,lipid_signal,lipid_shadow\n"
        "A001,noresponse,9.7,9.8\nA002,noresponse,9.9,9.9\nA003,response,0.3,0.4\n"
        "B001,noresponse,9.5,9.4\nB002,noresponse,9.8,10.0\nC001,response,0.4,0.3\n",
        encoding="utf-8",
    )
    out_clinical = tmp_path / "out_clinical.csv"
    out_clinical.write_text(
        "ID,age_out,bmi_z_out,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10.2,2.8,1.2,0,27.5,2.9\nA002,10.1,3.0,1.1,1,28.6,3.0\nA003,10.0,1.1,2.8,0,20.2,1.2\n"
        "B001,11.2,2.7,1.2,1,27.0,3.0\nB002,11.1,3.1,1.0,0,28.1,3.1\nC001,11.0,1.0,3.0,1,21.1,1.0\n",
        encoding="utf-8",
    )
    note = tmp_path / "discussion.txt"
    note.write_text("out 的数据是不是也可以做验证。", encoding="utf-8")

    strict_output_dir = tmp_path / "strict_outputs"
    strict_output_dir.mkdir()
    (strict_output_dir / "performance_summary.csv").write_text(
        "\n".join(
            [
                "experiment,mean_auc,std_auc,mean_train_auc,n_outer_folds",
                "clinical_slim_logistic,0.53,0.06,0.60,5",
                "lipid_elastic_net,0.54,0.05,0.78,5",
                "fusion_elastic_net,0.56,0.06,0.80,5",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: toy_pipeline",
                "paths:",
                f"  group: {group}",
                f"  lipid: {lipid}",
                f"  clinical_full: {clinical_full}",
                f"  clinical_slim: {clinical_slim}",
                "followup:",
                f"  output_dir: {tmp_path / 'followup_outputs'}",
                f"  strict_outputs_dir: {strict_output_dir}",
                "  models:",
                "    - model_label: clinical_baseline_main",
                "      experiment: clinical_slim_logistic",
                "      cv_overrides: {}",
                "  discussion_paths:",
                f"    - {note}",
                "  alternative_grouping:",
                "    endpoint_source:",
                "    endpoint_value_column:",
                "    gray_zone_rule:",
                "  self_validation:",
                "    random_holdout_splits: 2",
                "    test_size: 0.25",
                "    random_state: 11",
                "    pseudo_external:",
                "      enabled: true",
                "      group_by: id_prefix",
                "    cv_config:",
                "      outer_splits: 3",
                "      outer_repeats: 1",
                "      inner_splits: 2",
                "      random_state: 42",
                "      lipid_top_k: 2",
                "      clinical_top_k: 5",
                "      correlation_threshold: 0.95",
                "      clinical_missing_threshold: 0.2",
                "  outphase_validation:",
                "    enabled: true",
                f"    out_lipid_path: {out_lipid}",
                f"    out_clinical_full_path: {out_clinical}",
                "    clinical_anchor_mapping:",
                "      age_enroll: age_out",
                "      bmi_z_enroll: bmi_z_out",
                "      SFT: SFT",
                "      Gender: Gender",
                "      BMI: BMI",
                "    random_holdout_splits: 2",
                "    test_size: 0.33",
                "    random_state: 7",
                "    pseudo_external:",
                "      enabled: true",
                "      group_by: id_prefix",
                "    cv_config:",
                "      outer_splits: 3",
                "      outer_repeats: 1",
                "      inner_splits: 2",
                "      random_state: 42",
                "      lipid_top_k: 2",
                "      clinical_top_k: 5",
                "      correlation_threshold: 0.95",
                "      clinical_missing_threshold: 0.2",
            ]
        ),
        encoding="utf-8",
    )

    result = run_stage(stage="followup", config_path=config_path, dry_run=False)

    assert result["status"] == "completed"
    assert (tmp_path / "followup_outputs" / "outphase_validation_summary.csv").exists()
    assert (tmp_path / "followup_outputs" / "outphase_validation_fold_metrics.csv").exists()
    assert (tmp_path / "followup_outputs" / "outphase_validation.md").exists()
    assert (tmp_path / "followup_outputs" / "FigureF5_OutPhase_ModelPerformance.png").exists()
    assert (tmp_path / "followup_outputs" / "FigureF6_OutPhase_Distribution.png").exists()
    blocked_text = (tmp_path / "followup_outputs" / "blocked_items.md").read_text(encoding="utf-8")
    assert "缺少出组/干预后同批数据表" not in blocked_text
    assert result["output_files"]["outphase_validation_summary"].endswith("outphase_validation_summary.csv")



def test_pipeline_followup_stage_exports_school_split_outputs(tmp_path):
    from run_pipeline import run_stage

    group = tmp_path / "group.csv"
    group.write_text(
        "ID,Group\n"
        "A001,response\nA002,response\nA003,noresponse\n"
        "B001,response\nB002,response\nC001,noresponse\n",
        encoding="utf-8",
    )
    lipid = tmp_path / "lipid.csv"
    lipid.write_text(
        "NAME,lipid_signal,lipid_shadow\n"
        "A001,10.0,9.9\nA002,10.2,10.0\nA003,0.1,0.2\n"
        "B001,9.8,9.7\nB002,10.1,10.3\nC001,0.2,0.1\n",
        encoding="utf-8",
    )
    clinical_slim = tmp_path / "clinical_slim.csv"
    clinical_slim.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI\n"
        "A001,10,3.0,1.0,0,28\nA002,10,3.1,1.1,1,29\nA003,10,1.0,3.0,0,20\n"
        "B001,11,2.9,1.1,1,27.5\nB002,11,3.2,1.0,0,28.5\nC001,11,1.1,3.1,1,21\n",
        encoding="utf-8",
    )
    clinical_full = tmp_path / "clinical_full.csv"
    clinical_full.write_text(
        "ID,age_enroll,bmi_z_enroll,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10,3.0,1.0,0,28,3.0\nA002,10,3.1,1.1,1,29,3.1\nA003,10,1.0,3.0,0,20,1.0\n"
        "B001,11,2.9,1.1,1,27.5,3.2\nB002,11,3.2,1.0,0,28.5,3.0\nC001,11,1.1,3.1,1,21,1.1\n",
        encoding="utf-8",
    )
    out_lipid = tmp_path / "out_lipid.csv"
    out_lipid.write_text(
        "NAME,Group,lipid_signal,lipid_shadow\n"
        "A001,noresponse,9.7,9.8\nA002,noresponse,9.9,9.9\nA003,response,0.3,0.4\n"
        "B001,noresponse,9.5,9.4\nB002,noresponse,9.8,10.0\nC001,response,0.4,0.3\n",
        encoding="utf-8",
    )
    out_clinical = tmp_path / "out_clinical.csv"
    out_clinical.write_text(
        "ID,age_out,bmi_z_out,SFT,Gender,BMI,whole_blood_LYMPH_count\n"
        "A001,10.2,2.8,1.2,0,27.5,2.9\nA002,10.1,3.0,1.1,1,28.6,3.0\nA003,10.0,1.1,2.8,0,20.2,1.2\n"
        "B001,11.2,2.7,1.2,1,27.0,3.0\nB002,11.1,3.1,1.0,0,28.1,3.1\nC001,11.0,1.0,3.0,1,21.1,1.0\n",
        encoding="utf-8",
    )
    note = tmp_path / "discussion.txt"
    note.write_text("可以考虑用不同学校的同学分开，作为测试和训练集。", encoding="utf-8")

    mapping_path = tmp_path / "mapping.xlsx"
    mapping = pd.DataFrame(
        {
            "school": ["百旺", "百旺", "本部", "本部", "华清校区", "华清校区"],
            "ID": ["A001", "A002", "A003", "B001", "B002", "C001"],
            "intensity": [
                "Intermittent vigorous",
                "Intermittent vigorous",
                "Low-intensity",
                "Low-intensity",
                "Intermittent vigorous",
                "Intermittent vigorous",
            ],
        }
    )
    with pd.ExcelWriter(mapping_path, engine="openpyxl") as writer:
        mapping.to_excel(writer, sheet_name="运动强度分组_401人", index=False)

    strict_output_dir = tmp_path / "strict_outputs"
    strict_output_dir.mkdir()
    (strict_output_dir / "performance_summary.csv").write_text(
        "\n".join(
            [
                "experiment,mean_auc,std_auc,mean_train_auc,n_outer_folds",
                "clinical_slim_logistic,0.53,0.06,0.60,5",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(
        "\n".join(
            [
                "project_name: toy_pipeline",
                "paths:",
                f"  group: {group}",
                f"  lipid: {lipid}",
                f"  clinical_full: {clinical_full}",
                f"  clinical_slim: {clinical_slim}",
                "followup:",
                f"  output_dir: {tmp_path / 'followup_outputs'}",
                f"  strict_outputs_dir: {strict_output_dir}",
                "  models:",
                "    - model_label: clinical_baseline_main",
                "      experiment: clinical_slim_logistic",
                "      cv_overrides: {}",
                "  discussion_paths:",
                f"    - {note}",
                "  alternative_grouping:",
                "    endpoint_source:",
                "    endpoint_value_column:",
                "    gray_zone_rule:",
                "  self_validation:",
                "    random_holdout_splits: 2",
                "    test_size: 0.25",
                "    random_state: 11",
                "    pseudo_external:",
                "      enabled: true",
                "      group_by: school",
                f"      mapping_path: {mapping_path}",
                "      mapping_sheet_name: 运动强度分组_401人",
                "    cv_config:",
                "      outer_splits: 3",
                "      outer_repeats: 1",
                "      inner_splits: 2",
                "      random_state: 42",
                "      lipid_top_k: 2",
                "      clinical_top_k: 5",
                "      correlation_threshold: 0.95",
                "      clinical_missing_threshold: 0.2",
                "  outphase_validation:",
                "    enabled: true",
                f"    out_lipid_path: {out_lipid}",
                f"    out_clinical_full_path: {out_clinical}",
                "    clinical_anchor_mapping:",
                "      age_enroll: age_out",
                "      bmi_z_enroll: bmi_z_out",
                "      SFT: SFT",
                "      Gender: Gender",
                "      BMI: BMI",
                "    random_holdout_splits: 2",
                "    test_size: 0.33",
                "    random_state: 7",
                "    pseudo_external:",
                "      enabled: true",
                "      group_by: school",
                f"      mapping_path: {mapping_path}",
                "      mapping_sheet_name: 运动强度分组_401人",
                "    cv_config:",
                "      outer_splits: 3",
                "      outer_repeats: 1",
                "      inner_splits: 2",
                "      random_state: 42",
                "      lipid_top_k: 2",
                "      clinical_top_k: 5",
                "      correlation_threshold: 0.95",
                "      clinical_missing_threshold: 0.2",
            ]
        ),
        encoding="utf-8",
    )

    result = run_stage(stage="followup", config_path=config_path, dry_run=False)

    followup_dir = tmp_path / "followup_outputs"
    assert result["status"] == "completed"
    assert (followup_dir / "id_school_intensity_mapping.csv").exists()
    assert (followup_dir / "school_group_holdout_summary.csv").exists()
    school_summary = pd.read_csv(followup_dir / "school_group_holdout_summary.csv")
    assert set(school_summary["holdout_group"]) == {"百旺", "本部", "华清校区"}
    text = (followup_dir / "followup_summary.md").read_text(encoding="utf-8")
    assert "真实 school grouped split" in text
    assert "不能把旧的 leave-one-prefix-out 改名" in text
