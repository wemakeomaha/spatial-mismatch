from __future__ import annotations

import pandas as pd

from _common import COUNTY_GEOID, DATA_PROCESSED, DATA_RAW, ensure_dirs, tract_from_block


WAGE_COLUMNS = ["CE01", "CE02", "CE03"]


def aggregate_lodes(path, geocode_col: str, prefix: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["GEOID"])
    chunks = []
    usecols = [geocode_col, "C000", *WAGE_COLUMNS]
    for chunk in pd.read_csv(path, compression="gzip", usecols=usecols, chunksize=250_000, dtype={geocode_col: str}):
        chunk["GEOID"] = chunk[geocode_col].map(tract_from_block)
        chunk = chunk[chunk["GEOID"].str.startswith(COUNTY_GEOID)]
        numeric_cols = ["C000", *WAGE_COLUMNS]
        chunk[numeric_cols] = chunk[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        chunks.append(chunk.groupby("GEOID", as_index=False)[numeric_cols].sum())
    if not chunks:
        return pd.DataFrame(columns=["GEOID"])
    out = pd.concat(chunks).groupby("GEOID", as_index=False).sum()
    rename = {
        "C000": f"{prefix}_total",
        "CE01": f"{prefix}_low_wage",
        "CE02": f"{prefix}_medium_wage",
        "CE03": f"{prefix}_high_wage",
    }
    return out.rename(columns=rename)


def aggregate_od(path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["home_tract", "work_tract", "flow_jobs"])
    chunks = []
    for chunk in pd.read_csv(
        path,
        compression="gzip",
        usecols=["h_geocode", "w_geocode", "S000"],
        chunksize=250_000,
        dtype={"h_geocode": str, "w_geocode": str},
    ):
        chunk["home_tract"] = chunk["h_geocode"].map(tract_from_block)
        chunk["work_tract"] = chunk["w_geocode"].map(tract_from_block)
        chunk = chunk[
            chunk["home_tract"].str.startswith(COUNTY_GEOID)
            | chunk["work_tract"].str.startswith(COUNTY_GEOID)
        ]
        chunk["S000"] = pd.to_numeric(chunk["S000"], errors="coerce").fillna(0)
        chunks.append(chunk.groupby(["home_tract", "work_tract"], as_index=False)["S000"].sum())
    if not chunks:
        return pd.DataFrame(columns=["home_tract", "work_tract", "flow_jobs"])
    return (
        pd.concat(chunks)
        .groupby(["home_tract", "work_tract"], as_index=False)["S000"]
        .sum()
        .rename(columns={"S000": "flow_jobs"})
    )


def main() -> None:
    ensure_dirs()
    wac = aggregate_lodes(DATA_RAW / "ne_wac_S000_JT00.csv.gz", "w_geocode", "jobs")
    rac = aggregate_lodes(DATA_RAW / "ne_rac_S000_JT00.csv.gz", "h_geocode", "resident_workers")
    od = aggregate_od(DATA_RAW / "ne_od_main_JT00.csv.gz")

    metrics = pd.merge(wac, rac, on="GEOID", how="outer").fillna(0)
    metrics.to_csv(DATA_PROCESSED / "lehd_tract_metrics.csv", index=False)
    od.to_csv(DATA_PROCESSED / "lehd_od_tract_flows.csv", index=False)
    print(f"Wrote LEHD tract metrics for {len(metrics)} tracts and {len(od)} OD pairs")


if __name__ == "__main__":
    main()
