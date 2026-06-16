from __future__ import annotations

from _common import DATA_PROCESSED, DATA_RAW, area_sq_miles, centroid_from_geometry, ensure_dirs, read_json, write_json


def main() -> None:
    ensure_dirs()
    source = DATA_RAW / "douglas_county_tracts_tigerweb.geojson"
    if not source.exists():
        raise FileNotFoundError(f"Missing tract file: {source}. Run 01_download_or_import_data.py first.")

    geojson = read_json(source)
    features = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geoid = str(props.get("GEOID") or props.get("GEOID20") or "")
        if not geoid:
            continue
        lon, lat = centroid_from_geometry(feature.get("geometry", {}))
        area = area_sq_miles(feature.get("geometry", {}))
        feature["properties"] = {
            "GEOID": geoid,
            "tract_name": props.get("NAME") or props.get("BASENAME") or geoid,
            "state": props.get("STATE") or geoid[:2],
            "county": props.get("COUNTY") or geoid[2:5],
            "centroid_lon": lon,
            "centroid_lat": lat,
            "area_sq_mi": area,
        }
        features.append(feature)

    output = {"type": "FeatureCollection", "features": features}
    write_json(DATA_PROCESSED / "tracts_clean.geojson", output)
    print(f"Cleaned {len(features)} tracts")


if __name__ == "__main__":
    main()
