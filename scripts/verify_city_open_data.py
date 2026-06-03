"""Verify candidate City of El Paso Open Data feature services.

This script uses only the Python standard library so it can run in a normal
Python environment or the ArcGIS Pro Python environment.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request


LAYERS = {
    "EPCenterline": "https://gis.elpasotexas.gov/dev/rest/services/Streets/EPCenterline/FeatureServer/0",
    "BusStops": "https://gis.elpasotexas.gov/dev/rest/services/OpenData/BusStops/FeatureServer/0",
    "BusRoutes": "https://gis.elpasotexas.gov/dev/rest/services/OpenData/BusRoutes/FeatureServer/0",
    "BikeLanes": "https://gis.elpasotexas.gov/dev/rest/services/Streets/BikeLanes/FeatureServer/0",
    "Schools": "https://gis.elpasotexas.gov/dev/rest/services/OpenData/Schools/FeatureServer/0",
    "Parks": "https://gis.elpasotexas.gov/dev/rest/services/Parks/FeatureServer/11",
}


def get_json(url: str, params: dict[str, str] | None = None) -> dict:
    query = urllib.parse.urlencode(params or {})
    request_url = f"{url}?{query}" if query else url
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "el-paso-safe-streets-analysis/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_count(layer_url: str) -> int | str:
    payload = get_json(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "returnCountOnly": "true",
            "f": "json",
        },
    )
    return payload.get("count", "unknown")


def main() -> int:
    print("City of El Paso Open Data layer check")
    print("=" * 42)

    for name, url in LAYERS.items():
        try:
            metadata = get_json(url, {"f": "json"})
            count = get_count(url)
            geometry_type = metadata.get("geometryType", "unknown")
            service_name = metadata.get("name", name)
            print(f"{name}: {count} features | {geometry_type} | {service_name}")
        except Exception as exc:  # noqa: BLE001 - diagnostic script should keep going
            print(f"{name}: failed - {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
