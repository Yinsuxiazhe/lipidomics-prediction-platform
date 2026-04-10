"""
Phase 1: Data preparation for multi-indicator lipidomics prediction.
GLM5 execution — 2026-04-10

Computes delta (outroll - enroll) for 8 weight-loss indicators,
generates quartile/tertile labels, splits gender IDs, produces baseline stats.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
ENROLL  = PROJECT / "287_enroll_data_clean.csv"
OUTROLL = PROJECT / "287_outroll_data_clean.csv"
LIPID   = PROJECT / "281_merge_lipids_enroll.csv"
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"

# ── confirmed indicators (Zhang Shuxian, 2026-04-10) ───────────────────
INDICATORS = {
    "BMI":       ("BMI",    "BMI"),
    "weight":    ("weight", "weight"),
    "bmi_z":     ("bmi_z_enroll", "bmi_z_out"),
    "waistline": ("waistline", "waistline"),
    "hipline":   ("hipline", "hipline"),
    "WHR":       ("WHR",    "WHR"),
    "PBF":       ("Inbody_39_PBF_.Percent_Body_Fat.", "Inbody_39_PBF_.Percent_Body_Fat."),
    "PSM":       ("Inbody_PSM_.Percent_Skeletal_Muscle_Mass.", "Inbody_PSM_.Percent_Skeletal_Muscle_Mass."),
}


def load_data():
    """Load and align enroll, outroll, lipid data by ID."""
    enroll  = pd.read_csv(ENROLL)
    outroll = pd.read_csv(OUTROLL)
    lipid   = pd.read_csv(LIPID)
    return enroll, outroll, lipid


def compute_deltas(enroll: pd.DataFrame, outroll: pd.DataFrame) -> pd.DataFrame:
    """Compute absolute delta (outroll - enroll) for each indicator."""
    rows = []
    for label, (col_e, col_o) in INDICATORS.items():
        e = pd.to_numeric(enroll[col_e], errors="coerce")
        o = pd.to_numeric(outroll[col_o], errors="coerce")
        delta = o - e
        rows.append(delta.rename(label))
    df = pd.concat(rows, axis=1)
    df.insert(0, "ID", enroll["ID"].values)
    return df


def make_labels(delta_df: pd.DataFrame) -> pd.DataFrame:
    """Generate quartile (Q1 vs Q4) and tertile (T1 vs T3) binary labels.

    Returns DataFrame with columns like 'BMI_Q', 'BMI_T' etc.
    Values: 1 = top extreme (largest delta), 0 = bottom extreme (smallest delta), NaN = middle.
    """
    records = {}
    for col in INDICATORS:
        vals = delta_df[col]
        # Quartile: Q1 (bottom 25%) = 0, Q4 (top 25%) = 1
        q25 = vals.quantile(0.25)
        q75 = vals.quantile(0.75)
        q_label = pd.Series(np.nan, index=delta_df.index, name=f"{col}_Q")
        q_label[vals <= q25] = 0
        q_label[vals > q75] = 1
        records[f"{col}_Q"] = q_label

        # Tertile: T1 (bottom 33%) = 0, T3 (top 33%) = 1
        t33 = vals.quantile(0.333)
        t67 = vals.quantile(0.667)
        t_label = pd.Series(np.nan, index=delta_df.index, name=f"{col}_T")
        t_label[vals <= t33] = 0
        t_label[vals > t67] = 1
        records[f"{col}_T"] = t_label

    labels = pd.DataFrame(records)
    labels.insert(0, "ID", delta_df["ID"].values)
    return labels


def split_gender(enroll: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split IDs by gender. Gender=0 → Male, Gender=1 → Female."""
    male_ids   = enroll.loc[enroll["Gender"] == 0, ["ID"]].copy()
    female_ids = enroll.loc[enroll["Gender"] == 1, ["ID"]].copy()
    male_ids["gender"] = "male"
    female_ids["gender"] = "female"
    return male_ids, female_ids


