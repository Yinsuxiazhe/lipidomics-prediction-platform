from pathlib import Path

import pandas as pd


def test_group_audit_reports_missing_endpoint_source_as_blocker(tmp_path):
    from src.followup.group_audit import run_group_audit
    from src.io.load_data import RawProjectTables

    raw = RawProjectTables(
        group=pd.DataFrame({"ID": ["A001", "A002"], "Group": ["response", "noresponse"]}),
        lipid=pd.DataFrame({"NAME": ["A001", "A002"], "lipid_signal": [1.0, 0.0]}),
        clinical_full=pd.DataFrame(
            {
                "ID": ["A001", "A002"],
                "age_enroll": [10, 11],
                "bmi_z_enroll": [2.0, 1.5],
                "SFT": [1.0, 2.0],
                "Gender": [0, 1],
                "BMI": [24.0, 22.0],
            }
        ),
        clinical_slim=pd.DataFrame(
            {
                "ID": ["A001", "A002"],
                "age_enroll": [10, 11],
                "bmi_z_enroll": [2.0, 1.5],
                "SFT": [1.0, 2.0],
                "Gender": [0, 1],
                "BMI": [24.0, 22.0],
            }
        ),
    )
    meeting_note = tmp_path / "meeting.txt"
    meeting_note.write_text("当前分组来源于ΔBMI百分位变化与灰区样本讨论。", encoding="utf-8")

    result = run_group_audit(
        raw_tables=raw,
        meeting_note_paths=[meeting_note],
        output_dir=tmp_path,
        alternative_grouping_config={
            "endpoint_source": None,
            "endpoint_value_column": None,
            "gray_zone_rule": None,
        },
    )

    blocked = Path(result["blocked_items_path"]).read_text(encoding="utf-8")
    audit = Path(result["group_definition_audit_markdown"]).read_text(encoding="utf-8")
    baseline_balance = pd.read_csv(result["baseline_balance_summary_csv"]) 

    assert "endpoint_source" in blocked
    assert "当前只完成可接入化" in blocked
    assert "不是原始真值表" in audit
    assert {"variable", "response_mean", "noresponse_mean", "standardized_mean_difference"}.issubset(
        baseline_balance.columns
    )
