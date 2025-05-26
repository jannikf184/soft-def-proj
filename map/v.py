import json
import requests
import time
# import pandas as pd # Derzeit nicht aktiv genutzt
from datetime import datetime
import math
import os
import folium
from shapely.geometry import Point, LineString

#FIXME Wir haben extra ne funktion dafür warum ist das hardgecoded
fallback_staedte_liste = [
    {"name": "Flensburg", "lat": 54.7833021, "lon": 9.4333264}, {"name": "Hamburg", "lat": 53.550341, "lon": 10.000654},
    {"name": "Hanover", "lat": 52.3744779, "lon": 9.7385532}, {"name": "Kassel", "lat": 51.3154546, "lon": 9.4924096},
    {"name": "Würzburg", "lat": 49.79245, "lon": 9.932966}, {"name": "Ulm", "lat": 48.3974003, "lon": 9.9934336},
    {"name": "Kempten (Allgäu)", "lat": 47.7267063, "lon": 10.3168835},
    {"name": "Füssen", "lat": 47.5709212, "lon": 10.6977089},
    {"name": "Oberhausen", "lat": 51.4696137, "lon": 6.8514435},
    {"name": "Dusseldorf", "lat": 51.2254018, "lon": 6.7763137},
    {"name": "Cologne", "lat": 50.938361, "lon": 6.959974}, {"name": "Frankfurt", "lat": 50.1106444, "lon": 8.6820917},
    {"name": "Nuremberg", "lat": 49.453872, "lon": 11.077298},
    {"name": "Regensburg", "lat": 49.0195333, "lon": 12.0974869},
    {"name": "Passau", "lat": 48.5748229, "lon": 13.4609744}, {"name": "Lübeck", "lat": 53.866444, "lon": 10.684738},
    {"name": "Bremen", "lat": 53.0758196, "lon": 8.8071646}, {"name": "Münster", "lat": 51.9625101, "lon": 7.6251879},
    {"name": "Dortmund", "lat": 51.5142273, "lon": 7.4652789}, {"name": "Berlin", "lat": 52.5170365, "lon": 13.3888599},
    {"name": "Leipzig", "lat": 51.3406321, "lon": 12.3747329},
    {"name": "Bayreuth", "lat": 49.9427202, "lon": 11.5763079},
    {"name": "Ingolstadt", "lat": 48.7630165, "lon": 11.4250395},
    {"name": "Munich", "lat": 48.1371079, "lon": 11.5753822},
    {"name": "Magdeburg", "lat": 52.1315889, "lon": 11.6399609}
]
staedte_koordinaten_dict = {stadt['name']: {'lat': stadt['lat'], 'lon': stadt['lon']} for stadt in
                            fallback_staedte_liste}

