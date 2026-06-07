"""Build safe aggregate summaries from public CRIS-derived collision data.

The public El Paso Vision Zero collision layer contains fields sourced from
TxDOT CRIS-style crash records. This script queries the public layer without
geometry and writes aggregate summaries only. It does not save raw crash
records, coordinates, crash IDs, case IDs, or personally identifying details.
"""

from __future__ import annotations

import csv
import json
import pathlib
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


COLLISION_LAYER_URL = (
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/"
    "El_Paso_Dashboard_Data/FeatureServer/1"
)

OUT_DIR = pathlib.Path("data/processed/cris_derived")
PAGE_SIZE = 500
MAX_RETRIES = 4

FIELDS = [
    "year",
    "crash_mode",
    "crash_mode_2",
    "crash_sev_id",
    "death_cnt",
    "sus_serious_injry_cnt",
    "tot_injry_cnt",
    "col_bic_cnt",
    "col_ped_cnt",
    "bike_accident",
    "ped_accident",
    "rpt_street_name",
    "rpt_street_sfx",
    "street_name",
    "posted_speed_group",
    "dui",
    "hit_and_run",
]


def get_json(url: str, params: dict[str, str | int]) -> dict[str, Any]:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "el-paso-safe-streets-analysis/0.1"},
    )
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - retry diagnostic script
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(2 * attempt)
    raise RuntimeError(f"Unable to fetch {url} after {MAX_RETRIES} attempts: {last_error}") from last_error


def fetch_public_collision_attributes() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0

    while True:
        payload = get_json(
            f"{COLLISION_LAYER_URL}/query",
            {
                "where": "1=1",
                "outFields": ",".join(FIELDS),
                "returnGeometry": "false",
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
            },
        )
        if "error" in payload:
            raise RuntimeError(f"ArcGIS query failed: {payload['error']}")
        features = payload.get("features", [])
        records.extend(feature.get("attributes", {}) for feature in features)
        print(f"Fetched {len(records):,} public collision records...")

        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return records


def as_number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def flag_text(value: Any) -> str:
    return str(value or "").strip().upper()


def street_name(record: dict[str, Any]) -> str:
    report_name = " ".join(
        str(value).strip()
        for value in (record.get("rpt_street_name"), record.get("rpt_street_sfx"))
        if value not in (None, "")
    ).strip()
    return report_name or str(record.get("street_name") or "Unknown street").strip()


def crash_mode(record: dict[str, Any]) -> str:
    return str(record.get("crash_mode") or record.get("crash_mode_2") or "Unknown").strip()


def is_ksi(record: dict[str, Any]) -> bool:
    return (
        as_number(record.get("death_cnt")) > 0
        or as_number(record.get("sus_serious_injry_cnt")) > 0
        or flag_text(record.get("crash_sev_id")) in {"FATAL", "SUSPECTED SERIOUS INJURY"}
    )


def is_fatal(record: dict[str, Any]) -> bool:
    return as_number(record.get("death_cnt")) > 0 or flag_text(record.get("crash_sev_id")) == "FATAL"


def is_bike(record: dict[str, Any]) -> bool:
    mode = f"{record.get('crash_mode') or ''} {record.get('crash_mode_2') or ''}".upper()
    return "BIKE" in mode or "BICYCLE" in mode or as_number(record.get("col_bic_cnt")) > 0 or flag_text(record.get("bike_accident")) == "Y"


def is_ped(record: dict[str, Any]) -> bool:
    mode = f"{record.get('crash_mode') or ''} {record.get('crash_mode_2') or ''}".upper()
    return "PED" in mode or as_number(record.get("col_ped_cnt")) > 0 or flag_text(record.get("ped_accident")) == "Y"


def is_vru(record: dict[str, Any]) -> bool:
    return is_bike(record) or is_ped(record)


def blank_metrics() -> dict[str, float]:
    return {
        "total_crashes": 0,
        "ksi_crashes": 0,
        "fatal_crashes": 0,
        "bike_ped_crashes": 0,
        "bike_crashes": 0,
        "pedestrian_crashes": 0,
        "reported_injuries": 0,
        "reported_serious_injuries": 0,
        "reported_deaths": 0,
    }


