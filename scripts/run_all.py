from __future__ import annotations

import runpy
from pathlib import Path


SCRIPTS = [
    "01_download_or_import_data.py",
    "02_clean_geographies.py",
    "03_process_lehd_jobs_workers.py",
    "04_process_acs_housing_income.py",
    "05_calculate_mismatch_metrics.py",
    "06_export_geojson_layers.py",
    "07_prepare_accessibility_placeholders.py",
    "08_generate_data_quality_report.py",
]


def main() -> None:
    scripts_dir = Path(__file__).resolve().parent
    for script in SCRIPTS:
        print(f"\n--- Running {script} ---")
        runpy.run_path(str(scripts_dir / script), run_name="__main__")


if __name__ == "__main__":
    main()