autobahn_abschnitte_definition = {
    "A7": {"osm_ref": "A 7", "abschnitte": [
        {"start_stadt_name": "Flensburg", "end_stadt_name": "Hamburg", "fahrtrichtung_grad": 160},
        {"start_stadt_name": "Hamburg", "end_stadt_name": "Hanover", "fahrtrichtung_grad": 180},
        {"start_stadt_name": "Hanover", "end_stadt_name": "Kassel", "fahrtrichtung_grad": 180},
        {"start_stadt_name": "Kassel", "end_stadt_name": "Würzburg", "fahrtrichtung_grad": 165},
        {"start_stadt_name": "Würzburg", "end_stadt_name": "Ulm", "fahrtrichtung_grad": 160},
        {"start_stadt_name": "Ulm", "end_stadt_name": "Kempten (Allgäu)", "fahrtrichtung_grad": 180},
        {"start_stadt_name": "Kempten (Allgäu)", "end_stadt_name": "Füssen", "fahrtrichtung_grad": 160},
    ]},
    "A3": {"osm_ref": "A 3", "abschnitte": [
        {"start_stadt_name": "Oberhausen", "end_stadt_name": "Cologne", "fahrtrichtung_grad": 140},
        {"start_stadt_name": "Cologne", "end_stadt_name": "Frankfurt", "fahrtrichtung_grad": 110},
        {"start_stadt_name": "Frankfurt", "end_stadt_name": "Würzburg", "fahrtrichtung_grad": 115},
        {"start_stadt_name": "Würzburg", "end_stadt_name": "Nuremberg", "fahrtrichtung_grad": 100},
        {"start_stadt_name": "Nuremberg", "end_stadt_name": "Regensburg", "fahrtrichtung_grad": 125},
        {"start_stadt_name": "Regensburg", "end_stadt_name": "Passau", "fahrtrichtung_grad": 115},
    ]},
    "A1": {"osm_ref": "A 1", "abschnitte": [
        {"start_stadt_name": "Lübeck", "end_stadt_name": "Hamburg", "fahrtrichtung_grad": 220},
        {"start_stadt_name": "Hamburg", "end_stadt_name": "Bremen", "fahrtrichtung_grad": 230},
        {"start_stadt_name": "Bremen", "end_stadt_name": "Münster", "fahrtrichtung_grad": 190},
        {"start_stadt_name": "Münster", "end_stadt_name": "Dortmund", "fahrtrichtung_grad": 170},
    ]},
    "A2": {"osm_ref": "A 2", "abschnitte": [
        {"start_stadt_name": "Oberhausen", "end_stadt_name": "Dortmund", "fahrtrichtung_grad": 80},
        {"start_stadt_name": "Dortmund", "end_stadt_name": "Hanover", "fahrtrichtung_grad": 75},
        {"start_stadt_name": "Hanover", "end_stadt_name": "Magdeburg", "fahrtrichtung_grad": 90},
        {"start_stadt_name": "Magdeburg", "end_stadt_name": "Berlin", "fahrtrichtung_grad": 100},
    ]},
    "A9": {"osm_ref": "A 9", "abschnitte": [
        {"start_stadt_name": "Berlin", "end_stadt_name": "Leipzig", "fahrtrichtung_grad": 200},
        {"start_stadt_name": "Leipzig", "end_stadt_name": "Bayreuth", "fahrtrichtung_grad": 180},
        {"start_stadt_name": "Bayreuth", "end_stadt_name": "Nuremberg", "fahrtrichtung_grad": 190},
        {"start_stadt_name": "Nuremberg", "end_stadt_name": "Ingolstadt", "fahrtrichtung_grad": 170},
        {"start_stadt_name": "Ingolstadt", "end_stadt_name": "Munich", "fahrtrichtung_grad": 170},
    ]}
}

CURRENT_TIMESTAMP = int(time.time())
START_TIMESTAMP = CURRENT_TIMESTAMP - 86400

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WEATHER_CACHE_FILE = "wetterdaten_cache.json"
FORCE_WEATHER_REFRESH = False

# NEU: Schalter für Debugging der OSM-Darstellung
DEBUG_DRAW_ALL_OSM_WAYS = True  # Setze auf True, um alle OSM Ways einer Autobahn zu zeichnen

