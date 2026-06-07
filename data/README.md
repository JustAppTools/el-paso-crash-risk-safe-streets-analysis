# Data Folder

Raw data is intentionally not committed.

Recommended local structure:

```text
data/
├── raw/            # Raw downloads and CRIS extracts; ignored by Git
├── processed/      # Cleaned analysis-ready datasets; commit only if safe and lightweight
├── cache/          # Temporary downloads; ignored by Git
└── sample/         # Small public sample datasets, if needed
```

## Data Rules

- Do not commit raw crash extracts or crash-report details.
- Do not publish personally identifying crash-record information.
- Commit final summary tables only when they are aggregated and safe for public release.
- Keep large geodatabases, zipped shapefiles, rasters, and exports out of Git unless there is a deliberate reason to publish them.
- Use `data/processed/cris_derived/` for public aggregate crash summaries generated from the Vision Zero collision layer.
