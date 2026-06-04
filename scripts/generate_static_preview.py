"""Generate a static SVG preview from public El Paso Vision Zero layers.

The SVG is meant as a visual milestone for the repository. It fetches public
ArcGIS REST layers at runtime and writes a generalized map image without
storing raw crash records in Git.
"""

from __future__ import annotations

import html
import json
import math
import pathlib
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont


SERVICES = {
    "collisions": "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/1",
    "boundary": "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/2",
    "mv_hin": "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/7",
    "bp_hin": "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/8",
}

OUT_PATH = pathlib.Path("docs/assets/initial-safe-streets-preview.svg")
PNG_OUT_PATH = pathlib.Path("docs/assets/initial-safe-streets-preview.png")
PAGE_SIZE = 2000
WIDTH = 1400
HEIGHT = 900
PANEL_W = 315
MARGIN = 36
MAP_X = PANEL_W + 28
MAP_Y = 36
MAP_W = WIDTH - MAP_X - MARGIN
MAP_H = HEIGHT - MAP_Y - MARGIN
BBOX = (-106.72, 31.54, -106.15, 32.03)
MID_LAT = math.radians((BBOX[1] + BBOX[3]) / 2)
COS_LAT = math.cos(MID_LAT)


def fetch_json(url: str, params: dict[str, str | int]) -> dict:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "el-paso-safe-streets-analysis/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_geojson(service_url: str, params: dict[str, str | int] | None = None) -> dict:
    query = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    query.update(params or {})
    return fetch_json(f"{service_url}/query", query)


