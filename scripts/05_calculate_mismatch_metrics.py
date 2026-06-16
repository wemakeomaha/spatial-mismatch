from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd

from _common import (
    DATA_PROCESSED,
    DATA_RAW,
    OUTPUT_CSV,
    OUTPUTS,
    ensure_dirs,
    haversine_miles,
    read_gtfs_stop_routes,
    read_gtfs_stops,
    read_json,
)


EQUAL_MISMATCH_INDICATORS = [
    "job_access_disadvantage_norm",
    "lower_wage_worker_concentration_norm",
    "housing_affordability_gap_norm",
    "vehicle_access_disadvantage_norm",
    "transit_access_disadvantage_norm",
    "commute_burden_norm",
]

CUSTOM_MISMATCH_WEIGHTS = {
    "job_access_disadvantage_norm": 0.25,
    "lower_wage_worker_concentration_norm": 0.20,
    "housing_affordability_gap_norm": 0.20,
    "vehicle_access_disadvantage_norm": 0.15,
    "transit_access_disadvantage_norm": 0.15,
    "commute_burden_norm": 0.05,
}

OPPORTUNITY_ACCESS_WEIGHTS = {
    "job_access_opportunity_norm": 0.25,
    "wage_opportunity_norm": 0.20,
    "housing_affordability_opportunity_norm": 0.20,
    "transit_access_opportunity_norm": 0.20,
    "vehicle_access_opportunity_norm": 0.15,
}


def normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    low = values.min(skipna=True)
    high = values.max(skipna=True)
    if pd.isna(low) or pd.isna(high) or math.isclose(float(low), float(high)):
        out = pd.Series(np.nan, index=values.index)
    else:
        out = (values - low) / (high - low)
    return 1 - out if invert else out


