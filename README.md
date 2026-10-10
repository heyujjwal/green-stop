# 🌿 Green Stop

Offline-first commute decompression finder for Mumbai. Tell it where you are and
how many minutes you can spare. It finds a green spot (park, garden, seafront)
you can walk to and back in that time, gives the full address and a Google Maps
walking link, and a local open-weight LLM adds a short friendly note.

## How it works
Place → geocode (OSM) → find green spots (own CSV + OpenStreetMap) → distance math
→ facts card built in Python → local LLM (Ollama) adds a short note → Gradio UI

The LLM never supplies facts. Python builds the card, so nothing is invented.

## Run it
1. Install [Ollama](https://ollama.com) and run: `ollama pull gemma3:4b`
2. Then:
   pip install -r requirements.txt
   python app.py
3. Open http://127.0.0.1:7860

## Files
- `config.py`: model, prompt, stations
- `places.py`: CSV + OSM data, distance, maps link, weather
- `app.py`: LLM note + Gradio UI
- `green-spot.csv`: hand-picked spots (add your own)

## Notes
- Switch models by editing `MODEL` in `config.py` (e.g. `qwen3:4b`).
- First lookup of a new place needs internet; results are cached locally.
- Google Maps directions need internet. Everything else works offline once cached.

## License
MIT