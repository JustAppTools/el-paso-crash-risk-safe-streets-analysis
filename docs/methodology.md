# Methodology

## 1. Define Study Area

Start with the City of El Paso boundary for the primary analysis. Use El Paso County or El Paso MPO boundaries only when regional context is needed.

## 2. Acquire Crash Records

Use TxDOT CRIS Query to request public crash data for the selected date range and geography.

Suggested initial extract:

- Geography: City = El Paso, Texas
- Time window: 2017-2024 or latest available multi-year window
- Level: Crashes
- Severity: all severities
- Fields: crash ID, crash date/year, latitude, longitude, city, county, road name, severity, roadway type/class, pedestrian involvement, pedalcyclist involvement, contributing factors, lighting, speed, and alcohol-related indicators where available

Optional focused extracts:

- KSI crashes only
- Pedestrian-involved crashes
- Pedalcyclist-involved crashes
- Speed-involved crashes
- Alcohol-involved crashes

## 3. Prepare Crash Data

Clean and classify crash records before spatial analysis:

- Remove records without usable coordinates.
- Project all layers to a local projected coordinate system suitable for El Paso.
- Classify KSI crashes as fatal or suspected serious injury.
- Flag vulnerable road user crashes: pedestrian and pedalcyclist.
- Create year, month, day-of-week, and time-of-day fields.
- Review duplicate crash IDs.

## 4. Build Spatial Context

Add the following El Paso layers:

- Street centerlines
- Bus routes and bus stops
- Bike lanes
- Schools
- Parks
- MPO environmental justice or disadvantaged-community context
- Census ACS demographic layers, if used

## 5. Analyze Hot Spots and Corridors

Recommended ArcGIS Pro analysis tools:

- Kernel Density for crash-density surfaces
- Optimized Hot Spot Analysis for statistically significant clusters
- Near or Generate Near Table for proximity to schools, bus stops, parks, and bike facilities
- Spatial Join for crash counts by corridor segment, grid cell, tract, or buffer area
- Summarize Within for counts by neighborhood, tract, or priority zone
- Line Locate / snapping workflow for assigning crashes to street centerline segments

## 6. Create Priority Scores

Build a transparent scoring model using weighted indicators such as:

- KSI crash count
- Pedestrian/bicyclist crash count
- Total injury crash count
- Crash density
- Nearby schools
- Nearby bus stops or high-transit corridors
- Missing or disconnected bike facilities
- Disadvantaged-community or low-vehicle household context
- High traffic volume, if traffic-count data is joined

Keep weights simple and documented. Avoid implying precision beyond the data.

## 7. Validate Against Published Vision Zero Materials

Compare project outputs against El Paso Vision Zero maps:

- KSI Crashes
- Vehicle High Injury Network
- Bicycle and Pedestrian High Injury Network
- High Injury Intersections
- Priority Projects

The project does not need to exactly reproduce the City's analysis. Differences should be explained by scope, time window, filters, or scoring choices.

## 8. Final Outputs

Target deliverables:

- Crash hot spot map
- KSI and vulnerable road-user crash map
- High-risk corridor/intersection map
- Safe-streets priority zone map
- Data-source and methodology notes
- Optional ArcGIS Dashboard or StoryMap