# --- Hilfsfunktionen (wie gehabt, außer fetch_latest_weather_datapoint_from_api mit API_KEY Check) ---
def fetch_latest_weather_datapoint_from_api(lat, lon, current_api_key):
    if not current_api_key or current_api_key == "YOUR_NEW_API_KEY":  # Sicherstellen, dass ein Key da ist
        print(f"WARNUNG: Kein gültiger API Key für Wetterdaten (Lat {lat}, Lon {lon}). Überspringe API-Abruf.")
        return None
    url = (
        f"https://history.openweathermap.org/data/2.5/history/city"
        f"?lat={lat}&lon={lon}&type=hour&start={START_TIMESTAMP}&end={CURRENT_TIMESTAMP}&appid={current_api_key}&units=metric"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        api_response = r.json()
        hourly_data_list = api_response.get("list", [])
        if hourly_data_list:
            return hourly_data_list[-1]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(
                f"FEHLER 401: Nicht autorisiert für Wetterdaten-API (Lat {lat}, Lon {lon}). API-Key prüfen! Details: {e}")
        else:
            print(f"HTTP FEHLER Wetterdaten (Lat {lat}, Lon {lon}): {e}")
    except requests.exceptions.RequestException as e:
        print(f"FEHLER Wetterdaten (Lat {lat}, Lon {lon}): {e}")
    return None


def calculate_destination_point(lat_deg, lon_deg, bearing_deg, distance_km):
    R = 6371.0
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    bearing_rad = math.radians(bearing_deg)
    lat2_rad = math.asin(math.sin(lat_rad) * math.cos(distance_km / R) +
                         math.cos(lat_rad) * math.sin(distance_km / R) * math.cos(bearing_rad))
    lon2_rad = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(distance_km / R) * math.cos(lat_rad),
                                    math.cos(distance_km / R) - math.sin(lat_rad) * math.sin(lat2_rad))
    return math.degrees(lat2_rad), math.degrees(lon2_rad)


def get_osm_autobahn_geometry_by_ref(autobahn_ref_tag):
    query = f'[out:json][timeout:180];way["highway"="motorway"]["ref"="{autobahn_ref_tag}"];out geom;'
    print(f"INFO: Rufe OSM Geometrie für {autobahn_ref_tag} ab...")
    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=190)
        response.raise_for_status()
        data = response.json()
        all_osm_ways = []  # Liste von Listen von Koordinaten-Tupeln
        for element in data.get("elements", []):
            if element["type"] == "way" and "geometry" in element:
                # geometry ist eine Liste von {lat: ..., lon: ...} Objekten
                way_coords = [(node["lat"], node["lon"]) for node in element["geometry"]]
                if len(way_coords) >= 2:  # Nur Ways mit mind. 2 Punkten sind Linien
                    all_osm_ways.append(way_coords)

        if not all_osm_ways:
            print(f"WARNUNG: Keine Geometrie für {autobahn_ref_tag} von OSM erhalten.")
            return None
        print(f"INFO: Geometrie für {autobahn_ref_tag} mit {len(all_osm_ways)} Way-Segmenten von OSM erhalten.")
        # Debug: Längen der einzelnen Way-Segmente ausgeben
        # for i, way in enumerate(all_osm_ways):
        #     print(f"    OSM Way {i} Länge: {len(way)} Punkte")
        return all_osm_ways
    except requests.exceptions.RequestException as e:
        print(f"FEHLER beim Abrufen der OSM-Daten für {autobahn_ref_tag}: {e}")
    except json.JSONDecodeError:
        print(f"FEHLER: Ungültige JSON-Antwort von Overpass API für {autobahn_ref_tag}.")
    return None


def find_closest_point_index_on_osm_segment(target_coord_tuple, osm_segment_coords_list):
    if not osm_segment_coords_list or len(osm_segment_coords_list) < 2:
        return None, None, float('inf')
    try:
        target_point = Point(target_coord_tuple[1], target_coord_tuple[0])  # lon, lat für Shapely
        min_dist = float('inf')
        closest_idx = -1

        # Iteriere über die Punkte des OSM-Segments
        for i, p_coord in enumerate(osm_segment_coords_list):
            current_point_on_line = Point(p_coord[1], p_coord[0])  # lon, lat
            dist = target_point.distance(current_point_on_line)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        if closest_idx != -1:
            return closest_idx, osm_segment_coords_list[closest_idx], min_dist
        else:  # Sollte nicht passieren, wenn osm_segment_coords_list nicht leer ist
            return None, None, float('inf')

    except NameError:  # Shapely nicht da
        print("WARNUNG: Shapely nicht verfügbar. Nächstgelegener Punkt kann nicht präzise bestimmt werden.")
        # Fallback: Erster Punkt des Segments
        return 0, osm_segment_coords_list[0], float('inf')
    except Exception as e:
        print(f"FEHLER bei find_closest_point_index_on_osm_segment: {e}")
        return None, None, float('inf')