def baseline_stats(
    delta_df: pd.DataFrame,
    labels: pd.DataFrame,
    enroll: pd.DataFrame,
    lipid_ids: set,
) -> pd.DataFrame:
    """Compute baseline descriptive statistics (mean ± sd) for each indicator, overall and by gender."""
    lipid_ids_str = lipid_ids
    mask = delta_df["ID"].astype(str).isin(lipid_ids_str)
    d = delta_df.loc[mask].copy()
    gender_map = enroll.set_index("ID")["Gender"].map({0: "male", 1: "female"}).to_dict()
    d["gender"] = d["ID"].astype(str).map(gender_map)

    # Merge labels into d for easy counting
    label_cols = [c for c in labels.columns if c != "ID"]
    d = d.merge(labels[["ID"] + label_cols], on="ID", how="left")

    rows = []
    for col in INDICATORS:
        for group_name, subset in [("all", d), ("male", d[d["gender"] == "male"]), ("female", d[d["gender"] == "female"])]:
            v = subset[col].dropna()
            n_total = len(subset)
            n_valid = len(v)
            q_col = f"{col}_Q"
            t_col = f"{col}_T"
            n_q1 = int((subset[q_col] == 0).sum()) if q_col in subset.columns else 0
            n_q4 = int((subset[q_col] == 1).sum()) if q_col in subset.columns else 0
            n_t1 = int((subset[t_col] == 0).sum()) if t_col in subset.columns else 0
            n_t3 = int((subset[t_col] == 1).sum()) if t_col in subset.columns else 0
            rows.append({
                "indicator": col,
                "group": group_name,
                "n_total": n_total,
                "n_valid": n_valid,
                "delta_mean": v.mean(),
                "delta_std": v.std(),
                "delta_min": v.min(),
                "delta_max": v.max(),
                "n_quartile_Q1": n_q1,
                "n_quartile_Q4": n_q4,
                "n_tertile_T1": n_t1,
                "n_tertile_T3": n_t3,
            })
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 1: Data Preparation  [GLM5]")
    print("=" * 60)

    # Load
    print("\n[1/5] Loading data ...")
    enroll, outroll, lipid = load_data()
    print(f"  enroll:  {enroll.shape}")
    print(f"  outroll: {outroll.shape}")
    print(f"  lipid:   {lipid.shape}")

    # Deltas
    print("\n[2/5] Computing deltas (8 indicators) ...")
    delta_df = compute_deltas(enroll, outroll)
    for col in INDICATORS:
        v = delta_df[col].dropna()
        print(f"  {col:12s}  n={len(v):3d}  mean={v.mean():+.3f}  std={v.std():.3f}")
    delta_df.to_csv(OUT_DIR / "phase1_delta_matrix.csv", index=False)
    print(f"  → saved: phase1_delta_matrix.csv")

    # Labels
    print("\n[3/5] Generating quartile/tertile labels ...")
    labels = make_labels(delta_df)
    for col in INDICATORS:
        q0 = (labels[f"{col}_Q"] == 0).sum()
        q1 = (labels[f"{col}_Q"] == 1).sum()
        t0 = (labels[f"{col}_T"] == 0).sum()
        t1 = (labels[f"{col}_T"] == 1).sum()
        print(f"  {col:12s}  Q1={q0} Q4={q1}  T1={t0} T3={t1}")
    labels.to_csv(OUT_DIR / "phase1_labels.csv", index=False)
    print(f"  → saved: phase1_labels.csv")

    # Gender split
    print("\n[4/5] Splitting gender IDs ...")
    male_ids, female_ids = split_gender(enroll)
    lipid_ids = set(lipid["NAME"].astype(str))
    male_ids   = male_ids[male_ids["ID"].astype(str).isin(lipid_ids)]
    female_ids = female_ids[female_ids["ID"].astype(str).isin(lipid_ids)]
    male_ids.to_csv(OUT_DIR / "ids_male.csv", index=False)
    female_ids.to_csv(OUT_DIR / "ids_female.csv", index=False)
    print(f"  male:   {len(male_ids)} subjects (with lipid data)")
    print(f"  female: {len(female_ids)} subjects (with lipid data)")

    # Baseline stats
    print("\n[5/5] Baseline statistics ...")
    stats = baseline_stats(delta_df, labels, enroll, lipid_ids)
    stats.to_csv(OUT_DIR / "phase1_baseline_stats.csv", index=False)
    print(f"  → saved: phase1_baseline_stats.csv")
    print("\nSummary (all subjects with lipid data):")
    all_stats = stats[stats["group"] == "all"].set_index("indicator")
    for col in INDICATORS:
        s = all_stats.loc[col]
        print(f"  {col:12s}  n={int(s['n_valid']):3d}  Δ={s['delta_mean']:+.3f}±{s['delta_std']:.3f}  Q1={int(s['n_quartile_Q1'])} Q4={int(s['n_quartile_Q4'])}  T1={int(s['n_tertile_T1'])} T3={int(s['n_tertile_T3'])}")

    # Merge lipid features with delta for downstream use
    print("\n[Bonus] Merging lipid + delta for downstream ...")
    lipid_ids_int = lipid["NAME"].values
    delta_with_lipid = delta_df[delta_df["ID"].isin(lipid_ids_int)].copy()
    delta_with_lipid.to_csv(OUT_DIR / "phase1_delta_with_lipid_ids.csv", index=False)
    print(f"  {len(delta_with_lipid)} subjects ready for modeling")

    print("\n" + "=" * 60)
    print("Phase 1 complete. [GLM5]")
    print(f"Output: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
