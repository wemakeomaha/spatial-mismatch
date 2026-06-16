from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

import pandas as pd

from _common import ACS_YEAR, COUNTY_FIPS, DATA_PROCESSED, DATA_RAW, STATE_FIPS, ensure_dirs, load_project_env


ACS_VARIABLES = {
    "NAME": "tract_label",
    "B25064_001E": "median_rent",
    "B19013_001E": "median_household_income",
    "B08201_001E": "vehicle_households_total",
    "B08201_002E": "households_without_vehicles",
    "B17001_001E": "poverty_universe",
    "B17001_002E": "population_below_poverty",
    "B23025_002E": "civilian_labor_force",
    "B23025_005E": "unemployed_population",
    "B03002_001E": "race_ethnicity_total",
    "B03002_003E": "nh_white_population",
    "B03002_004E": "nh_black_population",
    "B03002_005E": "nh_native_population",
    "B03002_006E": "nh_asian_population",
    "B03002_007E": "nh_pacific_population",
    "B03002_008E": "nh_other_population",
    "B03002_009E": "nh_two_or_more_population",
    "B03002_012E": "hispanic_population",
    "B15003_001E": "education_25plus_total",
    "B15003_017E": "educ_hs_diploma",
    "B15003_018E": "educ_ged",
    "B15003_019E": "educ_some_college_less_1yr",
    "B15003_020E": "educ_some_college_1plus",
    "B15003_021E": "educ_associates",
    "B15003_022E": "educ_bachelors",
    "B15003_023E": "educ_masters",
    "B15003_024E": "educ_professional",
    "B15003_025E": "educ_doctorate",
    "B25070_001E": "rent_burden_universe",
    "B25070_007E": "rent_burden_30_34",
    "B25070_008E": "rent_burden_35_39",
    "B25070_009E": "rent_burden_40_49",
    "B25070_010E": "rent_burden_50_plus",
}


def fetch_acs(year: str) -> list[list[str]]:
    params = {
        "get": ",".join(ACS_VARIABLES.keys()),
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
    }
    census_key = os.getenv("CENSUS_API_KEY", "").strip()
    if census_key:
        params["key"] = census_key
    url = f"https://api.census.gov/data/{year}/acs/acs5?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
        if not text.lstrip().startswith("["):
            raise ValueError(text[:240].replace("\n", " "))
        return json.loads(text)


def main() -> None:
    ensure_dirs()
    load_project_env()
    errors = []
    rows = None
    used_year = None
    for year in [ACS_YEAR, "2023", "2022", "2021"]:
        try:
            rows = fetch_acs(year)
            used_year = year
            break
        except Exception as exc:
            errors.append({"year": year, "error": f"{type(exc).__name__}: {exc}"})

    if rows is None:
        key_status = "provided" if os.getenv("CENSUS_API_KEY", "").strip() else "missing"
        placeholder = DATA_RAW / "ACS_PLACEHOLDER.md"
        placeholder.write_text(
            "# ACS placeholder\n\n"
            "ACS download failed. Needed tract variables include median gross rent, "
            "median household income, vehicle access, poverty, unemployment, "
            "race/ethnicity, educational attainment, and rent burden fields.\n\n"
            f"Census API key status for this run: {key_status}. The key value is not written to disk.\n\n"
            "If the Census API response says `Invalid Key`, confirm that the key was copied exactly, "
            "activated through the Census signup email, and is set in the current terminal or `.env` file.\n\n"
            f"Errors: {errors}\n",
            encoding="utf-8",
        )
        pd.DataFrame(columns=["GEOID", *ACS_VARIABLES.values(), "acs_year"]).to_csv(
            DATA_PROCESSED / "acs_housing_income.csv", index=False
        )
        print(f"ACS download failed. Wrote {placeholder}")
        return

    placeholder = DATA_RAW / "ACS_PLACEHOLDER.md"
    if placeholder.exists():
        placeholder.unlink()

    header, records = rows[0], rows[1:]
    df = pd.DataFrame(records, columns=header)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    df = df.rename(columns=ACS_VARIABLES)
    numeric_cols = [col for col in ACS_VARIABLES.values() if col != "tract_label"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = pd.NA

    df["no_vehicle_share"] = df["households_without_vehicles"] / df["vehicle_households_total"]
    df["affordable_rent_estimate"] = df["median_household_income"] * 0.30 / 12
    df["poverty_rate"] = df["population_below_poverty"] / df["poverty_universe"]
    df["unemployment_rate"] = df["unemployed_population"] / df["civilian_labor_force"]
    df["nh_white_share"] = df["nh_white_population"] / df["race_ethnicity_total"]
    df["nh_black_share"] = df["nh_black_population"] / df["race_ethnicity_total"]
    df["nh_native_share"] = df["nh_native_population"] / df["race_ethnicity_total"]
    df["nh_asian_share"] = df["nh_asian_population"] / df["race_ethnicity_total"]
    df["nh_pacific_share"] = df["nh_pacific_population"] / df["race_ethnicity_total"]
    df["nh_other_share"] = df["nh_other_population"] / df["race_ethnicity_total"]
    df["nh_two_or_more_share"] = df["nh_two_or_more_population"] / df["race_ethnicity_total"]
    df["hispanic_share"] = df["hispanic_population"] / df["race_ethnicity_total"]
    df["people_of_color_share"] = 1 - df["nh_white_share"]
    df["hs_plus_population"] = df[
        [
            "educ_hs_diploma", "educ_ged", "educ_some_college_less_1yr", "educ_some_college_1plus",
            "educ_associates", "educ_bachelors", "educ_masters", "educ_professional", "educ_doctorate",
        ]
    ].sum(axis=1, min_count=1)
    df["bachelors_plus_population"] = df[["educ_bachelors", "educ_masters", "educ_professional", "educ_doctorate"]].sum(axis=1, min_count=1)
    df["hs_plus_share"] = df["hs_plus_population"] / df["education_25plus_total"]
    df["bachelors_plus_share"] = df["bachelors_plus_population"] / df["education_25plus_total"]
    df["rent_burdened_households"] = df[["rent_burden_30_34", "rent_burden_35_39", "rent_burden_40_49", "rent_burden_50_plus"]].sum(axis=1, min_count=1)
    df["rent_burden_rate"] = df["rent_burdened_households"] / df["rent_burden_universe"]
    df["acs_year"] = used_year
    keep = [
        "GEOID", "tract_label", "median_rent", "median_household_income", "affordable_rent_estimate",
        "vehicle_households_total", "households_without_vehicles", "no_vehicle_share",
        "poverty_universe", "population_below_poverty", "poverty_rate",
        "civilian_labor_force", "unemployed_population", "unemployment_rate",
        "race_ethnicity_total", "nh_white_population", "nh_black_population", "nh_native_population",
        "nh_asian_population", "nh_pacific_population", "nh_other_population",
        "nh_two_or_more_population", "hispanic_population", "nh_white_share", "nh_black_share",
        "nh_native_share", "nh_asian_share", "nh_pacific_share", "nh_other_share",
        "nh_two_or_more_share", "hispanic_share", "people_of_color_share",
        "education_25plus_total", "hs_plus_population", "bachelors_plus_population",
        "hs_plus_share", "bachelors_plus_share",
        "rent_burden_universe", "rent_burdened_households", "rent_burden_rate",
        "acs_year",
    ]
    df[keep].to_csv(DATA_PROCESSED / "acs_housing_income.csv", index=False)
    print(f"Wrote ACS tract indicators for {len(df)} tracts using {used_year} ACS 5-year")


if __name__ == "__main__":
    main()
