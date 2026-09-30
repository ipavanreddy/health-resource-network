"""Travel times between facilities: Google Maps Routes API (real) or haversine estimate (demo)."""
import logging
import math

import httpx

from app.config import settings
from app.integrations.modes import routes_enabled

log = logging.getLogger(__name__)

ROUTES_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROAD_FACTOR = 1.35
RURAL_SPEED_KMH = 35.0


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def estimate_minutes(a: tuple[float, float], b: tuple[float, float]) -> float:
    return round(haversine_km(a, b) * ROAD_FACTOR / RURAL_SPEED_KMH * 60, 1)


def _routes_matrix(origins: list[tuple[float, float]], dests: list[tuple[float, float]]) -> list[list[float | None]]:
    def wp(p):
        return {"waypoint": {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}}

    res = httpx.post(
        ROUTES_URL,
        json={"origins": [wp(o) for o in origins], "destinations": [wp(d) for d in dests], "travelMode": "DRIVE"},
        headers={"X-Goog-Api-Key": settings.maps_api_key,
                 "X-Goog-FieldMask": "originIndex,destinationIndex,duration,condition"},
        timeout=20,
    )
    res.raise_for_status()
    out: list[list[float | None]] = [[None] * len(dests) for _ in origins]
    for el in res.json():
        if el.get("condition") == "ROUTE_EXISTS" and "duration" in el:
            out[el.get("originIndex", 0)][el.get("destinationIndex", 0)] = round(
                float(el["duration"].rstrip("s")) / 60, 1)
    return out


Point = tuple[float, float]


def travel_matrix(origins: list[Point], dests: list[Point]) -> tuple[list[list[float]], str]:
    """Minutes from each origin to each destination. Returns (matrix, mode) with mode 'routes_api' or 'haversine'."""
    if routes_enabled() and origins and dests and len(origins) * len(dests) <= 625:
        try:
            m = _routes_matrix(origins, dests)
            full = [[v if v is not None else estimate_minutes(o, d) for v, d in zip(row, dests, strict=True)]
                    for row, o in zip(m, origins, strict=True)]
            return full, "routes_api"
        except Exception as exc:  # noqa: BLE001 - fall back to estimate, never break the journey
            log.warning("Routes API failed, using haversine estimate: %s", exc)
    return [[estimate_minutes(o, d) for d in dests] for o in origins], "haversine"
