# Methods Note

## Geography

The atlas uses Douglas County, Nebraska census tracts as the Phase 1 geography. LEHD/LODES block records are aggregated to tract GEOID using the first 11 digits of each block code.

## Data Sources

- Census TIGERweb tract boundaries for Douglas County.
- LEHD/LODES WAC, RAC, and OD files for Nebraska.
- ACS 5-year tract indicators when `CENSUS_API_KEY` is available.
- GTFS static feed when `GTFS_URL` is supplied.

## ACS Equity And Labor Indicators

The ACS script requests poverty, unemployment, race/ethnicity, educational attainment, vehicle access, median household income, median gross rent, and rent burden. If the Census API requires a key and no key is provided, those fields remain missing and are not replaced with synthetic values.

## Transit Access

When GTFS is available, transit access uses distance to the nearest stop, stop counts within 0.25 and 0.5 miles of the tract centroid, and distinct route count within 0.5 miles. The current service proxy is route availability near the tract centroid. Frequency requires calendar/stop_times expansion by time window and should be added in a later phase. If GTFS is unavailable, transit fields are null and marked as a placeholder.

## Opportunity Access Index

The Opportunity Access Index is a positive score from 0 to 100. Higher values indicate stronger access to opportunity.

```text
opportunity_access_index = 100 * weighted_mean(
  0.25 * job_access_opportunity_norm,
  0.20 * wage_opportunity_norm,
  0.20 * housing_affordability_opportunity_norm,
  0.20 * transit_access_opportunity_norm,
  0.15 * vehicle_access_opportunity_norm
)
```

## Revised Spatial Mismatch Scores

The revised mismatch score is no longer only a jobs-worker ratio. It combines low job access, concentration of lower-wage or lower-income workers, housing affordability gaps, vehicle-access disadvantage, weak transit access, and commute burden when available.

Equal-weight score:

```text
spatial_mismatch_score_equal = 100 * mean(
  job_access_disadvantage_norm,
  lower_wage_worker_concentration_norm,
  housing_affordability_gap_norm,
  vehicle_access_disadvantage_norm,
  transit_access_disadvantage_norm,
  commute_burden_norm
)
```

Custom-weight score:

```text
spatial_mismatch_score_custom = 100 * weighted_mean(
  0.25 * job_access_disadvantage_norm,
  0.20 * lower_wage_worker_concentration_norm,
  0.20 * housing_affordability_gap_norm,
  0.15 * vehicle_access_disadvantage_norm,
  0.15 * transit_access_disadvantage_norm,
  0.05 * commute_burden_norm
)
```

When an indicator is missing, its weight is excluded from that tract's denominator. This prevents missing ACS, GTFS, or network-analysis inputs from being treated as zero disadvantage.

## Accessibility Placeholders

`scripts/07_prepare_accessibility_placeholders.py` creates documentation for future jobs-reachable-within-30-minutes metrics by car and transit. Full implementation requires a routable street network or travel-time API, a transit schedule/network model, a selected departure time window, and a job destination layer.

## Revision Points

Edit `CUSTOM_MISMATCH_WEIGHTS`, `EQUAL_MISMATCH_INDICATORS`, and `OPPORTUNITY_ACCESS_WEIGHTS` in `scripts/05_calculate_mismatch_metrics.py` to revise formulas. Set `TRANSIT_ACCESS_MILES`, `LODES_YEAR`, `ACS_YEAR`, `CENSUS_API_KEY`, and `GTFS_URL` as needed before rerunning the workflow.
