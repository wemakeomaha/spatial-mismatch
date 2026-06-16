from __future__ import annotations

import json
import os
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from _common import DATA_PROCESSED, DATA_RAW, OUTPUT_CSV, OUTPUTS, PROJECT_ROOT, ensure_dirs, load_project_env, read_json


ACS_REPORT_FIELDS = [
    "median_rent",
    "median_household_income",
    "affordable_rent_estimate",
    "vehicle_households_total",
    "households_without_vehicles",
    "no_vehicle_share",
    "poverty_universe",
    "population_below_poverty",
    "poverty_rate",
    "civilian_labor_force",
    "unemployed_population",
    "unemployment_rate",
    "race_ethnicity_total",
    "nh_white_population",
    "nh_black_population",
    "nh_native_population",
    "nh_asian_population",
    "nh_pacific_population",
    "nh_other_population",
    "nh_two_or_more_population",
    "hispanic_population",
    "nh_white_share",
    "nh_black_share",
    "nh_native_share",
    "nh_asian_share",
    "nh_pacific_share",
    "nh_other_share",
    "nh_two_or_more_share",
    "hispanic_share",
    "people_of_color_share",
    "education_25plus_total",
    "hs_plus_population",
    "bachelors_plus_population",
    "hs_plus_share",
    "bachelors_plus_share",
    "rent_burden_universe",
    "rent_burdened_households",
    "rent_burden_rate",
]


def pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.1f}%"


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return "_No records._\n"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body]) + "\n"


def file_status(path: Path) -> str:
    if path.exists():
        return f"present ({path.stat().st_size:,} bytes)"
    return "missing"


def gtfs_diagnostics() -> tuple[str, list[dict]]:
    gtfs_path = DATA_RAW / "omaha_gtfs.zip"
    if not gtfs_path.exists():
        return "GTFS unavailable - no `data_raw/omaha_gtfs.zip` file.", []
    rows = []
    try:
        with ZipFile(gtfs_path) as zf:
            names = set(zf.namelist())
            for filename in ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt", "calendar_dates.txt"]:
                if filename not in names:
                    rows.append({"file": filename, "status": "missing", "records": "n/a"})
                    continue
                with zf.open(filename) as raw:
                    count = max(0, sum(1 for _ in raw) - 1)
                rows.append({"file": filename, "status": "present", "records": f"{count:,}"})
        return "GTFS zip found and inspected.", rows
    except Exception as exc:
        return f"GTFS zip could not be inspected: {type(exc).__name__}: {exc}", rows