def fetch_paged(service_url: str, params: dict[str, str | int] | None = None) -> list[dict]:
    features: list[dict] = []
    offset = 0
    while True:
        page = fetch_geojson(
            service_url,
            {
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
                **(params or {}),
            },
        )
        page_features = page.get("features", [])
        features.extend(page_features)
        if len(page_features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return features


def xy(lon: float, lat: float) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = BBOX
    x = MAP_X + ((lon - min_lon) * COS_LAT / ((max_lon - min_lon) * COS_LAT)) * MAP_W
    y = MAP_Y + (1 - ((lat - min_lat) / (max_lat - min_lat))) * MAP_H
    return x, y


def xy_int(lon: float, lat: float) -> tuple[int, int]:
    x, y = xy(lon, lat)
    return round(x), round(y)


def in_bbox(lon: float, lat: float) -> bool:
    min_lon, min_lat, max_lon, max_lat = BBOX
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def path_from_coords(coords: list) -> str:
    if not coords:
        return ""
    parts = []
    for line in coords:
        if not line:
            continue
        points = [xy(lon, lat) for lon, lat in line if in_bbox(lon, lat)]
        if len(points) < 2:
            continue
        start = points[0]
        rest = " ".join(f"L {x:.1f},{y:.1f}" for x, y in points[1:])
        parts.append(f"M {start[0]:.1f},{start[1]:.1f} {rest}")
    return " ".join(parts)


def is_ksi(feature: dict) -> bool:
    props = feature.get("properties", {})
    return (
        float(props.get("ksi") or 0) > 0
        or float(props.get("death_cnt") or 0) > 0
        or float(props.get("sus_serious_injry_cnt") or 0) > 0
    )


def is_fatal(feature: dict) -> bool:
    return float(feature.get("properties", {}).get("death_cnt") or 0) > 0


def is_vru(feature: dict) -> bool:
    props = feature.get("properties", {})
    mode = f"{props.get('crash_mode') or ''} {props.get('crash_mode_2') or ''}".upper()
    return (
        "PED" in mode
        or "BIKE" in mode
        or "BICYCLE" in mode
        or float(props.get("col_ped_cnt") or 0) > 0
        or float(props.get("col_bic_cnt") or 0) > 0
    )


def line_paths(features: list[dict], color: str, width: float, opacity: float) -> str:
    paths = []
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "LineString":
            coords = [coords]
        path = path_from_coords(coords)
        if path:
            paths.append(
                f'<path d="{path}" fill="none" stroke="{color}" stroke-linecap="round" '
                f'stroke-linejoin="round" stroke-width="{width}" opacity="{opacity}" />'
            )
    return "\n".join(paths)


def boundary_paths(features: list[dict]) -> str:
    paths = []
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        rings = []
        if geometry.get("type") == "Polygon":
            rings = coords
        elif geometry.get("type") == "MultiPolygon":
            rings = [ring for polygon in coords for ring in polygon]
        for ring in rings:
            points = [xy(lon, lat) for lon, lat in ring if in_bbox(lon, lat)]
            if len(points) < 3:
                continue
            start = points[0]
            rest = " ".join(f"L {x:.1f},{y:.1f}" for x, y in points[1:])
            paths.append(
                f'<path d="M {start[0]:.1f},{start[1]:.1f} {rest} Z" '
                'fill="#eef4f0" stroke="#33443b" stroke-width="1.8" opacity="0.78" />'
            )
    return "\n".join(paths)


def point_marks(features: list[dict]) -> str:
    marks = []
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = coords[:2]
        if not in_bbox(lon, lat):
            continue
        x, y = xy(lon, lat)
        if is_fatal(feature):
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="#8d1c23" opacity="0.86" />')
        elif is_ksi(feature):
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#d9483b" opacity="0.72" />')
        elif is_vru(feature):
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#1f9a8a" opacity="0.46" />')
        else:
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.15" fill="#f0a23a" opacity="0.13" />')
    return "\n".join(marks)


def top_streets(features: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for feature in features:
        props = feature.get("properties", {})
        report_street = " ".join(
            value for value in [props.get("rpt_street_name"), props.get("rpt_street_sfx")] if value
        ).strip()
        street = report_street or props.get("street_name") or "Unknown street"
        counts[street] = counts.get(street, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:6]


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_lines(draw: ImageDraw.ImageDraw, features: list[dict], color: tuple[int, int, int, int], width: int) -> None:
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "LineString":
            coords = [coords]
        for line in coords:
            points = [xy_int(lon, lat) for lon, lat in line if in_bbox(lon, lat)]
            if len(points) >= 2:
                draw.line(points, fill=color, width=width, joint="curve")


def draw_boundary(draw: ImageDraw.ImageDraw, features: list[dict]) -> None:
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        rings = []
        if geometry.get("type") == "Polygon":
            rings = coords
        elif geometry.get("type") == "MultiPolygon":
            rings = [ring for polygon in coords for ring in polygon]
        for ring in rings:
            points = [xy_int(lon, lat) for lon, lat in ring if in_bbox(lon, lat)]
            if len(points) >= 3:
                draw.polygon(points, fill=(238, 244, 240, 190), outline=(51, 68, 59, 160))


def draw_preview_png(
    collisions: list[dict],
    boundary: list[dict],
    mv_hin: list[dict],
    bp_hin: list[dict],
    total: int,
    ksi: int,
    vru: int,
    fatal: int,
    streets: list[tuple[str, int]],
) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f8faf7")
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rounded_rectangle((MAP_X, MAP_Y, MAP_X + MAP_W, MAP_Y + MAP_H), radius=8, fill="#dfe7df", outline="#c9d2ca")
    draw_boundary(draw, boundary)
    draw_lines(draw, mv_hin, (217, 72, 59, 205), 5)
    draw_lines(draw, bp_hin, (31, 154, 138, 215), 5)

    for feature in collisions:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = coords[:2]
        if not in_bbox(lon, lat):
            continue
        x, y = xy_int(lon, lat)
        if is_fatal(feature):
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(141, 28, 35, 220))
        elif is_ksi(feature):
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(217, 72, 59, 178))
        elif is_vru(feature):
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(31, 154, 138, 112))
        else:
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(240, 162, 58, 54))

    kicker = get_font(13, True)
    title = get_font(30, True)
    body = get_font(15)
    metric_label = get_font(12, True)
    metric_value = get_font(31, True)
    street_font = get_font(14, True)
    small_bold = get_font(12, True)
    legend_font = get_font(13, True)

    draw.text((36, 44), "EL PASO, TEXAS", fill="#2f6fb2", font=kicker)
    draw.text((36, 76), "Crash Risk &", fill="#172638", font=title)
    draw.text((36, 112), "Safe Streets", fill="#172638", font=title)
    draw.text((36, 154), "Initial visual output using public", fill="#5f6b76", font=body)
    draw.text((36, 176), "Vision Zero collision and HIN layers.", fill="#5f6b76", font=body)

    metrics = [("CRASHES", total), ("KSI", ksi), ("BIKE/PED", vru), ("FATAL", fatal)]
    positions = [(36, 234), (181, 234), (36, 320), (181, 320)]
    for (label, value), (x, y) in zip(metrics, positions):
        draw.text((x, y), label, fill="#5f6b76", font=metric_label)
        draw.text((x, y + 18), f"{value:,}", fill="#172638", font=metric_value)

    draw.text((36, 402), "TOP STREETS", fill="#2f6fb2", font=kicker)
    for idx, (street, count) in enumerate(streets):
        y = 432 + idx * 42
        draw.text((36, y), f"{idx + 1}. {street[:28]}", fill="#26333f", font=street_font)
        draw.text((36, y + 18), f"{count:,} crashes", fill="#d9483b", font=small_bold)

    legend_x = MAP_X + 18
    legend_y = MAP_Y + MAP_H - 122
    draw.rounded_rectangle((legend_x, legend_y, legend_x + 226, legend_y + 98), radius=8, fill=(255, 255, 255, 240), outline="#d8ded8")
    draw.ellipse((legend_x + 13, legend_y + 19, legend_x + 23, legend_y + 29), fill="#d9483b")
    draw.text((legend_x + 34, legend_y + 16), "KSI crash", fill="#23313d", font=legend_font)
    draw.ellipse((legend_x + 13, legend_y + 45, legend_x + 23, legend_y + 55), fill="#1f9a8a")
    draw.text((legend_x + 34, legend_y + 42), "Bike/Ped crash", fill="#23313d", font=legend_font)
    draw.line((legend_x + 13, legend_y + 75, legend_x + 28, legend_y + 75), fill="#d9483b", width=4)
    draw.text((legend_x + 34, legend_y + 68), "High Injury Network", fill="#23313d", font=legend_font)

    PNG_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(PNG_OUT_PATH)


