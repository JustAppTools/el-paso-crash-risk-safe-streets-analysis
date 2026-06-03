# Scripts

Helper scripts for validating public data sources and preparing GIS inputs.

Current scripts:

- `verify_city_open_data.py`: queries candidate City of El Paso ArcGIS FeatureServer layers and prints basic availability metadata.
- `download_city_open_data.py`: downloads candidate City of El Paso ArcGIS FeatureServer layers as GeoJSON into `data/raw/city_open_data/`.

These scripts are not a replacement for ArcGIS Pro workflows. They are lightweight helpers for repeatability and documentation.
