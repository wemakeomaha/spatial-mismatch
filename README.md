# Opportunity and Spatial Mismatch Atlas for Omaha

Phase 1 planning/research prototype for **Opportunity and Affordability in Omaha: A Spatial Mismatch Analysis of Jobs, Wages, Housing, and Access**.

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
- Affordable rent is 30 percent of the monthly median household income.
- Rent burden uses ACS gross-rent-as-percentage-of-income categories at or above 30 percent.
- Transit access uses the tract centroid proximity to GTFS stops, stop counts, and nearby route counts when GTFS is available.
