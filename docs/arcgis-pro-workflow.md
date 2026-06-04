# ArcGIS Pro Workflow

This workflow turns the repository scaffold and local downloads into an ArcGIS Pro analysis project.

## 1. Create the ArcGIS Pro Project

Recommended project name:

```text
ElPasoCrashRiskSafeStreets
```

Recommended local project location:

```text
C:\ArcGIS Projects\el-paso-crash-risk-safe-streets-analysis\arcgis
```

Keep ArcGIS project files local unless there is a specific reason to commit them. ArcGIS project folders can contain caches, locks, and generated files that are not useful in Git.

## 2. Add Local City Layers

The City of El Paso layers have been downloaded locally as GeoJSON:

```text
data/raw/city_open_data/
```

Add these layers to the map:

- `EPCenterline.geojson`
- `BusStops.geojson`
- `BusRoutes.geojson`
- `BikeLanes.geojson`
- `Schools.geojson`
- `Parks.geojson`

Then export each layer into the project geodatabase so geoprocessing is faster and more stable.

Suggested geodatabase feature class names:

- `ep_centerline`
- `bus_stops`
- `bus_routes`
- `bike_lanes`
- `schools`
- `parks`

## 3. Add TxDOT CRIS Crash Data

After the CRIS export is available:

1. Place the CSV or exported table in `data/raw/txdot_cris/`.
2. Add the table to ArcGIS Pro.
3. Use XY Table To Point with longitude and latitude fields.
4. Set the input coordinate system to WGS 1984 unless CRIS specifies otherwise.
5. Export the event layer into the project geodatabase as `txdot_cris_crashes`.

## 4. Clean Crash Records

Create a cleaned crash layer:

- Remove records with missing or invalid coordinates.
- Remove duplicate crash IDs.
- Keep only the selected study area.
- Create fields for:
  - `is_ksi`
  - `is_fatal`
  - `is_serious_injury`
  - `is_pedestrian`
  - `is_pedalcyclist`
  - `is_vru`
  - `crash_year`

Suggested output:

```text
crashes_clean
```

## 5. Create Analysis Layers

Recommended derived layers:

- `crash_hotspots`
- `ksi_hotspots`
- `vru_hotspots`
- `high_risk_corridors`
- `high_risk_intersections`
- `school_proximity_crashes`
- `transit_proximity_crashes`
- `bike_facility_gap_crashes`
- `safe_streets_priority_zones`

## 6. Suggested Geoprocessing Tools

| Question | ArcGIS Pro tool |
| --- | --- |
| Where are crash clusters? | Optimized Hot Spot Analysis |
| Where is crash density highest? | Kernel Density |
| Which crashes are near schools, parks, bus stops, or bike lanes? | Near or Generate Near Table |
| Which roads have the most crashes? | Spatial Join or Summarize Nearby |
| Which corridors should be prioritized? | Field Calculator plus weighted scoring |
| How do results compare with Vision Zero? | Overlay and visual comparison |

## 7. Cartographic Outputs

Target map layouts:

- Crash density overview
- KSI crash concentration
- Pedestrian and bicyclist crash concentration
- High-risk corridors and intersections
- Priority safe-streets investment areas

Export final static maps into:

```text
outputs/maps/
```

The `outputs/` folder is ignored by Git by default. Commit only final, lightweight images if they are meant to appear in the public README.

