# CRIS-Derived Aggregate Workflow

This project can move forward without committing raw TxDOT CRIS extracts. The interactive dashboard already uses the public El Paso Vision Zero collision layer, which contains CRIS-style crash attributes exposed through a public ArcGIS REST service.

The reproducible aggregate workflow is:

```powershell
python scripts/build_cris_derived_summaries.py
```

The script queries the public collision layer with `returnGeometry=false`, then writes summary tables under:

```text
data/processed/cris_derived/
```

Expected outputs:

- `summary_total.csv`
- `summary_by_year.csv`
- `summary_by_mode.csv`
- `summary_by_year_mode.csv`
- `summary_by_posted_speed_group.csv`
- `top_streets_by_volume.csv`
- `summary_by_severity.csv`
- `metadata.json`

## Privacy Position

The workflow does not save raw crash records, coordinates, crash IDs, case IDs, or personally identifying crash-report details. It only publishes aggregate tables that are appropriate for a public portfolio repository.

Raw CRIS exports can still be requested for a deeper ArcGIS Pro analysis, but those files belong under ignored `data/raw/txdot_cris/` storage and should not be committed.

## Availability Note

The aggregate script depends on the public Vision Zero ArcGIS service being reachable at runtime. If the service times out, rerun the script later; the repository still documents the exact source layer, fields, output tables, and privacy limits.
