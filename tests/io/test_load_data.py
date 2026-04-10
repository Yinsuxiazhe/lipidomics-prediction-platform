def test_load_project_tables_standardizes_key_ids(tmp_path):
    from src.io.load_data import load_project_tables

    group = tmp_path / "group.csv"
    group.write_text("ID,Group\nA001,response\n", encoding="utf-8")

    lipid = tmp_path / "lipid.csv"
    lipid.write_text("NAME,L1\nA001,1.0\n", encoding="utf-8")

    clinical_full = tmp_path / "clinical_full.csv"
    clinical_full.write_text("ID,age_enroll\nA001,10\n", encoding="utf-8")

    clinical_slim = tmp_path / "clinical_slim.csv"
    clinical_slim.write_text("ID,age_enroll\nA001,10\n", encoding="utf-8")

    data = load_project_tables(
        group_path=group,
        lipid_path=lipid,
        clinical_full_path=clinical_full,
        clinical_slim_path=clinical_slim,
    )

    assert list(data.group.columns) == ["ID", "Group"]
    assert data.group["ID"].dtype == object
    assert data.lipid["NAME"].dtype == object
    assert data.clinical_full["ID"].dtype == object
    assert data.clinical_slim["ID"].dtype == object
