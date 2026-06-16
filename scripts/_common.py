from __future__ import annotations

import csv
import gzip
import json
import math
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data_raw"
DATA_PROCESSED = PROJECT_ROOT / "data_processed"
OUTPUTS = PROJECT_ROOT / "outputs"
OUTPUT_CSV = OUTPUTS / "csv"
OUTPUT_GEOJSON = OUTPUTS / "geojson"
OUTPUT_MAPS = OUTPUTS / "maps"

STATE_FIPS = os.getenv("STATE_FIPS", "31")
COUNTY_FIPS = os.getenv("COUNTY_FIPS", "055")
COUNTY_GEOID = f"{STATE_FIPS}{COUNTY_FIPS}"
LODES_YEAR = os.getenv("LODES_YEAR", "2022")
ACS_YEAR = os.getenv("ACS_YEAR", "2024")


def load_project_env() -> None:
    """Load simple KEY=VALUE pairs from project .env without overriding the shell."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_dirs() -> None:
    for path in [DATA_RAW, DATA_PROCESSED, OUTPUT_CSV, OUTPUT_GEOJSON, OUTPUT_MAPS]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def download(url: str, path: Path, timeout: int = 90) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "job-housing-mismatch-omaha/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, path.open("wb") as f:
            shutil.copyfileobj(response, f)
        return {"ok": True, "url": url, "path": str(path), "bytes": path.stat().st_size}
    except Exception as exc:
        placeholder = path.with_suffix(path.suffix + ".placeholder.txt")
        placeholder.write_text(
            f"Download failed for:\n{url}\n\nError:\n{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        return {"ok": False, "url": url, "path": str(path), "error": f"{type(exc).__name__}: {exc}"}


def tigerweb_tract_url(layer_id: int = 8) -> str:
    params = {
        "where": f"STATE='{STATE_FIPS}' AND COUNTY='{COUNTY_FIPS}'",
        "outFields": "GEOID,NAME,STATE,COUNTY,TRACT",
        "outSR": "4326",
        "f": "geojson",
        "returnGeometry": "true",
    }
    return (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        f"TIGERweb/Tracts_Blocks/MapServer/{layer_id}/query?"
        + urllib.parse.urlencode(params)
    )


def lodes_url(kind: str) -> str:
    # kind is one of wac, rac, od. JT00 means all jobs, all primary/private/federal.
    filename = f"ne_{kind}_{'main_' if kind == 'od' else 'S000_'}JT00_{LODES_YEAR}.csv.gz"
    return f"https://lehd.ces.census.gov/data/lodes/LODES8/ne/{kind}/{filename}"


def tract_from_block(value: object) -> str:
    text = str(value).split(".")[0].zfill(15)
    return text[:11]


def flatten_positions(geometry: dict) -> list[tuple[float, float]]:
    coords = geometry.get("coordinates", [])
    positions: list[tuple[float, float]] = []

    def walk(node):
        if not node:
            return
        if isinstance(node[0], (int, float)):
            positions.append((float(node[0]), float(node[1])))
        else:
            for child in node:
                walk(child)

    walk(coords)
    return positions


def centroid_from_geometry(geometry: dict) -> tuple[float | None, float | None]:
    positions = flatten_positions(geometry)
    if not positions:
        return None, None
    lon = sum(p[0] for p in positions) / len(positions)
    lat = sum(p[1] for p in positions) / len(positions)
    return lon, lat


def _ring_area_sq_meters(ring: list[list[float]]) -> float:
    if len(ring) < 4:
        return 0.0
    lat0 = math.radians(sum(point[1] for point in ring) / len(ring))
    meters_per_deg_lat = 111_132.0
    meters_per_deg_lon = 111_320.0 * math.cos(lat0)
    xy = [(point[0] * meters_per_deg_lon, point[1] * meters_per_deg_lat) for point in ring]
    area = 0.0
    for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def area_sq_miles(geometry: dict) -> float | None:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if not coords:
        return None
    polygons = [coords] if gtype == "Polygon" else coords if gtype == "MultiPolygon" else []
    total = 0.0
    for polygon in polygons:
        if not polygon:
            continue
        outer = _ring_area_sq_meters(polygon[0])
        holes = sum(_ring_area_sq_meters(ring) for ring in polygon[1:])
        total += max(0.0, outer - holes)
    return total / 2_589_988.110336 if total else None


def haversine_miles(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def read_gtfs_stops(gtfs_zip: Path) -> list[tuple[str, float, float]]:
    stops: list[tuple[str, float, float]] = []
    if not gtfs_zip.exists():
        return stops
    with ZipFile(gtfs_zip) as zf:
        with zf.open("stops.txt") as raw:
            reader = csv.DictReader(line.decode("utf-8-sig") for line in raw)
            for row in reader:
                try:
                    stops.append((row.get("stop_id", ""), float(row["stop_lon"]), float(row["stop_lat"])))
                except (KeyError, TypeError, ValueError):
                    continue
    return stops


def read_gtfs_stop_routes(gtfs_zip: Path) -> dict[str, set[str]]:
    """Return stop_id -> route_ids using GTFS stop_times, trips, and routes.

    This intentionally stays lightweight for the Phase 1 atlas. It counts
    distinct routes serving stops near each tract, not full network reachability.
    """
    if not gtfs_zip.exists():
        return {}
    try:
        with ZipFile(gtfs_zip) as zf:
            with zf.open("trips.txt") as raw:
                trips = {
                    row["trip_id"]: row["route_id"]
                    for row in csv.DictReader(line.decode("utf-8-sig") for line in raw)
                    if row.get("trip_id") and row.get("route_id")
                }
            stop_routes: dict[str, set[str]] = {}
            with zf.open("stop_times.txt") as raw:
                for row in csv.DictReader(line.decode("utf-8-sig") for line in raw):
                    stop_id = row.get("stop_id")
                    route_id = trips.get(row.get("trip_id", ""))
                    if stop_id and route_id:
                        stop_routes.setdefault(stop_id, set()).add(route_id)
        return stop_routes
    except Exception:
        return {}


def open_lodes_csv(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", newline="")
