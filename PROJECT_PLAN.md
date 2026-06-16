# Phase 1 Project Plan

Project: Opportunity and Affordability in Omaha: A Spatial Mismatch Analysis of Jobs, Wages, Housing, and Access

## Workbook Inventory Findings

The uploaded workbook, `Job_Housing Mismatch.xlsx`, is a preliminary GIS layer inventory. It lists 33 candidate layers covering jobs, housing, resident workers, transportation, commute flows, planning context, and derived mismatch indicators. All rows are currently marked `Available = False`, so Phase 1 is designed as a reproducible public-data prototype rather than a finished local-data integration.

## Phase 1 Scope

The prototype will use census tracts in Douglas County, Nebraska as the primary geography, with tract GEOID as the join key. Omaha-focused interpretation should be possible from the Douglas County tract layer, while later phases can add city boundary clipping, neighborhoods, corridors, zoning, permits, employers, sidewalks, bike facilities, and detailed travel-time surfaces.

## Required Phase 1 Data Sources

1. Census tract boundaries: Census TIGERweb GeoJSON for Nebraska census tracts, filtered to Douglas County.
2. LEHD/LODES workplace area characteristics: Nebraska WAC file, block level rolled up to tract.
3. LEHD/LODES residence area characteristics: Nebraska RAC file, block level rolled up to tract.
4. LEHD/LODES origin-destination flows: Nebraska OD main file, block origins/destinations rolled up to tract.
5. ACS 5-year median rent: ACS variable `B25064_001E`.
6. ACS 5-year median household income: ACS variable `B19013_001E`.
7. ACS households without vehicles: ACS variables `B08201_001E` and `B08201_002E`.
8. Transit routes and stops: GTFS static feed when a feed URL is supplied or can be downloaded.

## Workflow

1. Download or import public datasets into `data_raw/`.
2. Clean tract geometries and create stable tract-level geography files.
3. Process LEHD WAC, RAC, and OD files from census blocks to tracts.
4. Pull ACS indicators and calculate housing affordability fields.
5. Calculate tract-level mismatch metrics and a configurable Spatial Mismatch Score.
6. Export CSV and GeoJSON layers for the dashboard and ArcGIS Online.
7. Serve the dashboard locally with a lightweight static web server.

## Prototype Assumptions

The first prototype uses Douglas County tracts as the analysis geography. LODES wage tiers are monthly earnings categories: low wage is `CE01`, medium wage is `CE02`, and high wage is `CE03`. Affordable rent is estimated as 30 percent of monthly median household income. Transit access is calculated as whether a tract centroid is within a configurable distance of a GTFS stop, defaulting to 0.5 miles. If GTFS is not available, the workflow writes a placeholder and sets transit fields to missing rather than inventing access values.

## Later Phase Candidates From Workbook

Later phases should add major employers, employment centers, industry detail, parcels, housing units by type, affordable housing locations, building permits, zoning, future land use, planning districts, road network, sidewalks, bike network, transit frequency, housing-plus-transportation cost burden, and network-based travel-time surfaces.
