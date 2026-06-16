# Data Quality Report

## Dataset Audit

| dataset | status |
| --- | --- |
| data_raw\download_manifest.json | present (2,438 bytes) |
| data_raw\douglas_county_tracts_tigerweb.geojson | present (891,072 bytes) |
| data_raw\ne_wac_S000_JT00.csv.gz | present (502,454 bytes) |
| data_raw\ne_rac_S000_JT00.csv.gz | present (1,464,657 bytes) |
| data_raw\ne_od_main_JT00.csv.gz | present (4,741,680 bytes) |
| data_raw\omaha_gtfs.zip | missing |
| data_processed\tracts_clean.geojson | present (2,168,701 bytes) |
| data_processed\lehd_tract_metrics.csv | present (7,777 bytes) |
| data_processed\lehd_od_tract_flows.csv | present (1,588,449 bytes) |
| data_processed\acs_housing_income.csv | present (76,976 bytes) |

## ACS Diagnostics

- Census API key available to this run: yes
- Census API key diagnostic: ACS data present; latest ACS pull succeeded
- Census API key required in this environment: yes; without a key, the Census API returned a `Missing Key` response.
- ACS rows downloaded: 163
- ACS year(s): 2024
- Tracts in boundary layer: 163
- ACS GEOIDs matched to tract layer: 163
- ACS GEOIDs missing from tract layer: 0
- Tract GEOIDs missing from ACS table: 0
- Minimum ACS field completeness: 95.1%
- Meets 95 percent completeness target: yes

Previous ACS placeholders occurred because the Census API returned a `Missing Key` HTML response when no `CENSUS_API_KEY` was available. The workflow now reads `CENSUS_API_KEY` from the system environment or a local `.env` file. If the response is `Invalid Key`, the key must be corrected or activated before ACS fields can populate.

## ACS Field Completeness Before Join

| field | non_null | tracts | completeness |
| --- | --- | --- | --- |
| median_rent | 155 | 163 | 95.1% |
| median_household_income | 163 | 163 | 100.0% |
| affordable_rent_estimate | 163 | 163 | 100.0% |
| vehicle_households_total | 163 | 163 | 100.0% |
| households_without_vehicles | 163 | 163 | 100.0% |
| no_vehicle_share | 163 | 163 | 100.0% |
| poverty_universe | 163 | 163 | 100.0% |
| population_below_poverty | 163 | 163 | 100.0% |
| poverty_rate | 163 | 163 | 100.0% |
| civilian_labor_force | 163 | 163 | 100.0% |
| unemployed_population | 163 | 163 | 100.0% |
| unemployment_rate | 163 | 163 | 100.0% |
| race_ethnicity_total | 163 | 163 | 100.0% |
| nh_white_population | 163 | 163 | 100.0% |
| nh_black_population | 163 | 163 | 100.0% |
| nh_native_population | 163 | 163 | 100.0% |
| nh_asian_population | 163 | 163 | 100.0% |
| nh_pacific_population | 163 | 163 | 100.0% |
| nh_other_population | 163 | 163 | 100.0% |
| nh_two_or_more_population | 163 | 163 | 100.0% |
| hispanic_population | 163 | 163 | 100.0% |
| nh_white_share | 163 | 163 | 100.0% |
| nh_black_share | 163 | 163 | 100.0% |
| nh_native_share | 163 | 163 | 100.0% |
| nh_asian_share | 163 | 163 | 100.0% |
| nh_pacific_share | 163 | 163 | 100.0% |
| nh_other_share | 163 | 163 | 100.0% |
| nh_two_or_more_share | 163 | 163 | 100.0% |
| hispanic_share | 163 | 163 | 100.0% |
| people_of_color_share | 163 | 163 | 100.0% |
| education_25plus_total | 163 | 163 | 100.0% |
| hs_plus_population | 163 | 163 | 100.0% |
| bachelors_plus_population | 163 | 163 | 100.0% |
| hs_plus_share | 163 | 163 | 100.0% |
| bachelors_plus_share | 163 | 163 | 100.0% |
| rent_burden_universe | 163 | 163 | 100.0% |
| rent_burdened_households | 163 | 163 | 100.0% |
| rent_burden_rate | 163 | 163 | 100.0% |

## ACS Field Completeness After Join

| field | non_null_after_join | tracts | completeness |
| --- | --- | --- | --- |
| median_rent | 155 | 163 | 95.1% |
| median_household_income | 163 | 163 | 100.0% |
| affordable_rent_estimate | 163 | 163 | 100.0% |
| vehicle_households_total | 0 | 163 | 0.0% |
| households_without_vehicles | 163 | 163 | 100.0% |
| no_vehicle_share | 163 | 163 | 100.0% |
| poverty_universe | 0 | 163 | 0.0% |
| population_below_poverty | 0 | 163 | 0.0% |
| poverty_rate | 163 | 163 | 100.0% |
| civilian_labor_force | 0 | 163 | 0.0% |
| unemployed_population | 0 | 163 | 0.0% |
| unemployment_rate | 163 | 163 | 100.0% |
| race_ethnicity_total | 0 | 163 | 0.0% |
| nh_white_population | 0 | 163 | 0.0% |
| nh_black_population | 0 | 163 | 0.0% |
| nh_native_population | 0 | 163 | 0.0% |
| nh_asian_population | 0 | 163 | 0.0% |
| nh_pacific_population | 0 | 163 | 0.0% |
| nh_other_population | 0 | 163 | 0.0% |
| nh_two_or_more_population | 0 | 163 | 0.0% |
| hispanic_population | 0 | 163 | 0.0% |
| nh_white_share | 163 | 163 | 100.0% |
| nh_black_share | 163 | 163 | 100.0% |
| nh_native_share | 0 | 163 | 0.0% |
| nh_asian_share | 0 | 163 | 0.0% |
| nh_pacific_share | 0 | 163 | 0.0% |
| nh_other_share | 0 | 163 | 0.0% |
| nh_two_or_more_share | 0 | 163 | 0.0% |
| hispanic_share | 163 | 163 | 100.0% |
| people_of_color_share | 163 | 163 | 100.0% |
| education_25plus_total | 0 | 163 | 0.0% |
| hs_plus_population | 0 | 163 | 0.0% |
| bachelors_plus_population | 0 | 163 | 0.0% |
| hs_plus_share | 163 | 163 | 100.0% |
| bachelors_plus_share | 163 | 163 | 100.0% |
| rent_burden_universe | 0 | 163 | 0.0% |
| rent_burdened_households | 0 | 163 | 0.0% |
| rent_burden_rate | 163 | 163 | 100.0% |

## Join Diagnostics

- Boundary tract GEOID count: 163
- Processed ACS GEOID count: 163
- Matched GEOID count: 163
- Missing tract GEOIDs: none
- Extra ACS GEOIDs: none

## GTFS Diagnostics

GTFS unavailable - no `data_raw/omaha_gtfs.zip` file.


## Census API Key Setup

1. Request a key at `https://api.census.gov/data/key_signup.html`.
2. Open the Census confirmation email and activate the key if the email requires activation.
3. Copy `.env.example` to `.env` in the project root:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Edit `.env` so it contains:

   ```text
   CENSUS_API_KEY=your_real_key_here
   ```

5. Or set the key only for the current PowerShell session:

   ```powershell
   $env:CENSUS_API_KEY = "your_real_key_here"
   python scripts/run_all.py
   ```

6. Do not commit `.env`; it is ignored by `.gitignore`.
7. Rerun `python scripts/run_all.py` and re-check this report.
