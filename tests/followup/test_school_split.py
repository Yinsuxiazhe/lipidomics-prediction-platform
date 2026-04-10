from pathlib import Path

import pandas as pd


def _write_mapping_xlsx(path: Path) -> Path:
    mapping = pd.DataFrame(
        {
            "school": ["百旺", "本部", "百旺", "华清校区"],
            "ID": ["001", "002", "003", "004"],
            "intensity": [
                "Intermittent vigorous",
                "Low-intensity",
                "Intermittent vigorous",
                "Intermittent vigorous",
            ],
        }
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        mapping.to_excel(writer, sheet_name="运动强度分组_401人", index=False)
    return path


def test_load_school_mapping_normalizes_id_and_preserves_columns(tmp_path):
    from src.followup.school_split import load_school_mapping

    mapping_path = _write_mapping_xlsx(tmp_path / "mapping.xlsx")
    frame = load_school_mapping(mapping_path)

    assert list(frame.columns) == ["ID", "school", "intensity"]
    assert list(frame["ID"]) == ["001", "002", "003", "004"]
    assert set(frame["school"]) == {"百旺", "本部", "华清校区"}
    assert set(frame["intensity"]) == {"Intermittent vigorous", "Low-intensity"}


def test_resolve_group_series_supports_prefix_and_school(tmp_path):
    from src.followup.school_split import resolve_group_series

    mapping_path = _write_mapping_xlsx(tmp_path / "mapping.xlsx")
    frame = pd.DataFrame(
        {
            "ID": ["001", "002", "003", "004"],
            "Group": ["response", "noresponse", "response", "noresponse"],
        }
    )

    prefix_series, prefix_meta = resolve_group_series(frame, group_by="id_prefix")
    school_series, school_meta = resolve_group_series(
        frame,
        group_by="school",
        mapping_path=mapping_path,
        mapping_sheet_name="运动强度分组_401人",
    )

    assert list(prefix_series) == ["0", "0", "0", "0"]
    assert prefix_meta["validation_scheme"] == "leave_one_prefix_out"
    assert list(school_series) == ["百旺", "本部", "百旺", "华清校区"]
    assert school_meta["validation_scheme"] == "leave_one_school_out"
    assert school_meta["mapping_frame"].shape == (4, 3)


def test_resolve_fixed_group_split_supports_school_combo():
    from src.followup.school_split import resolve_fixed_group_split

    group_values = pd.Series(["百旺", "本部", "百旺", "华清校区"], dtype=object)
    group_meta = {
        "group_by": "school",
        "validation_scheme": "leave_one_school_out",
    }

    fixed_meta = resolve_fixed_group_split(
        group_values,
        group_meta=group_meta,
        fixed_group_split_config={
            "enabled": True,
            "test_groups": ["百旺", "本部"],
        },
    )

    assert fixed_meta is not None
    assert fixed_meta["validation_scheme"] == "fixed_school_combo_holdout"
    assert fixed_meta["test_groups"] == ["百旺", "本部"]
    assert fixed_meta["holdout_group_label"] == "百旺 + 本部"