def weighted_score(df: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    score_parts = []
    available_weight = pd.Series(0.0, index=df.index)
    for col, weight in weights.items():
        values = pd.to_numeric(df.get(col), errors="coerce")
        score_parts.append(values.fillna(0) * weight)
        available_weight += np.where(values.notna(), weight, 0)
    return (sum(score_parts) / available_weight.replace({0: np.nan}) * 100).round(1)


def equal_score(df: pd.DataFrame, indicators: list[str]) -> pd.Series:
    weights = {indicator: 1 / len(indicators) for indicator in indicators}
    return weighted_score(df, weights)


def tract_base() -> pd.DataFrame:
    tracts = read_json(DATA_PROCESSED / "tracts_clean.geojson")
    rows = []
    for feature in tracts.get("features", []):
        props = feature.get("properties", {})
        rows.append(
            {
                "GEOID": props.get("GEOID"),
                "tract_name": props.get("tract_name"),
                "area_sq_mi": props.get("area_sq_mi"),
                "centroid_lon": props.get("centroid_lon"),
                "centroid_lat": props.get("centroid_lat"),
            }
        )
    return pd.DataFrame(rows)


def transit_access(base: pd.DataFrame) -> pd.DataFrame:
    stops = read_gtfs_stops(DATA_RAW / "omaha_gtfs.zip")
    stop_routes = read_gtfs_stop_routes(DATA_RAW / "omaha_gtfs.zip")
    access_distance = float(os.getenv("TRANSIT_ACCESS_MILES", "0.5"))
    rows = []

    for _, row in base.iterrows():
        lon, lat = row.get("centroid_lon"), row.get("centroid_lat")
        if not stops or pd.isna(lon) or pd.isna(lat):
            rows.append(
                {
                    "GEOID": row["GEOID"],
                    "nearest_stop_miles": np.nan,
                    "stops_within_0_25_mi": np.nan,
                    "stops_within_0_5_mi": np.nan,
                    "routes_within_0_5_mi": np.nan,
                    "transit_access_flag": pd.NA,
                    "transit_metric_status": "GTFS unavailable - placeholder",
                }
            )
            continue

        near_025 = 0
        near_05 = 0
        route_ids: set[str] = set()
        nearest = np.nan
        for stop_id, stop_lon, stop_lat in stops:
            distance = haversine_miles(float(lon), float(lat), stop_lon, stop_lat)
            nearest = distance if pd.isna(nearest) else min(float(nearest), distance)
            if distance <= 0.25:
                near_025 += 1
            if distance <= 0.5:
                near_05 += 1
                route_ids.update(stop_routes.get(stop_id, set()))

        rows.append(
            {
                "GEOID": row["GEOID"],
                "nearest_stop_miles": nearest,
                "stops_within_0_25_mi": near_025,
                "stops_within_0_5_mi": near_05,
                "routes_within_0_5_mi": len(route_ids) if stop_routes else np.nan,
                "transit_access_flag": bool(nearest <= access_distance) if not pd.isna(nearest) else pd.NA,
                "transit_metric_status": "GTFS stop and route proximity",
            }
        )
    return pd.DataFrame(rows)


def ensure_columns(df: pd.DataFrame, columns: list[str], fill=np.nan) -> None:
    for col in columns:
        if col not in df.columns:
            df[col] = fill


def write_methods_note() -> None:
    (OUTPUTS / "methods_note.md").write_text(
        "# Methods Note\n\n"
        "## Geography\n\n"
        "The atlas uses Douglas County, Nebraska census tracts as the Phase 1 geography. "
        "LEHD/LODES block records are aggregated to tract GEOID using the first 11 digits of each block code.\n\n"
        "## Data Sources\n\n"
        "- Census TIGERweb tract boundaries for Douglas County.\n"
        "- LEHD/LODES WAC, RAC, and OD files for Nebraska.\n"
        "- ACS 5-year tract indicators when `CENSUS_API_KEY` is available.\n"
        "- GTFS static feed when `GTFS_URL` is supplied.\n\n"
        "## ACS Equity And Labor Indicators\n\n"
        "The ACS script requests poverty, unemployment, race/ethnicity, educational attainment, vehicle access, "
        "median household income, median gross rent, and rent burden. If the Census API requires a key and no key "
        "is provided, those fields remain missing and are not replaced with synthetic values.\n\n"
        "## Transit Access\n\n"
        "When GTFS is available, transit access uses distance to the nearest stop, stop counts within 0.25 and "
        "0.5 miles of the tract centroid, and distinct route count within 0.5 miles. The current service proxy is "
        "route availability near the tract centroid. Frequency requires calendar/stop_times expansion by time window "
        "and should be added in a later phase. If GTFS is unavailable, transit fields are null and marked as a placeholder.\n\n"
        "## Opportunity Access Index\n\n"
        "The Opportunity Access Index is a positive score from 0 to 100. Higher values indicate stronger access to opportunity.\n\n"
        "```text\n"
        "opportunity_access_index = 100 * weighted_mean(\n"
        "  0.25 * job_access_opportunity_norm,\n"
        "  0.20 * wage_opportunity_norm,\n"
        "  0.20 * housing_affordability_opportunity_norm,\n"
        "  0.20 * transit_access_opportunity_norm,\n"
        "  0.15 * vehicle_access_opportunity_norm\n"
        ")\n"
        "```\n\n"
        "## Revised Spatial Mismatch Scores\n\n"
        "The revised mismatch score is no longer only a jobs-worker ratio. It combines low job access, concentration of "
        "lower-wage or lower-income workers, housing affordability gaps, vehicle-access disadvantage, weak transit access, "
        "and commute burden when available.\n\n"
        "Equal-weight score:\n\n"
        "```text\n"
        "spatial_mismatch_score_equal = 100 * mean(\n"
        "  job_access_disadvantage_norm,\n"
        "  lower_wage_worker_concentration_norm,\n"
        "  housing_affordability_gap_norm,\n"
        "  vehicle_access_disadvantage_norm,\n"
        "  transit_access_disadvantage_norm,\n"
        "  commute_burden_norm\n"
        ")\n"
        "```\n\n"
        "Custom-weight score:\n\n"
        "```text\n"
        "spatial_mismatch_score_custom = 100 * weighted_mean(\n"
        "  0.25 * job_access_disadvantage_norm,\n"
        "  0.20 * lower_wage_worker_concentration_norm,\n"
        "  0.20 * housing_affordability_gap_norm,\n"
        "  0.15 * vehicle_access_disadvantage_norm,\n"
        "  0.15 * transit_access_disadvantage_norm,\n"
        "  0.05 * commute_burden_norm\n"
        ")\n"
        "```\n\n"
        "When an indicator is missing, its weight is excluded from that tract's denominator. This prevents missing ACS, GTFS, "
        "or network-analysis inputs from being treated as zero disadvantage.\n\n"
        "## Accessibility Placeholders\n\n"
        "`scripts/07_prepare_accessibility_placeholders.py` creates documentation for future jobs-reachable-within-30-minutes "
        "metrics by car and transit. Full implementation requires a routable street network or travel-time API, a transit "
        "schedule/network model, a selected departure time window, and a job destination layer.\n\n"
        "## Revision Points\n\n"
        "Edit `CUSTOM_MISMATCH_WEIGHTS`, `EQUAL_MISMATCH_INDICATORS`, and `OPPORTUNITY_ACCESS_WEIGHTS` in "
        "`scripts/05_calculate_mismatch_metrics.py` to revise formulas. Set `TRANSIT_ACCESS_MILES`, `LODES_YEAR`, "
        "`ACS_YEAR`, `CENSUS_API_KEY`, and `GTFS_URL` as needed before rerunning the workflow.\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    base = tract_base()
    lehd = pd.read_csv(DATA_PROCESSED / "lehd_tract_metrics.csv", dtype={"GEOID": str}) if (DATA_PROCESSED / "lehd_tract_metrics.csv").exists() else pd.DataFrame(columns=["GEOID"])
    acs = pd.read_csv(DATA_PROCESSED / "acs_housing_income.csv", dtype={"GEOID": str}) if (DATA_PROCESSED / "acs_housing_income.csv").exists() else pd.DataFrame(columns=["GEOID"])
    transit = transit_access(base)

    df = base.merge(lehd, on="GEOID", how="left").merge(acs, on="GEOID", how="left").merge(transit, on="GEOID", how="left")
    ensure_columns(
        df,
        [
            "median_rent", "median_household_income", "affordable_rent_estimate",
            "households_without_vehicles", "no_vehicle_share", "poverty_rate",
            "unemployment_rate", "people_of_color_share", "nh_white_share",
            "nh_black_share", "hispanic_share", "bachelors_plus_share",
            "hs_plus_share", "rent_burden_rate",
        ],
    )
    ensure_columns(
        df,
        [
            "jobs_total", "jobs_low_wage", "jobs_medium_wage", "jobs_high_wage",
            "resident_workers_total", "resident_workers_low_wage",
            "resident_workers_medium_wage", "resident_workers_high_wage",
        ],
        fill=0,
    )

    for col in [
        "jobs_total", "jobs_low_wage", "jobs_medium_wage", "jobs_high_wage",
        "resident_workers_total", "resident_workers_low_wage",
        "resident_workers_medium_wage", "resident_workers_high_wage",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["jobs_worker_ratio"] = df["jobs_total"] / df["resident_workers_total"].replace({0: np.nan})
    df["share_low_wage_jobs"] = df["jobs_low_wage"] / df["jobs_total"].replace({0: np.nan})
    df["share_low_wage_resident_workers"] = df["resident_workers_low_wage"] / df["resident_workers_total"].replace({0: np.nan})
    df["job_density_per_sq_mi"] = df["jobs_total"] / pd.to_numeric(df["area_sq_mi"], errors="coerce").replace({0: np.nan})
    df["rent_affordability_gap"] = pd.to_numeric(df["median_rent"], errors="coerce") - pd.to_numeric(df["affordable_rent_estimate"], errors="coerce")
    df["rent_affordability_gap_positive"] = df["rent_affordability_gap"].clip(lower=0)
    df["wage_housing_mismatch_flag"] = np.where(df["rent_affordability_gap"].notna(), df["rent_affordability_gap"] > 0, pd.NA)

    # If ACS poverty is missing, LEHD low-wage resident workers provide a public-data fallback for worker disadvantage.
    lower_wage_or_income = pd.to_numeric(df["poverty_rate"], errors="coerce").combine_first(df["share_low_wage_resident_workers"])

    transit_opportunity_raw = pd.to_numeric(df["stops_within_0_5_mi"], errors="coerce")
    if "routes_within_0_5_mi" in df.columns:
        transit_opportunity_raw = transit_opportunity_raw + pd.to_numeric(df["routes_within_0_5_mi"], errors="coerce").fillna(0)
    if transit_opportunity_raw.notna().sum() == 0:
        transit_opportunity_raw = df["transit_access_flag"].map({True: 1.0, False: 0.0})

    df["job_access_disadvantage_norm"] = normalize(df["jobs_worker_ratio"], invert=True)
    df["lower_wage_worker_concentration_norm"] = normalize(lower_wage_or_income)
    df["housing_affordability_gap_norm"] = normalize(df["rent_affordability_gap_positive"].combine_first(df["rent_burden_rate"]))
    df["vehicle_access_disadvantage_norm"] = normalize(df["no_vehicle_share"])
    df["transit_access_disadvantage_norm"] = normalize(transit_opportunity_raw, invert=True)
    df["commute_burden_norm"] = np.nan

    df["job_access_opportunity_norm"] = normalize(df["jobs_worker_ratio"])
    df["wage_opportunity_norm"] = normalize(df["share_low_wage_jobs"], invert=True)
    df["housing_affordability_opportunity_norm"] = normalize(df["rent_affordability_gap_positive"].combine_first(df["rent_burden_rate"]), invert=True)
    df["transit_access_opportunity_norm"] = normalize(transit_opportunity_raw)
    df["vehicle_access_opportunity_norm"] = normalize(df["no_vehicle_share"], invert=True)

    df["spatial_mismatch_score_equal"] = equal_score(df, EQUAL_MISMATCH_INDICATORS)
    df["spatial_mismatch_score_custom"] = weighted_score(df, CUSTOM_MISMATCH_WEIGHTS)
    df["spatial_mismatch_score"] = df["spatial_mismatch_score_custom"]
    df["opportunity_access_index"] = weighted_score(df, OPPORTUNITY_ACCESS_WEIGHTS)

    df["spatial_mismatch_tier"] = pd.cut(
        df["spatial_mismatch_score_custom"],
        bins=[-0.1, 33.3, 66.6, 100.0],
        labels=["Lower", "Moderate", "Higher"],
    )
    df["opportunity_access_tier"] = pd.cut(
        df["opportunity_access_index"],
        bins=[-0.1, 33.3, 66.6, 100.0],
        labels=["Lower", "Moderate", "Higher"],
    )

    df = df.rename(
        columns={
            "jobs_total": "total_jobs",
            "jobs_low_wage": "low_wage_jobs",
            "jobs_medium_wage": "medium_wage_jobs",
            "jobs_high_wage": "high_wage_jobs",
            "resident_workers_total": "resident_workers",
        }
    )

    output_cols = [
        "GEOID", "tract_name", "total_jobs", "resident_workers", "jobs_worker_ratio",
        "low_wage_jobs", "medium_wage_jobs", "high_wage_jobs", "share_low_wage_jobs",
        "share_low_wage_resident_workers", "job_density_per_sq_mi",
        "median_rent", "median_household_income", "affordable_rent_estimate",
        "rent_affordability_gap", "wage_housing_mismatch_flag", "rent_burden_rate",
        "poverty_rate", "unemployment_rate", "households_without_vehicles", "no_vehicle_share",
        "people_of_color_share", "nh_white_share", "nh_black_share", "hispanic_share",
        "bachelors_plus_share", "hs_plus_share",
        "transit_access_flag", "nearest_stop_miles", "stops_within_0_25_mi",
        "stops_within_0_5_mi", "routes_within_0_5_mi", "transit_metric_status",
        "spatial_mismatch_score_equal", "spatial_mismatch_score_custom", "spatial_mismatch_score",
        "spatial_mismatch_tier", "opportunity_access_index", "opportunity_access_tier",
        "area_sq_mi", "centroid_lon", "centroid_lat",
    ]
    for col in output_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df[output_cols].to_csv(OUTPUT_CSV / "tract_mismatch_table.csv", index=False)
    df[[
        "GEOID", "tract_name", "opportunity_access_index", "opportunity_access_tier",
        "job_access_opportunity_norm", "wage_opportunity_norm",
        "housing_affordability_opportunity_norm", "transit_access_opportunity_norm",
        "vehicle_access_opportunity_norm", "total_jobs", "resident_workers",
        "jobs_worker_ratio", "median_rent", "median_household_income",
        "nearest_stop_miles", "stops_within_0_5_mi", "routes_within_0_5_mi",
    ]].to_csv(OUTPUT_CSV / "tract_opportunity_access.csv", index=False)

    write_methods_note()
    print(f"Wrote atlas metrics to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
