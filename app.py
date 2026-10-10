import re

import gradio as gr
import ollama

from config import MODEL, STATIONS, SYSTEM
from places import (distance_km, find_spots, geocode, get_conditions,
                    maps_link, reverse_address)


def clean(text):
    """Remove any <think>...</think> block some models add."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def ask_llm(place, best, conditions, language):
    """The LLM only adds a short human note; it never supplies facts."""
    prompt = (
        f"A tired commuter will walk {best['walk_min']} minutes from {place} to "
        f"{best['name']} ({best['type']}). Conditions: {conditions}. Tip: {best['tip']}. "
        f"Write 2 short encouraging sentences in {language}. If AQI is above 150 or it is "
        f"raining, add a one-line caution."
    )
    try:
        r = ollama.chat(model=MODEL, think=False, messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ])
        print("RAW RESPONSE:", r)
        return clean(r["message"]["content"])
    except Exception as e:
        print("OLLAMA ERROR:", e)
        return ""


def suggest(place, minutes, language):
    try:
        loc = geocode(place)
    except Exception:
        return "Couldn't look up that place (offline?). Type coordinates like `19.0186,72.8424` instead."
    if loc is None:
        return "I couldn't find that place. Try adding the city, e.g. 'Andheri station, Mumbai'."
    lat, lon = loc

    options = find_spots(lat, lon, int(minutes))
    if not options:
        return "No green spot fits that time. Try a few more minutes."

    best = options[0]
    km = distance_km(lat, lon, best["lat"], best["lon"]) * 1.3
    address = best.get("address") or reverse_address(best["lat"], best["lon"]) \
        or f"Address unavailable offline (coordinates: {best['lat']}, {best['lon']})"
    link = maps_link(lat, lon, best["lat"], best["lon"])
    conditions = get_conditions(lat, lon)

    card = (
        f"### 🌿 {best['name']} ({best['type']})\n"
        f"- **From:** {place}\n"
        f"- **Address:** {address}\n"
        f"- **Walk:** about {best['walk_min']} min each way ({km:.1f} km)\n"
        f"- **Total time needed:** about {best['walk_min'] * 2 + 5} min (there, 5 min break, back)\n"
        f"- **Conditions now:** {conditions}\n"
        f"- **Tip:** {best['tip']}\n\n"
        f"**[📍 Open walking directions in Google Maps]({link})**\n"
    )

    note = ask_llm(place, best, conditions, language)

    others = ""
    if len(options) > 1:
        others = "\n**Other options:**\n" + "\n".join(
            f"- {o['name']}: {o['walk_min']} min walk" for o in options[1:]
        )

    return card + (f"\n💬 {note}\n" if note else "") + others


# ---------- UI ----------
demo = gr.Interface(
    fn=suggest,
    inputs=[
        gr.Textbox(value="Dadar station, Mumbai", label="Where are you? (any place, or lat,lon)"),
        gr.Slider(30, 90, value=45, step=5, label="Minutes you can spare"),
        gr.Dropdown(["English", "Hindi", "Marathi"], value="English", label="Language"),
    ],
    outputs=gr.Markdown(label="Your green reset"),
    title="🌿 Green Stop",
    description="Mumbai commute got you drained? Find a green pocket near your route. Runs fully on your own device.",
)

if __name__ == "__main__":
    demo.launch()