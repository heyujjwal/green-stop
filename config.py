import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "green-spot.csv")
CACHE_FILE = os.path.join(BASE_DIR, "osm_cache.json")

HEADERS = {"User-Agent": "green-stop-hackathon/1.0"}  # Nominatim requires this

MODEL = "gemma3:4b"   # or "qwen3:4b"

SYSTEM = (
    "You are a friendly Mumbai commute companion. Suggest a short green reset "
    "for a tired commuter. Use ONLY the places and facts provided. Never invent "
    "places, distances or times. Keep it under 80 words, warm and practical."
)

STATIONS = {
    "Churchgate": (18.9322, 72.8264),
    "Charni Road": (18.9519, 72.8185),
    "Mahalaxmi": (18.9829, 72.8231),
    "Byculla": (18.9764, 72.8325),
    "Dadar": (19.0186, 72.8424),
    "Mahim": (19.0410, 72.8400),
    "Bandra": (19.0544, 72.8402),
}