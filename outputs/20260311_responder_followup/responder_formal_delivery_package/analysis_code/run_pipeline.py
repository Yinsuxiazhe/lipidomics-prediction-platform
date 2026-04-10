from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from src.data.build_cohort import build_analysis_cohorts
from src.followup.run_followup import run_followup_analysis
from src.io.load_data import load_project_tables
from src.models.run_nested_cv import run_experiments
from src.reports.make_figures import write_roc_outputs
from src.reports.make_tables import write_experiment_tables


ALLOWED_STAGES = ("validate", "cohort", "experiments", "followup")


def load_pipeline_config(config_path: str | Path) -> dict[str, Any]:
    with Path(config_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def run_stage(
    stage: str,
    config_path: str | Path = "config/analysis.yaml",
    dry_run: bool = False,
) -> dict[str, Any]:
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"Unsupported stage: {stage}")

    config = load_pipeline_config(config_path)
    if dry_run:
        return {
            "project_name": config.get("project_name", "unknown"),
            "stage": stage,
            "status": "dry_run",
            "paths": config.get("paths", {}),
        }

    paths = config.get("paths", {})
    raw_tables = load_project_tables(
        group_path=paths["group"],
        lipid_path=paths["lipid"],
        clinical_full_path=paths["clinical_full"],
        clinical_slim_path=paths["clinical_slim"],
    )

    if stage == "validate":
        return {
            "project_name": config.get("project_name", "unknown"),
            "stage": stage,
            "status": "completed",
            "raw_shapes": {
                "group": raw_tables.group.shape,
                "lipid": raw_tables.lipid.shape,
                "clinical_full": raw_tables.clinical_full.shape,
                "clinical_slim": raw_tables.clinical_slim.shape,
            },
        }

    cohorts = build_analysis_cohorts(raw_tables)
    if stage == "cohort":
        return {
            "project_name": config.get("project_name", "unknown"),
            "stage": stage,
            "status": "completed",
            "summary": cohorts.summary,
        }

    if stage == "followup":
        result = run_followup_analysis(
            raw_tables=raw_tables,
            cohorts=cohorts,
            followup_config=config.get("followup", {}),
            positive_label=config.get("target", {}).get("positive_label", "response"),
        )
        return {
            "project_name": config.get("project_name", "unknown"),
            "stage": stage,
            **result,
        }

    if stage == "experiments":
        experiments_cfg = config.get("experiments", {})
        results = run_experiments(
            cohorts=cohorts,
            requested_experiments=experiments_cfg.get("requested"),
            dry_run=False,
            cv_config=experiments_cfg.get("cv_config"),
            positive_label=config.get("target", {}).get("positive_label", "response"),
        )
        output_cfg = config.get("outputs", {})
        if output_cfg.get("base_dir"):
            table_outputs = write_experiment_tables(results, output_cfg["base_dir"])
            figure_outputs = write_roc_outputs(results, output_cfg["base_dir"])
            results["output_files"] = {**table_outputs, **figure_outputs}
        return results

    return {
        "project_name": config.get("project_name", "unknown"),
        "stage": stage,
        "status": "not_implemented_yet",
        "paths": config.get("paths", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lipidomics prediction pipeline stages.")
    parser.add_argument("--config", default="config/analysis.yaml", help="Path to YAML config file.")
    parser.add_argument("--stage", default="validate", choices=ALLOWED_STAGES, help="Stage to run.")
    parser.add_argument("--dry-run", action="store_true", help="Only build a stage manifest.")
    args = parser.parse_args()

    manifest = run_stage(stage=args.stage, config_path=args.config, dry_run=args.dry_run)
    print(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
