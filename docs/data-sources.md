# Data Sources

This page tracks candidate datasets for the El Paso Crash Risk & Safe Streets Analysis. Counts and availability should be re-verified before final analysis.

## Crash and Safety Data

| Source | Dataset / Tool | Use | Link |
| --- | --- | --- | --- |
| TxDOT | CRIS Query | Primary crash data source. Query by city, county, date range, severity, pedestrian involvement, pedalcyclist involvement, speed, alcohol, and other factors. | https://cris.dot.state.tx.us/public/Query/app/home |
| TxDOT | Crash Reports and Records | Official guidance on crash records, public query tools, retention, and data visualizations. | https://www.txdot.gov/data-maps/crash-reports-records.html.html |
| TxDOT | CRIS guidance | Confirms CRIS includes location, crash type, roadway conditions, severity, pedestrian/bicyclist crash attributes, contributing factors, traffic count, and other fields. | https://www.txdot.gov/manuals/des/tsp/chapter-2-data-collection/2-3-existing-data-sources/2-3-8-cris.html |
| City of El Paso | Vision Zero Progress & Data | Dashboard and published maps for crash trends, KSI crashes, High Injury Networks, intersections, and priority projects. | https://www.elpasotexas.gov/visionzero/progress-and-data/ |
| City of El Paso | Collision Landscape Summary | Baseline crash trend and KSI analysis for city-managed roads. Useful for validation and methodology comparison. | https://www.elpasotexas.gov/assets/Documents/CoEP/Vision-Zero/Collision-Landscape-Summary_forCity.pdf |
| City of El Paso | KSI Crashes Map | Published KSI crash map and summary. Useful for validation and final narrative context. | https://www.elpasotexas.gov/assets/Documents/CoEP/Vision-Zero/Documents/Maps/KSI-Crashes-2015-2021-Vision-Zero-El-Paso.pdf |

## Public Vision Zero Web Map Services

The interactive web output uses public ArcGIS REST layers referenced by El Paso Vision Zero's public Experience/Dashboard configuration. These services provide the working crash-risk dashboard and the safe aggregate-summary workflow. A separate TxDOT CRIS request/export remains optional for deeper ArcGIS Pro analysis and should stay out of Git.

| Layer | Geometry | Verified count | Use | Feature service |
| --- | --- | ---: | --- | --- |
| El Paso Collisions | Point | 19,693 | Collision density, KSI points, vulnerable-road-user filtering, and summary metrics | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/1 |
| City Boundary | Polygon | 1 | Study-area frame | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/2 |
| HIN - Motor Vehicles | Polyline | 1,666 | Vehicle High Injury Network | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/7 |
| HIN - Bike/Ped | Polyline | 1,456 | Bicycle/pedestrian High Injury Network | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/8 |
| Alta EJ Index | Polygon | 435 | Optional equity-context overlay | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/11 |
| Predictive Modeling Network | Polyline | 26,522 | Optional systemic-risk network overlay | https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Predictive_Modeling/FeatureServer/0 |

## City of El Paso GIS Layers

Candidate layers from City of El Paso Open Data / ArcGIS services:

| Layer | Geometry | Initial use | Feature service |
| --- | --- | --- | --- |
| EPCenterline | Line | Street network, corridor segmentation, crash snapping, road-name context | https://gis.elpasotexas.gov/dev/rest/services/Streets/EPCenterline/FeatureServer/0 |
| BusStops | Point | Transit exposure and pedestrian-access context | https://gis.elpasotexas.gov/dev/rest/services/OpenData/BusStops/FeatureServer/0 |
| BusRoutes | Line | Transit corridor context | https://gis.elpasotexas.gov/dev/rest/services/OpenData/BusRoutes/FeatureServer/0 |
| BikeLanes | Line | Bicycle-facility overlap and safety gaps | https://gis.elpasotexas.gov/dev/rest/services/Streets/BikeLanes/FeatureServer/0 |
| Schools | Point | School-zone proximity and vulnerable-user context | https://gis.elpasotexas.gov/dev/rest/services/OpenData/Schools/FeatureServer/0 |
| Parks | Polygon | Park-access and recreation-trip context | https://gis.elpasotexas.gov/dev/rest/services/Parks/FeatureServer/11 |

City source page:

- https://city-of-el-paso-open-data-coepgis.hub.arcgis.com/
- https://experience.elpasotexas.gov/data.php

## Regional Transportation and Equity Context

| Source | Dataset / Tool | Use | Link |
| --- | --- | --- | --- |
| El Paso MPO | GIS File Listing | Regional shapefiles for transportation planning context. | https://www.elpasompo.org/GeographicInformationSystems |
| El Paso MPO | GIS Maps | Accident fatalities, environmental justice zones, household density, employment/population distribution, ports of entry, hazardous cargo routes, and project maps. | https://www.elpasompo.org/GISMaps |
| TxDOT | Traffic Count Maps and GIS downloads | Traffic exposure context for crash-rate or corridor-priority analysis. | https://www.txdot.gov/data-maps/traffic-count-maps.html |
| U.S. Census Bureau | ACS 5-year estimates | Demographic and equity variables by tract or block group. | https://data.census.gov/ |

## Data Handling Notes

- Do not commit raw CRIS extracts, crash reports, or personally identifying crash-record details.
- Store raw downloads in `data/raw/`, which is ignored by Git.
- Store cleaned public analysis extracts in `data/processed/` only when they are lightweight and safe to publish.
- Store public crash summaries in `data/processed/cris_derived/` only as aggregate tables without coordinates, crash IDs, or case details.
- Final maps, screenshots, and summary tables can be published when they avoid sensitive record-level detail.
