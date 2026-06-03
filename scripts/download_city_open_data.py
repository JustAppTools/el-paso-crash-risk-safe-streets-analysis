"""Download candidate City of El Paso feature services as GeoJSON.

Outputs are written to data/raw/city_open_data/, which is ignored by Git.
Run this from the repository root:

    python scripts/download_city_open_data.py

Use --layers to download a subset:

    python scripts/download_city_open_data.py --layers BusStops Schools
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time
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

OUT_DIR = pathlib.Path("data/raw/city_open_data")
PAGE_SIZE = 2000


def get_json(url: str, params: dict[str, str | int]) -> dict:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "el-paso-safe-streets-analysis/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_count(layer_url: str) -> int:
    payload = get_json(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "returnCountOnly": "true",
            "f": "json",
        },
    )
    return int(payload["count"])


def download_layer(name: str, layer_url: str, out_dir: pathlib.Path) -> pathlib.Path:
    count = get_count(layer_url)
    features = []

    for offset in range(0, count, PAGE_SIZE):
        payload = get_json(
            f"{layer_url}/query",
            {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true",
                "f": "geojson",
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
            },
        )
        features.extend(payload.get("features", []))
        print(f"{name}: downloaded {min(offset + PAGE_SIZE, count)} of {count}")
        time.sleep(0.2)

    output = {
        "type": "FeatureCollection",
        "name": name,
        "features": features,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{name}.geojson"
    output_path.write_text(json.dumps(output), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--layers",
        nargs="+",
        choices=sorted(LAYERS),
        default=sorted(LAYERS),
        help="Layer names to download. Defaults to all candidate layers.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    for name in args.layers:
        output_path = download_layer(name, LAYERS[name], OUT_DIR)
        print(f"Wrote {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

