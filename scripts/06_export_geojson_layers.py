from __future__ import annotations

import pandas as pd

from _common import DATA_PROCESSED, OUTPUT_CSV, OUTPUT_GEOJSON, ensure_dirs, read_json, write_json


def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def export_layer(name: str, properties: list[str], rows: dict[str, dict], tracts: dict) -> None:
    features = []
    for feature in tracts.get("features", []):
        geoid = str(feature.get("properties", {}).get("GEOID", ""))
        row = rows.get(geoid, {})
        props = {key: clean_value(row.get(key)) for key in properties}
        props["GEOID"] = geoid
        props["tract_name"] = feature.get("properties", {}).get("tract_name")
        features.append({"type": "Feature", "geometry": feature.get("geometry"), "properties": props})
    write_json(OUTPUT_GEOJSON / name, {"type": "FeatureCollection", "features": features})


def main() -> None:
    ensure_dirs()
    table_path = OUTPUT_CSV / "tract_mismatch_table.csv"
    if not table_path.exists():
        raise FileNotFoundError(f"Missing {table_path}. Run 05_calculate_mismatch_metrics.py first.")

    df = pd.read_csv(table_path, dtype={"GEOID": str})
    rows = df.set_index("GEOID").to_dict(orient="index")
    tracts = read_json(DATA_PROCESSED / "tracts_clean.geojson")

    all_props = [col for col in df.columns if col != "GEOID"]
    export_layer("tract_mismatch.geojson", all_props, rows, tracts)
    export_layer("job_density.geojson", ["total_jobs", "job_density_per_sq_mi", "jobs_worker_ratio"], rows, tracts)
    export_layer(
        "opportunity_access_index.geojson",
        [
            "opportunity_access_index", "opportunity_access_tier", "jobs_worker_ratio",
            "total_jobs", "median_rent", "median_household_income", "transit_access_flag",
            "stops_within_0_5_mi", "routes_within_0_5_mi",
        ],
        rows,
        tracts,
    )
    export_layer(
        "revised_spatial_mismatch.geojson",
        [
            "spatial_mismatch_score_equal", "spatial_mismatch_score_custom",
            "spatial_mismatch_score", "spatial_mismatch_tier", "jobs_worker_ratio",
            "share_low_wage_resident_workers", "rent_burden_rate", "no_vehicle_share",
            "nearest_stop_miles", "transit_metric_status",
        ],
        rows,
        tracts,
    )
    export_layer(
        "equity_context.geojson",
        [
            "poverty_rate", "unemployment_rate", "people_of_color_share", "nh_white_share",
            "nh_black_share", "hispanic_share", "bachelors_plus_share", "hs_plus_share",
            "median_household_income", "median_rent", "rent_burden_rate",
            "households_without_vehicles", "no_vehicle_share",
        ],
        rows,
        tracts,
    )
    export_layer(
        "wage_housing_mismatch.geojson",
        ["median_rent", "median_household_income", "affordable_rent_estimate", "wage_housing_mismatch_flag"],
        rows,
        tracts,
    )
    print(f"Wrote GeoJSON layers to {OUTPUT_GEOJSON}")


if __name__ == "__main__":
    main()