# --- Wetterdaten laden oder von API abrufen und cachen (wie gehabt) ---
wetterdaten_aller_startstaedte = {}
if not FORCE_WEATHER_REFRESH and os.path.exists(WEATHER_CACHE_FILE):
    print(f"INFO: Lade Wetterdaten aus Cache-Datei: {WEATHER_CACHE_FILE}")
    try:
        with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
            wetterdaten_aller_startstaedte = json.load(f)
    except Exception as e:  # Breitere Exception für korrupte Datei etc.
        print(f"FEHLER: Cache-Datei {WEATHER_CACHE_FILE} konnte nicht geladen werden ({e}). Rufe Daten von API ab.")
        FORCE_WEATHER_REFRESH = True

if FORCE_WEATHER_REFRESH or not wetterdaten_aller_startstaedte:
    print(f"INFO: Wetterdaten werden von API abgerufen (Cache nicht genutzt oder Refresh erzwungen).")
    unique_start_cities_to_fetch = {}
    for autobahn_data in autobahn_abschnitte_definition.values():
        for abschnitt in autobahn_data['abschnitte']:
            start_stadt_name = abschnitt["start_stadt_name"]
            if start_stadt_name not in unique_start_cities_to_fetch:
                coords = staedte_koordinaten_dict.get(start_stadt_name)
                if coords: unique_start_cities_to_fetch[start_stadt_name] = coords

    for stadt_name, coords in unique_start_cities_to_fetch.items():
        print(f"  Rufe Wetterdaten für {stadt_name} ab...")
        wetter_eintrag = fetch_latest_weather_datapoint_from_api(coords['lat'], coords['lon'], api_key)
        wetterdaten_aller_startstaedte[stadt_name] = wetter_eintrag
        time.sleep(0.2)  # Kleine Pause

    try:
        with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(wetterdaten_aller_startstaedte, f, indent=4)
        print(f"INFO: Wetterdaten erfolgreich in {WEATHER_CACHE_FILE} gespeichert.")
    except Exception as e:
        print(f"FEHLER beim Speichern der Wetterdaten in Cache {WEATHER_CACHE_FILE}: {e}")

# --- Hauptlogik zur Kartenerstellung ---
map_center_lat, map_center_lon = 51.1657, 10.4515
wetter_karte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=6)

fahrtrichtung_pfeil_laenge_km = 15
wind_arrow_scale_factor = 3.0
min_wind_arrow_length_km, max_wind_arrow_length_km = 5, 50

osm_geometries_cache = {}

