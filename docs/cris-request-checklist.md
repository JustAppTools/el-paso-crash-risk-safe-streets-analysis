# TxDOT CRIS Request Checklist

Use this checklist to request or export the crash data needed for the El Paso Crash Risk & Safe Streets Analysis.

## Recommended Primary Extract

| Setting | Recommended value |
| --- | --- |
| Geography | City = El Paso, Texas |
| Date range | 2017-01-01 through latest complete year available |
| Data level | Crashes |
| Severity | All crashes |
| Output | CSV, table, or geocoded export with latitude/longitude |

## Fields To Include

Request these fields when available:

- Crash ID
- Crash date and crash year
- Latitude and longitude
- City and county
- Street or highway name
- Intersecting street, if available
- Crash severity / worst injury
- Road class and roadway type
- Posted speed limit
- Lighting condition
- Weather condition
- Surface condition
- Manner of collision
- Contributing factors
- Pedestrian involvement flag
- Pedalcyclist involvement flag
- Motorcycle involvement flag
- Alcohol involvement flag
- Speed involvement flag
- Hit-and-run flag

## Optional Focused Extracts

Create focused exports if CRIS query limits make the all-crash extract too large:

- Fatal and suspected serious injury crashes
- Pedestrian-involved crashes
- Pedalcyclist-involved crashes
- Speed-involved crashes
- Alcohol-involved crashes
- Motorcycle-involved crashes

## Local Storage

Place raw CRIS files under:

```text
data/raw/txdot_cris/
```

That folder is ignored by Git. Do not commit raw crash extracts unless the records are confirmed safe, public, aggregated, and free of sensitive details.

## Minimum Useful Dataset

The project can move forward if the CRIS extract has at least:

- Crash ID
- Crash year or date
- Latitude and longitude
- Crash severity
- Pedestrian or pedalcyclist involvement, if vulnerable-road-user analysis is included
- Road name or highway/street context

## Analysis Notes

- Treat fatal and suspected serious injury crashes as KSI.
- Remove records without usable coordinates before spatial analysis.
- Compare results with El Paso Vision Zero's published KSI and High Injury Network maps.
- Document any differences caused by date range, city boundary, roadway ownership, or severity filters.