def main() -> None:
    ensure_dirs()
    load_project_env()

    tracts = read_json(DATA_PROCESSED / "tracts_clean.geojson")
    tract_geoids = {str(feature.get("properties", {}).get("GEOID")) for feature in tracts.get("features", [])}
    tract_count = len(tract_geoids)

    acs_path = DATA_PROCESSED / "acs_housing_income.csv"
    acs = pd.read_csv(acs_path, dtype={"GEOID": str}) if acs_path.exists() else pd.DataFrame(columns=["GEOID"])
    acs_geoids = set(acs["GEOID"].dropna().astype(str)) if "GEOID" in acs.columns else set()
    matched_geoids = tract_geoids & acs_geoids
    missing_from_acs = sorted(tract_geoids - acs_geoids)
    extra_acs_geoids = sorted(acs_geoids - tract_geoids)

    table_path = OUTPUT_CSV / "tract_mismatch_table.csv"
    table = pd.read_csv(table_path, dtype={"GEOID": str}) if table_path.exists() else pd.DataFrame(columns=["GEOID"])

    completeness_rows = []
    joined_completeness_rows = []
    for field in ACS_REPORT_FIELDS:
        non_null = int(acs[field].notna().sum()) if field in acs.columns else 0
        completeness_rows.append(
            {
                "field": field,
                "non_null": non_null,
                "tracts": tract_count,
                "completeness": pct(non_null / tract_count * 100 if tract_count else float("nan")),
            }
        )
        joined_non_null = int(table[field].notna().sum()) if field in table.columns else 0
        joined_completeness_rows.append(
            {
                "field": field,
                "non_null_after_join": joined_non_null,
                "tracts": tract_count,
                "completeness": pct(joined_non_null / tract_count * 100 if tract_count else float("nan")),
            }
        )

    raw_files = [
        DATA_RAW / "download_manifest.json",
        DATA_RAW / "douglas_county_tracts_tigerweb.geojson",
        DATA_RAW / "ne_wac_S000_JT00.csv.gz",
        DATA_RAW / "ne_rac_S000_JT00.csv.gz",
        DATA_RAW / "ne_od_main_JT00.csv.gz",
        DATA_RAW / "omaha_gtfs.zip",
        DATA_PROCESSED / "tracts_clean.geojson",
        DATA_PROCESSED / "lehd_tract_metrics.csv",
        DATA_PROCESSED / "lehd_od_tract_flows.csv",
        DATA_PROCESSED / "acs_housing_income.csv",
    ]
    audit_rows = [{"dataset": str(path.relative_to(PROJECT_ROOT)), "status": file_status(path)} for path in raw_files]

    key_available = bool(os.getenv("CENSUS_API_KEY", "").strip())
    placeholder_path = DATA_RAW / "ACS_PLACEHOLDER.md"
    acs_placeholder_text = placeholder_path.read_text(encoding="utf-8") if placeholder_path.exists() else ""
    if len(acs) > 0:
        key_diagnostic = "ACS data present; latest ACS pull succeeded"
    elif "Invalid Key" in acs_placeholder_text:
        key_diagnostic = "provided but rejected by Census API as invalid"
    elif "Missing Key" in acs_placeholder_text:
        key_diagnostic = "missing according to Census API response"
    elif key_available:
        key_diagnostic = "provided"
    else:
        key_diagnostic = "not provided"
    acs_years = sorted(acs["acs_year"].dropna().astype(str).unique()) if "acs_year" in acs.columns else []
    min_completeness = min(
        [row["non_null"] / tract_count * 100 for row in completeness_rows if tract_count],
        default=float("nan"),
    )
    gtfs_status, gtfs_rows = gtfs_diagnostics()

    report = (
        "# Data Quality Report\n\n"
        "## Dataset Audit\n\n"
        + markdown_table(audit_rows, ["dataset", "status"])
        + "\n## ACS Diagnostics\n\n"
        f"- Census API key available to this run: {'yes' if key_available else 'no'}\n"
        f"- Census API key diagnostic: {key_diagnostic}\n"
        "- Census API key required in this environment: yes; without a key, the Census API returned a `Missing Key` response.\n"
        f"- ACS rows downloaded: {len(acs):,}\n"
        f"- ACS year(s): {', '.join(acs_years) if acs_years else 'none'}\n"
        f"- Tracts in boundary layer: {tract_count:,}\n"
        f"- ACS GEOIDs matched to tract layer: {len(matched_geoids):,}\n"
        f"- ACS GEOIDs missing from tract layer: {len(extra_acs_geoids):,}\n"
        f"- Tract GEOIDs missing from ACS table: {len(missing_from_acs):,}\n"
        f"- Minimum ACS field completeness: {pct(min_completeness)}\n"
        f"- Meets 95 percent completeness target: {'yes' if min_completeness >= 95 else 'no'}\n\n"
        "Previous ACS placeholders occurred because the Census API returned a `Missing Key` HTML response when no "
        "`CENSUS_API_KEY` was available. The workflow now reads `CENSUS_API_KEY` from the system environment or a local `.env` file. "
        "If the response is `Invalid Key`, the key must be corrected or activated before ACS fields can populate.\n\n"
        "## ACS Field Completeness Before Join\n\n"
        + markdown_table(completeness_rows, ["field", "non_null", "tracts", "completeness"])
        + "\n## ACS Field Completeness After Join\n\n"
        + markdown_table(joined_completeness_rows, ["field", "non_null_after_join", "tracts", "completeness"])
        + "\n## Join Diagnostics\n\n"
        f"- Boundary tract GEOID count: {tract_count:,}\n"
        f"- Processed ACS GEOID count: {len(acs_geoids):,}\n"
        f"- Matched GEOID count: {len(matched_geoids):,}\n"
        f"- Missing tract GEOIDs: {', '.join(missing_from_acs[:20]) if missing_from_acs else 'none'}"
        f"{' ...' if len(missing_from_acs) > 20 else ''}\n"
        f"- Extra ACS GEOIDs: {', '.join(extra_acs_geoids[:20]) if extra_acs_geoids else 'none'}"
        f"{' ...' if len(extra_acs_geoids) > 20 else ''}\n\n"
        "## GTFS Diagnostics\n\n"
        f"{gtfs_status}\n\n"
        + (markdown_table(gtfs_rows, ["file", "status", "records"]) if gtfs_rows else "")
        + "\n## Census API Key Setup\n\n"
        "1. Request a key at `https://api.census.gov/data/key_signup.html`.\n"
        "2. Open the Census confirmation email and activate the key if the email requires activation.\n"
        "3. Copy `.env.example` to `.env` in the project root:\n\n"
        "   ```powershell\n"
        "   Copy-Item .env.example .env\n"
        "   ```\n\n"
        "4. Edit `.env` so it contains:\n\n"
        "   ```text\n"
        "   CENSUS_API_KEY=your_real_key_here\n"
        "   ```\n\n"
        "5. Or set the key only for the current PowerShell session:\n\n"
        "   ```powershell\n"
        "   $env:CENSUS_API_KEY = \"your_real_key_here\"\n"
        "   python scripts/run_all.py\n"
        "   ```\n\n"
        "6. Do not commit `.env`; it is ignored by `.gitignore`.\n"
        "7. Rerun `python scripts/run_all.py` and re-check this report.\n"
    )

    (OUTPUTS / "data_quality_report.md").write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUTS / 'data_quality_report.md'}")


if __name__ == "__main__":
    main()