for autobahn_name, autobahn_data in autobahn_abschnitte_definition.items():
    print(f"\nVerarbeite Autobahn: {autobahn_name} ({autobahn_data['osm_ref']})")
    osm_ref = autobahn_data['osm_ref']

    if osm_ref not in osm_geometries_cache:
        all_osm_ways_for_this_autobahn = get_osm_autobahn_geometry_by_ref(osm_ref)
        if all_osm_ways_for_this_autobahn:
            osm_geometries_cache[osm_ref] = all_osm_ways_for_this_autobahn
        else:
            print(f"WARNUNG: Keine OSM-Geometrie für {autobahn_name}. Überspringe detaillierte Darstellung.")
            continue

    current_autobahn_osm_ways = osm_geometries_cache.get(osm_ref)
    if not current_autobahn_osm_ways:
        continue

    # DEBUGGING: Alle OSM Ways einer Autobahn zeichnen
    if DEBUG_DRAW_ALL_OSM_WAYS:
        print(f"  DEBUG: Zeichne alle {len(current_autobahn_osm_ways)} OSM Way-Segmente für {autobahn_name}")
        for i, way_segment_coords in enumerate(current_autobahn_osm_ways):
            folium.PolyLine(
                locations=way_segment_coords,
                color="purple",  # Eine feste Farbe für alle Segmente dieser Autobahn
                weight=3,
                opacity=0.6,
                tooltip=f"OSM Way {i} für {autobahn_name}"
            ).add_to(wetter_karte)
        # Wenn dieser Modus aktiv ist, überspringen wir die abschnittsweise Logik für diese Autobahn
        continue

        # Reguläre abschnittsweise Verarbeitung
    for abschnitt_idx, abschnitt in enumerate(autobahn_data['abschnitte']):
        start_stadt_name = abschnitt["start_stadt_name"]
        end_stadt_name = abschnitt["end_stadt_name"]
        fahrtrichtung_grad_kompass = abschnitt["fahrtrichtung_grad"]

        start_stadt_coords_data = staedte_koordinaten_dict.get(start_stadt_name)
        end_stadt_coords_data = staedte_koordinaten_dict.get(end_stadt_name)

        if not start_stadt_coords_data or not end_stadt_coords_data:
            print(f"FEHLER: Koordinaten für {start_stadt_name} oder {end_stadt_name} nicht gefunden.")
            continue

        start_lat, start_lon = start_stadt_coords_data['lat'], start_stadt_coords_data['lon']
        end_lat, end_lon = end_stadt_coords_data['lat'], end_stadt_coords_data['lon']

        print(f"  Abschnitt {abschnitt_idx + 1}: {start_stadt_name} -> {end_stadt_name}")

        best_segment_for_abschnitt_coords = None
        min_combined_distance = float('inf')

        # Iteriere durch ALLE Ways der aktuellen Autobahn, um den besten für diesen Abschnitt zu finden
        for osm_single_way_coords in current_autobahn_osm_ways:
            # Finde nächstgelegene Punkte auf diesem spezifischen OSM Way
            idx_start_on_way, _, dist_start = find_closest_point_index_on_osm_segment((start_lat, start_lon),
                                                                                      osm_single_way_coords)
            idx_end_on_way, _, dist_end = find_closest_point_index_on_osm_segment((end_lat, end_lon),
                                                                                  osm_single_way_coords)

            if idx_start_on_way is not None and idx_end_on_way is not None:
                # Heuristik: Ist dieser Way relevant für den aktuellen Abschnitt?
                # Wir nehmen den Way, bei dem die Summe der Distanzen zu Start/Endstadt minimal ist.
                # Dies ist immer noch die Schwachstelle, wenn der Abschnitt über mehrere Ways geht.
                current_combined_distance = dist_start + dist_end

                # Debug-Ausgabe für jeden betrachteten OSM-Way
                # print(f"    Prüfe OSM Way (Länge {len(osm_single_way_coords)}): dist_start={dist_start:.4f}, dist_end={dist_end:.4f}, combined={current_combined_distance:.4f}")

                if current_combined_distance < min_combined_distance:
                    # Extrahiere den Teil des Ways zwischen den gefundenen Indizes
                    extracted_coords_on_this_way = []
                    if idx_start_on_way <= idx_end_on_way:
                        extracted_coords_on_this_way = osm_single_way_coords[idx_start_on_way: idx_end_on_way + 1]
                    else:  # Start-Index ist nach End-Index, d.h. der Way verläuft entgegen unserer Fahrtrichtung
                        extracted_coords_on_this_way = osm_single_way_coords[idx_end_on_way: idx_start_on_way + 1]
                        extracted_coords_on_this_way.reverse()  # In unsere Fahrtrichtung drehen

                    if len(extracted_coords_on_this_way) >= 2:
                        # print(f"      => Neuer Kandidat für best_segment gefunden. Länge: {len(extracted_coords_on_this_way)} Punkte. Combined dist: {current_combined_distance:.4f}")
                        min_combined_distance = current_combined_distance
                        best_segment_for_abschnitt_coords = extracted_coords_on_this_way
                    # else:
                    # print(f"      => Extrahierter Abschnitt zu kurz ({len(extracted_coords_on_this_way)} Punkte).")

        abschnitt_farbe = "blue"  # Platzhalter
        # TODO: Farbe basierend auf Wetterdaten bestimmen

        if best_segment_for_abschnitt_coords:
            print(
                f"    -> Bestes OSM-Segment für Abschnitt gefunden. Länge: {len(best_segment_for_abschnitt_coords)} Punkte. Min combined dist: {min_combined_distance:.4f}")
            folium.PolyLine(
                locations=best_segment_for_abschnitt_coords, color=abschnitt_farbe, weight=5, opacity=0.7,
                tooltip=f"OSM: {start_stadt_name} -> {end_stadt_name}"
            ).add_to(wetter_karte)
        else:
            print(
                f"    WARNUNG: Kein passendes OSM-Segment für {start_stadt_name} -> {end_stadt_name}. Zeichne gerade Linie.")
            folium.PolyLine(
                locations=[(start_lat, start_lon), (end_lat, end_lon)], color="red", weight=3, opacity=0.7,
                dash_array='5, 5', tooltip=f"Fallback: {start_stadt_name} -> {end_stadt_name}"
            ).add_to(wetter_karte)

        # Pfeile (wie gehabt)
        mid_lat, mid_lon = (start_lat + end_lat) / 2, (start_lon + end_lon) / 2
        pfeil_start_fahrt = calculate_destination_point(mid_lat, mid_lon, (fahrtrichtung_grad_kompass + 180) % 360,
                                                        fahrtrichtung_pfeil_laenge_km / 2)
        pfeil_ende_fahrt = calculate_destination_point(mid_lat, mid_lon, fahrtrichtung_grad_kompass,
                                                       fahrtrichtung_pfeil_laenge_km / 2)
        folium.PolyLine(locations=[pfeil_start_fahrt, pfeil_ende_fahrt], color="black", weight=2).add_to(wetter_karte)
        folium.RegularPolygonMarker(location=pfeil_ende_fahrt, fill_color='black', color='black', number_of_sides=3,
                                    radius=5, rotation=(fahrtrichtung_grad_kompass - 90 + 360) % 360).add_to(
            wetter_karte)

        wetter_eintrag = wetterdaten_aller_startstaedte.get(start_stadt_name)
        if wetter_eintrag:
            wind_speed_mps = wetter_eintrag.get("wind", {}).get("speed")
            wind_deg_meteo = wetter_eintrag.get("wind", {}).get("deg")
            if wind_speed_mps is not None and wind_deg_meteo is not None:
                wind_pfeil_richtung_kompass = (wind_deg_meteo + 180) % 360
                wind_pfeil_laenge_km = max(min_wind_arrow_length_km,
                                           min(wind_speed_mps * wind_arrow_scale_factor, max_wind_arrow_length_km))
                pfeil_ende_wind = calculate_destination_point(start_lat, start_lon, wind_pfeil_richtung_kompass,
                                                              wind_pfeil_laenge_km)
                folium.PolyLine(locations=[(start_lat, start_lon), pfeil_ende_wind], color="darkblue", weight=2.5,
                                opacity=0.8,
                                tooltip=f"Wind in {start_stadt_name}: {wind_speed_mps:.1f} m/s aus {wind_deg_meteo}°").add_to(
                    wetter_karte)
                folium.RegularPolygonMarker(location=pfeil_ende_wind, fill_color='darkblue', color='darkblue',
                                            number_of_sides=3, radius=6,
                                            rotation=(wind_pfeil_richtung_kompass - 90 + 360) % 360).add_to(
                    wetter_karte)

# --- Karte speichern ---
karten_dateiname = "autobahn_wetter_osm_debug.html"
wetter_karte.save(karten_dateiname)
print(f"\n✅ Karte erfolgreich als '{karten_dateiname}' gespeichert.")
print("\nSkriptausführung beendet.")
