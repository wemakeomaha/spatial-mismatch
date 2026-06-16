# Opportunity and Spatial Mismatch Atlas for Omaha

Phase 1 planning/research prototype for **Opportunity and Affordability in Omaha: A Spatial Mismatch Analysis of Jobs, Wages, Housing, and Access**.

The project creates a reproducible census-tract workflow for Douglas County/Omaha and a local Leaflet atlas for exploring job access, wage opportunity, housing affordability, transportation access, and neighborhood equity context.

## Project Structure

```text
job-housing-mismatch-omaha/
  data_raw/
  data_processed/
  scripts/
    01_download_or_import_data.py
    02_clean_geographies.py
    03_process_lehd_jobs_workers.py
    04_process_acs_housing_income.py
    05_calculate_mismatch_metrics.py
    06_export_geojson_layers.py
    07_prepare_accessibility_placeholders.py
  dashboard/
  outputs/
    geojson/
    csv/
    maps/
    methods_note.md
    accessibility_placeholders.md
  README.md
```

## Data Sources

- Census tract boundaries: Census TIGERweb for Douglas County, Nebraska.
- Workplace jobs: LEHD/LODES WAC, rolled from blocks to tracts.
- Resident workers: LEHD/LODES RAC, rolled from blocks to tracts.
- Origin-destination flows: LEHD/LODES OD main, rolled from block flows to tract flows.
- ACS equity and labor indicators: poverty, unemployment, race/ethnicity, educational attainment, vehicle access, median household income, median gross rent, and rent burden.
- Transit access: GTFS static feed when supplied with `GTFS_URL`.

## Assumptions

- Phase 1 geography is Douglas County census tracts.
- LEHD wage categories use `CE01` as low wage, `CE02` as medium wage, and `CE03` as high wage.
- Affordable rent is 30 percent of monthly median household income.
- Rent burden uses ACS gross-rent-as-percentage-of-income categories at or above 30 percent.
- Transit access uses tract centroid proximity to GTFS stops, stop counts, and nearby route counts when GTFS is available.
- Network-based “jobs reachable within 30 minutes” metrics are not estimated until a routing engine or travel-time API is added.
- Missing datasets are not replaced with fake values.

## Run The Workflow

From this folder:

```powershell
python scripts/run_all.py
```

Optional settings:

```powershell
$env:LODES_YEAR = "2022"
$env:ACS_YEAR = "2024"
$env:CENSUS_API_KEY = "your_census_key"
$env:GTFS_URL = "https://agency-url/gtfs.zip"
$env:TRANSIT_ACCESS_MILES = "0.5"
python scripts/run_all.py
```

If the Census API requires a key and `CENSUS_API_KEY` is not set, the workflow writes `data_raw/ACS_PLACEHOLDER.md` and leaves ACS-derived fields null. If GTFS is not supplied, it writes `data_raw/GTFS_PLACEHOLDER.md` and leaves transit proximity fields null.

## Dashboard

Serve the project root locally:

```powershell
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/dashboard/
```

The atlas includes KPI cards, layer toggles, legends, hover tooltips, tract search, source notes, and a concise explanation of the Spatial Mismatch Hypothesis.

## Outputs

- `outputs/csv/tract_mismatch_table.csv`
- `outputs/csv/tract_opportunity_access.csv`
- `outputs/csv/accessibility_30min_placeholder.csv`
- `outputs/geojson/tract_mismatch.geojson`
- `outputs/geojson/job_density.geojson`
- `outputs/geojson/wage_housing_mismatch.geojson`
- `outputs/geojson/opportunity_access_index.geojson`
- `outputs/geojson/revised_spatial_mismatch.geojson`
- `outputs/geojson/equity_context.geojson`
- `outputs/methods_note.md`
- `outputs/accessibility_placeholders.md`

These CSV and GeoJSON files can be used in the local dashboard or uploaded to ArcGIS Online.

## Scoring

The project now creates:

- `spatial_mismatch_score_equal`: equal-weight mismatch score.
- `spatial_mismatch_score_custom`: custom-weight mismatch score.
- `spatial_mismatch_score`: dashboard default, currently equal to the custom score.
- `opportunity_access_index`: positive access-to-opportunity score.

Weights and formulas are documented in `outputs/methods_note.md` and can be edited in `scripts/05_calculate_mismatch_metrics.py`.