def add_record(metrics: dict[str, float], record: dict[str, Any]) -> None:
    metrics["total_crashes"] += 1
    metrics["ksi_crashes"] += int(is_ksi(record))
    metrics["fatal_crashes"] += int(is_fatal(record))
    metrics["bike_ped_crashes"] += int(is_vru(record))
    metrics["bike_crashes"] += int(is_bike(record))
    metrics["pedestrian_crashes"] += int(is_ped(record))
    metrics["reported_injuries"] += as_number(record.get("tot_injry_cnt"))
    metrics["reported_serious_injuries"] += as_number(record.get("sus_serious_injry_cnt"))
    metrics["reported_deaths"] += as_number(record.get("death_cnt"))


def write_rows(path: pathlib.Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def metrics_row(group: Any, metrics: dict[str, float], group_field: str) -> dict[str, Any]:
    row: dict[str, Any] = {group_field: group}
    for key, value in metrics.items():
        row[key] = int(value)
    return row


def build_outputs(records: list[dict[str, Any]]) -> None:
    summary_total = blank_metrics()
    by_year: defaultdict[int, dict[str, float]] = defaultdict(blank_metrics)
    by_mode: defaultdict[str, dict[str, float]] = defaultdict(blank_metrics)
    by_street: defaultdict[str, dict[str, float]] = defaultdict(blank_metrics)
    by_speed: defaultdict[str, dict[str, float]] = defaultdict(blank_metrics)
    by_year_mode: defaultdict[tuple[int, str], dict[str, float]] = defaultdict(blank_metrics)
    severity_counts: Counter[str] = Counter()

    for record in records:
        year = int(as_number(record.get("year"))) if as_number(record.get("year")) else 0
        mode = crash_mode(record)
        street = street_name(record)
        speed_group = str(record.get("posted_speed_group") or "Unknown")
        severity = str(record.get("crash_sev_id") or "Unknown")

        add_record(summary_total, record)
        add_record(by_year[year], record)
        add_record(by_mode[mode], record)
        add_record(by_street[street], record)
        add_record(by_speed[speed_group], record)
        add_record(by_year_mode[(year, mode)], record)
        severity_counts[severity] += 1

    metric_fields = list(blank_metrics())

    write_rows(
        OUT_DIR / "summary_total.csv",
        ["scope", *metric_fields],
        [metrics_row("El Paso public Vision Zero collision layer", summary_total, "scope")],
    )

    write_rows(
        OUT_DIR / "summary_by_year.csv",
        ["year", *metric_fields],
        [metrics_row(year, metrics, "year") for year, metrics in sorted(by_year.items()) if year],
    )

    write_rows(
        OUT_DIR / "summary_by_mode.csv",
        ["crash_mode", *metric_fields],
        [metrics_row(mode, metrics, "crash_mode") for mode, metrics in sorted(by_mode.items())],
    )

    write_rows(
        OUT_DIR / "summary_by_year_mode.csv",
        ["year", "crash_mode", *metric_fields],
        [
            {"year": year, "crash_mode": mode, **{key: int(value) for key, value in metrics.items()}}
            for (year, mode), metrics in sorted(by_year_mode.items())
            if year
        ],
    )

    write_rows(
        OUT_DIR / "summary_by_posted_speed_group.csv",
        ["posted_speed_group", *metric_fields],
        [metrics_row(group, metrics, "posted_speed_group") for group, metrics in sorted(by_speed.items())],
    )

    top_streets = sorted(
        by_street.items(),
        key=lambda item: (item[1]["total_crashes"], item[1]["ksi_crashes"]),
        reverse=True,
    )[:50]
    write_rows(
        OUT_DIR / "top_streets_by_volume.csv",
        ["street_name", *metric_fields],
        [metrics_row(street, metrics, "street_name") for street, metrics in top_streets],
    )

    write_rows(
        OUT_DIR / "summary_by_severity.csv",
        ["crash_severity", "total_crashes"],
        [
            {"crash_severity": severity, "total_crashes": count}
            for severity, count in sorted(severity_counts.items(), key=lambda item: item[1], reverse=True)
        ],
    )

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_layer": COLLISION_LAYER_URL,
        "source_record_count": len(records),
        "privacy_note": (
            "Outputs are aggregated summary tables only. Raw crash records, coordinates, "
            "crash IDs, case IDs, and personally identifying details are not stored in this repository."
        ),
        "classification_note": (
            "KSI is classified from fatal/death counts and suspected serious injury counts. "
            "Bike/pedestrian flags are derived from crash mode and available bike/ped count fields."
        ),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> int:
    records = fetch_public_collision_attributes()
    build_outputs(records)
    print(f"Wrote aggregate summaries to {OUT_DIR}")
    print(f"Aggregated {len(records):,} public collision records without saving raw records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
