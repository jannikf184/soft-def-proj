import requests     #FIXME actually not necessary, because lon an lat are hardcoded tf?
import json
from keys import load_API_KEY
# Dein OpenWeatherMap API Key
api_key = load_API_KEY

# Liste der Städtenamen, die du prüfen möchtest
staedte_namen = [
    "Flensburg",
    "Hamburg",
    "Hannover",
    "Kassel",
    "Würzburg",
    "Ulm",
    "Kempten",
    "Füssen",
    "Oberhausen",
    "Düsseldorf",
    "Köln",
    "Frankfurt am Main",
    "Nürnberg",
    "Regensburg",
    "Passau",
    "Lübeck",
    "Bremen",
    "Münster",
    "Dortmund",
    "Berlin",
    "Leipzig",
    "Bayreuth",
    "Ingolstadt",
    "München",
    "Magdeburg"
]

staedte_koordinaten = []

for stadt in staedte_namen:
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={stadt},DE&limit=1&appid={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        daten = response.json()
        if daten:
            stadt_info = daten[0]
            staedte_koordinaten.append({
                "name": stadt_info["name"],
                "lat": stadt_info["lat"],
                "lon": stadt_info["lon"]
            })
    except requests.exceptions.RequestException as e:
        print(f"❌ Fehler bei der API-Abfrage für {stadt}: {e}")

# Ergebnisse in JSON-Datei speichern
with open("../exporter/staedte_koordinaten.json", "w") as f:
    json.dump(staedte_koordinaten, f, indent=4, ensure_ascii=False)

print("✅ Koordinaten erfolgreich exportiert als 'staedte_koordinaten.json'")