def main() -> int:
    collision_fields = ",".join(
        [
            "OBJECTID",
            "year",
            "crash_mode",
            "crash_mode_2",
            "ksi",
            "death_cnt",
            "sus_serious_injry_cnt",
            "col_bic_cnt",
            "col_ped_cnt",
            "rpt_street_name",
            "rpt_street_sfx",
            "street_name",
        ]
    )
    collisions = fetch_paged(SERVICES["collisions"], {"outFields": collision_fields})
    boundary = fetch_geojson(SERVICES["boundary"]).get("features", [])
    mv_hin = fetch_geojson(SERVICES["mv_hin"]).get("features", [])
    bp_hin = fetch_geojson(SERVICES["bp_hin"]).get("features", [])

    total = len(collisions)
    ksi = sum(1 for feature in collisions if is_ksi(feature))
    fatal = sum(1 for feature in collisions if is_fatal(feature))
    vru = sum(1 for feature in collisions if is_vru(feature))
    streets = top_streets(collisions)

    street_rows = []
    for idx, (street, count) in enumerate(streets):
        y = 432 + idx * 42
        street_rows.append(
            f'<text x="36" y="{y}" class="street-name">{idx + 1}. {html.escape(street[:28])}</text>'
            f'<text x="36" y="{y + 18}" class="street-count">{count:,} crashes</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <style>
    .bg {{ fill: #f8faf7; }}
    .map-bg {{ fill: #dfe7df; }}
    .title {{ fill: #172638; font: 800 30px Arial, sans-serif; }}
    .kicker {{ fill: #2f6fb2; font: 800 13px Arial, sans-serif; letter-spacing: 1px; }}
    .body {{ fill: #5f6b76; font: 15px Arial, sans-serif; }}
    .metric-label {{ fill: #5f6b76; font: 700 12px Arial, sans-serif; }}
    .metric-value {{ fill: #172638; font: 800 31px Arial, sans-serif; }}
    .street-name {{ fill: #26333f; font: 700 14px Arial, sans-serif; }}
    .street-count {{ fill: #d9483b; font: 800 12px Arial, sans-serif; }}
    .legend {{ fill: #23313d; font: 700 13px Arial, sans-serif; }}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" />
  <rect class="map-bg" x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" rx="8" />
  <text class="kicker" x="36" y="58">EL PASO, TEXAS</text>
  <text class="title" x="36" y="98">Crash Risk &amp;</text>
  <text class="title" x="36" y="134">Safe Streets</text>
  <text class="body" x="36" y="168">Initial visual output using public</text>
  <text class="body" x="36" y="190">Vision Zero collision and HIN layers.</text>
  <g transform="translate(36 234)">
    <text class="metric-label" x="0" y="0">CRASHES</text>
    <text class="metric-value" x="0" y="37">{total:,}</text>
    <text class="metric-label" x="145" y="0">KSI</text>
    <text class="metric-value" x="145" y="37">{ksi:,}</text>
    <text class="metric-label" x="0" y="84">BIKE/PED</text>
    <text class="metric-value" x="0" y="121">{vru:,}</text>
    <text class="metric-label" x="145" y="84">FATAL</text>
    <text class="metric-value" x="145" y="121">{fatal:,}</text>
  </g>
  <text class="kicker" x="36" y="402">TOP STREETS</text>
  {"".join(street_rows)}
  <g clip-path="url(#mapClip)">
    <defs>
      <clipPath id="mapClip"><rect x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" rx="8" /></clipPath>
    </defs>
    {boundary_paths(boundary)}
    {line_paths(mv_hin, "#d9483b", 4.2, 0.78)}
    {line_paths(bp_hin, "#1f9a8a", 4.0, 0.82)}
    {point_marks(collisions)}
  </g>
  <rect x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{MAP_H}" rx="8" fill="none" stroke="#c9d2ca" />
  <g transform="translate({MAP_X + 18} {MAP_Y + MAP_H - 122})">
    <rect x="0" y="0" width="226" height="98" rx="8" fill="#ffffff" opacity="0.94" stroke="#d8ded8" />
    <circle cx="18" cy="24" r="5" fill="#d9483b" /><text class="legend" x="34" y="29">KSI crash</text>
    <circle cx="18" cy="50" r="5" fill="#1f9a8a" /><text class="legend" x="34" y="55">Bike/Ped crash</text>
    <line x1="13" y1="75" x2="28" y2="75" stroke="#d9483b" stroke-width="4" /><text class="legend" x="34" y="80">High Injury Network</text>
  </g>
</svg>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg, encoding="utf-8")
    draw_preview_png(collisions, boundary, mv_hin, bp_hin, total, ksi, vru, fatal, streets)
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {PNG_OUT_PATH}")
    print(f"Metrics: {total:,} crashes; {ksi:,} KSI; {vru:,} bike/ped; {fatal:,} fatal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
