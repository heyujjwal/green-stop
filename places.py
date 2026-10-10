import csv
import json
import math
import os
from urllib.parse import urlencode

import requests

from config import CACHE_FILE, CSV_FILE, HEADERS, STATIONS


# ---------- cache ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


# ---------- your curated spots ----------
def load_spots(path=CSV_FILE):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["lat"] = float(r["lat"])
        r["lon"] = float(r["lon"])
    return rows


SPOTS = load_spots()


# ---------- geocoding ----------
def geocode(place):
    """Accepts 'lat,lon' (works offline) or any place name (needs internet)."""
    place = place.strip()
    try:
        lat, lon = [float(x) for x in place.split(",")]
        return lat, lon
    except ValueError:
        pass
    if place in STATIONS:
        return STATIONS[place]
    cache = load_cache()
    key = "geo:" + place.lower()
    if key in cache:
        return tuple(cache[key])
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": place, "format": "json", "limit": 1},
                     headers=HEADERS, timeout=8).json()
    if not r:
        return None
    result = (float(r[0]["lat"]), float(r[0]["lon"]))
    cache[key] = result
    save_cache(cache)
    return result


def reverse_address(lat, lon):
    """Full address from coordinates (OSM Nominatim). Cached for offline use."""
    cache = load_cache()
    key = f"rev:{round(lat, 4)},{round(lon, 4)}"
    if key in cache:
        return cache[key]
    try:
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
                         params={"lat": lat, "lon": lon, "format": "json", "zoom": 18},
                         headers=HEADERS, timeout=6).json()
        addr = r.get("display_name", "")
    except Exception:
        return ""
    if addr:
        cache[key] = addr
        save_cache(cache)
    return addr


# ---------- OpenStreetMap spots ----------
def osm_spots(lat, lon, radius_m):
    """Parks, gardens, nature reserves, beaches near a point (cached)."""
    cache = load_cache()
    key = f"osm:{round(lat, 3)},{round(lon, 3)},{radius_m // 250}"
    if key in cache:
        return cache[key]
    query = f"""
    [out:json][timeout:25];
    (
      nwr["leisure"~"park|garden|nature_reserve"]["name"](around:{radius_m},{lat},{lon});
      nwr["natural"="beach"]["name"](around:{radius_m},{lat},{lon});
    );
    out center tags 40;
    """
    data = requests.post("https://overpass-api.de/api/interpreter",
                         data={"data": query}, headers=HEADERS, timeout=30).json()
    spots = []
    for e in data["elements"]:
        t = e.get("tags", {})
        c = e.get("center", e)
        if "lat" not in c:
            continue
        spots.append({
            "name": t["name"],
            "type": t.get("leisure") or t.get("natural"),
            "lat": c["lat"], "lon": c["lon"],
            "tip": "Found via OpenStreetMap",
        })
    cache[key] = spots
    save_cache(cache)
    return spots


# ---------- distance + matching ----------
def distance_km(lat1, lon1, lat2, lon2):
    """Haversine: straight-line distance between two GPS points."""
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def walk_minutes(km):
    # x1.3 because real streets aren't straight; 5 km/h walking speed
    return round(km * 1.3 / 5 * 60)


def find_spots(lat, lon, minutes):
    max_one_way = (minutes - 5) / 2
    radius_m = int(max_one_way / 60 * 5 / 1.3 * 1000)
    if radius_m < 100:
        return []

    candidates = list(SPOTS)
    try:
        candidates += osm_spots(lat, lon, radius_m)
    except Exception as e:
        print("OSM unavailable, using CSV only:", e)

    options, seen = [], set()
    for s in candidates:
        if s["name"] in seen:
            continue
        one_way = walk_minutes(distance_km(lat, lon, s["lat"], s["lon"]))
        if one_way * 2 + 5 <= minutes:
            options.append({**s, "walk_min": one_way})
            seen.add(s["name"])
    options.sort(key=lambda s: s["walk_min"])
    return options[:3]


# ---------- links + live conditions ----------
def maps_link(olat, olon, dlat, dlon):
    """Google Maps walking directions: opens the Maps app on a phone."""
    return "https://www.google.com/maps/dir/?" + urlencode({
        "api": 1,
        "origin": f"{olat},{olon}",
        "destination": f"{dlat},{dlon}",
        "travelmode": "walking",
    })


def get_conditions(lat, lon):
    """Optional live weather + AQI from Open-Meteo. Fails safely when offline."""
    try:
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "temperature_2m,precipitation"},
                         timeout=4).json()["current"]
        a = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "us_aqi"},
                         timeout=4).json()["current"]
        return f"{w['temperature_2m']}°C, rain {w['precipitation']} mm, AQI {a['us_aqi']}"
    except Exception:
        return "unknown (offline)"