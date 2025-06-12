import json
import requests
import time
import math
import os
import folium
from keys import load_API_KEY

try:
    from shapely.geometry import Point, LineString
except ImportError:
    print(
        "FEHLER: Die Bibliothek 'Shapely' wurde nicht gefunden. Bitte installieren Sie sie mit 'pip install Shapely'.")

# --- Konstanten und Konfiguration ---
API_KEY = load_API_KEY
CURRENT_TIMESTAMP = int(time.time())
START_TIMESTAMP = CURRENT_TIMESTAMP - 86400
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WEATHER_CACHE_FILE = "../wetterdaten_cache.json"
FORCE_WEATHER_REFRESH = True
OSM_GEOMETRY_CACHE_FILE = "../osm_geometrien_cache.json"
FORCE_OSM_REFRESH = False
FAHRGESCHWINDIGKEIT_KMH_CONST = 150

# Fahrzeug- und physikalische Konstanten
CD_Q7 = 0.34    #drag coefficient
A_Q7 = 2.8      #fläche
MASSE_Q7_KG = 2200
C_R_Q7 = 0.01
G_ACCEL = 9.81
WIRKUNGSGRAD_MOTOR_ANTRIEB = 0.285
ENERGIEGEHALT_BENZIN_J_PRO_L = 32 * 10 ** 6

# --- Lade Städtekoordinaten & Autobahnabschnitte (Basisdefinition) ---
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
original_autobahn_abschnitte_definition = {
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

def fetch_latest_weather_from_prometheus(city_name: str, prometheus_url="http://prometheus:9090"):#localhost from ide prometheus from docker
    def query(metric):
        query_url = f"{prometheus_url}/api/v1/query"
        params = {"query": f'{metric}{{city="{city_name}"}}'}
        try:
            r = requests.get(query_url, params=params, timeout=5)
            r.raise_for_status()
            result = r.json()
            value = result["data"]["result"][0]["value"][1] if result["data"]["result"] else None
            return float(value) if value else None
        except Exception as e:
            print(f"Prometheus-Fehler ({metric}, {city_name}): {e}")
            return None

    return {
        "dt": int(time.time()),
        "main": {
            "temp": query("weather_temperature"),
            "pressure": query("weather_pressure"),
            "humidity": query("weather_humidity"),
            "feels_like": query("weather_feels_like"),
            "temp_min": query("weather_temp_min"),
            "temp_max": query("weather_temp_max"),
        },
        "wind": {
            "speed": query("weather_wind_speed"),
            "deg": query("weather_wind_deg"),
            "gust": query("weather_wind_gust"),
        },
        # clouds, weather etc. optional
    }


def calculate_destination_point(lat_deg, lon_deg, bearing_deg, distance_km):
    R = 6371.0
    lat_rad, lon_rad, bearing_rad = math.radians(lat_deg), math.radians(lon_deg), math.radians(bearing_deg)
    lat2_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_km / R) + math.cos(lat_rad) * math.sin(distance_km / R) * math.cos(
            bearing_rad))
    lon2_rad = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(distance_km / R) * math.cos(lat_rad),
                                    math.cos(distance_km / R) - math.sin(lat_rad) * math.sin(lat2_rad))
    return math.degrees(lat2_rad), math.degrees(lon2_rad)


def get_midpoint_of_way(way_coords):
    if not way_coords: return None
    min_lat, max_lat = min(p[0] for p in way_coords), max(p[0] for p in way_coords)
    min_lon, max_lon = min(p[1] for p in way_coords), max(p[1] for p in way_coords)
    return ((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)


def get_midpoint_of_defined_abschnitt(start_stadt_coords, end_stadt_coords):
    if not start_stadt_coords or not end_stadt_coords: return None
    return ((start_stadt_coords['lat'] + end_stadt_coords['lat']) / 2,
            (start_stadt_coords['lon'] + end_stadt_coords['lon']) / 2)


def calculate_distance_sq(coord1, coord2):
    if not coord1 or not coord2: return float('inf')
    return (coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2


def get_osm_autobahn_geometry_by_ref(autobahn_ref_tag):
    query_bbox_string = ""
    strict_de_bbox = {"min_lat": 47.27, "max_lat": 55.06, "min_lon": 6.496, "max_lon": 15.05}
    query = f'[out:json][timeout:180];{query_bbox_string}(way["highway"="motorway"]["ref"="{autobahn_ref_tag}"];);out geom;'
    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=190);
        response.raise_for_status();
        data = response.json()
        parsed_osm_ways = []
        for element in data.get("elements", []):
            if element["type"] == "way" and "geometry" in element:
                way_coords = [(node["lat"], node["lon"]) for node in element["geometry"]]
                if len(way_coords) >= 2: parsed_osm_ways.append({"id": element.get("id", "N/A"), "coords": way_coords})
        if not parsed_osm_ways: return None
        filtered_osm_ways = []
        for way_data in parsed_osm_ways:
            way_coords = way_data["coords"]
            way_is_acceptable = True
            for point_lat, point_lon in way_coords:
                if not (strict_de_bbox["min_lat"] <= point_lat <= strict_de_bbox["max_lat"] and \
                        strict_de_bbox["min_lon"] <= point_lon <= strict_de_bbox["max_lon"]):
                    way_is_acceptable = False;
                    break
            if way_is_acceptable: filtered_osm_ways.append(way_coords)
        return filtered_osm_ways if filtered_osm_ways else None
    except:
        return None



def calc_airspeed_against_car(wind_speed_kmh=0, wind_direction_deg=0, car_direction_deg=0):
    """
    Die Funktion nimmt Windgeschwindigkeit, Windrichtung und projeziert den Anteil des Windes,
    der mit oder gegen die Fahrtrichtung "arbeitet"
    :param wind_speed_kmh: Windgeschwindigkeit in kmh
    :param wind_direction_deg: ""
    :param car_direction_deg: ""
    :return:
    Die relative Windgeschwindigkeit auf das Auto
    z.B: 150 km/h (Auto) + 10 km/h (Gegenwind) = 160km/h
    """
    relative_direction = car_direction_deg - wind_direction_deg
    v_rel_kmh = math.cos(math.radians(relative_direction)) * wind_speed_kmh
    return FAHRGESCHWINDIGKEIT_KMH_CONST + v_rel_kmh



def normiere_verbrauch(v, v_min=8, v_max=22):
    if v_max == v_min: return 50
    v_clamped = max(v_min, min(v, v_max))
    if v_clamped <= v_min:
        norm_score = 100
    elif v_clamped >= v_max:
        norm_score = 1
    else:
        norm_score = 100 - ((v_clamped - v_min) * 99 / (v_max - v_min))
    return round(norm_score)


def calc_fuel_rating(temp_c, wind_speed_kmh, wind_direction_deg, car_direction_deg, druck_hpa, debug_city=""):
    cd_value = CD_Q7
    area_m2 = A_Q7
    masse_kg = MASSE_Q7_KG
    cr_coeff = C_R_Q7
    fahrzeug_geschwindigkeit_mps = FAHRGESCHWINDIGKEIT_KMH_CONST / 3.6
    v_luft_anstroemung_kmh = calc_airspeed_against_car(wind_speed_kmh, wind_direction_deg, car_direction_deg)
    v_luft_anstroemung_mps = v_luft_anstroemung_kmh / 3.6
    druck_pa = druck_hpa * 100
    temp_kelvin = temp_c + 273.15
    r_specific_air = 287.058
    air_density_kg_m3 = druck_pa / (r_specific_air * temp_kelvin)
    f_drag_newton = 0.5 * air_density_kg_m3 * cd_value * area_m2 * (v_luft_anstroemung_mps ** 2)
    f_roll_newton = cr_coeff * masse_kg * G_ACCEL
    p_drag_watts = f_drag_newton * fahrzeug_geschwindigkeit_mps
    p_roll_watts = f_roll_newton * fahrzeug_geschwindigkeit_mps
    p_total_watts = p_drag_watts + p_roll_watts
    p_total_watts = max(1000, p_total_watts)
    if fahrzeug_geschwindigkeit_mps <= 0:
        return float('inf'), normiere_verbrauch(float('inf'), v_min=8, v_max=22)
    energie_100km_joule = (p_total_watts / fahrzeug_geschwindigkeit_mps) * 100000
    verbrauch_l_100km = energie_100km_joule / (ENERGIEGEHALT_BENZIN_J_PRO_L * WIRKUNGSGRAD_MOTOR_ANTRIEB)
    # if debug_city:
    #     print(f"\n--- DEBUG calc_fuel_rating für {debug_city} (Fahrtrichtung: {car_direction_deg}°) ---")
    #     # ... (weitere Debug-Prints) ...
    #     print(f"  => Verbrauch berechnet: {verbrauch_l_100km:.2f} l/100km")
    return verbrauch_l_100km, normiere_verbrauch(verbrauch_l_100km, v_min=8, v_max=22)


def get_verbrauch_farbe(verbrauch_l_100km,
                        ref_verbrauch=12.0,
                        bester_verbrauch_ziel=8.0,
                        schlechtester_verbrauch_schwelle=17.2):
    yellow_rgb = (254,221,0);
    gruen_ziel_rgb = (8,255,8);
    rot_ziel_rgb = (225,6,0)
    if bester_verbrauch_ziel >= ref_verbrauch: bester_verbrauch_ziel = ref_verbrauch - 0.1
    if schlechtester_verbrauch_schwelle <= ref_verbrauch: schlechtester_verbrauch_schwelle = ref_verbrauch + 0.1
    r, g, b = yellow_rgb
    if verbrauch_l_100km <= bester_verbrauch_ziel:
        r, g, b = gruen_ziel_rgb
    elif verbrauch_l_100km >= schlechtester_verbrauch_schwelle:
        r, g, b = rot_ziel_rgb
    elif verbrauch_l_100km < ref_verbrauch:
        if ref_verbrauch == bester_verbrauch_ziel:
            r, g, b = gruen_ziel_rgb if verbrauch_l_100km <= ref_verbrauch else yellow_rgb
        else:
            faktor = (ref_verbrauch - verbrauch_l_100km) / (ref_verbrauch - bester_verbrauch_ziel)
            faktor = max(0, min(1, faktor))
            r = int(yellow_rgb[0] * (1 - faktor) + gruen_ziel_rgb[0] * faktor)
            g = int(yellow_rgb[1] * (1 - faktor) + gruen_ziel_rgb[1] * faktor)
            b = int(yellow_rgb[2] * (1 - faktor) + gruen_ziel_rgb[2] * faktor)
    elif verbrauch_l_100km > ref_verbrauch:
        if schlechtester_verbrauch_schwelle == ref_verbrauch:
            r, g, b = rot_ziel_rgb if verbrauch_l_100km >= ref_verbrauch else yellow_rgb
        else:
            faktor = (verbrauch_l_100km - ref_verbrauch) / (schlechtester_verbrauch_schwelle - ref_verbrauch)
            faktor = max(0, min(1, faktor))
            r = int(yellow_rgb[0] * (1 - faktor) + rot_ziel_rgb[0] * faktor)
            g = int(yellow_rgb[1] * (1 - faktor) + rot_ziel_rgb[1] * faktor)
            b = int(yellow_rgb[2] * (1 - faktor) + rot_ziel_rgb[2] * faktor)
    r = max(0, min(255, r));
    g = max(0, min(255, g));
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# --- Wetterdaten Caching ---
wetterdaten_aller_startstaedte = {}
if not FORCE_WEATHER_REFRESH and os.path.exists(WEATHER_CACHE_FILE):
    try:
        with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
            wetterdaten_aller_startstaedte = json.load(f)
    except Exception as e:
        print(f"FEHLER: Cache-Datei {WEATHER_CACHE_FILE} konnte nicht geladen werden ({e}).");
        FORCE_WEATHER_REFRESH = True
if FORCE_WEATHER_REFRESH or not wetterdaten_aller_startstaedte:
    print(f"INFO: Wetterdaten werden von API abgerufen.")
    unique_cities_for_weather = set()
    for autobahn_data in original_autobahn_abschnitte_definition.values():  # Sicherstellen, dass alle relevanten Städte gecacht werden
        for abschnitt in autobahn_data['abschnitte']:
            unique_cities_for_weather.add(abschnitt["start_stadt_name"])
            unique_cities_for_weather.add(abschnitt["end_stadt_name"])  # Wichtig für Option 1 der Gegenrichtung

    if not unique_cities_for_weather and not wetterdaten_aller_startstaedte:
        print("WARNUNG: Keine Städte für Wetterdatenabruf und Cache leer.")
    else:
        for stadt_name in list(unique_cities_for_weather):
            coords = staedte_koordinaten_dict.get(stadt_name)
            if coords:
                wetter_eintrag = fetch_latest_weather_from_prometheus(stadt_name)
                wetterdaten_aller_startstaedte[stadt_name] = wetter_eintrag;
                time.sleep(0.1)
        try:
            with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(wetterdaten_aller_startstaedte, f, indent=4)
            print(f"INFO: Wetterdaten erfolgreich in {WEATHER_CACHE_FILE} gespeichert.")
        except Exception as e:
            print(f"FEHLER beim Speichern der Wetterdaten in Cache {WEATHER_CACHE_FILE}: {e}")

# --- OSM Geometrie Caching ---
osm_geometries_cache_data = {}
if not FORCE_OSM_REFRESH and os.path.exists(OSM_GEOMETRY_CACHE_FILE):
    try:
        with open(OSM_GEOMETRY_CACHE_FILE, "r", encoding="utf-8") as f:
            osm_geometries_cache_data = json.load(f)
    except Exception as e:
        print(f"FEHLER: OSM Cache-Datei {OSM_GEOMETRY_CACHE_FILE} konnte nicht geladen werden ({e}).");
        FORCE_OSM_REFRESH = True


# --- Hauptfunktion zur Kartenerstellung ---
def erstelle_karte(aktuelle_autobahn_definition, karten_dateiname_suffix, ist_gegenrichtung_flag=False):
    map_center_lat, map_center_lon = 51.1657, 10.4515
    karte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=6, tiles="CartoDB positron")
    fahrtrichtung_pfeil_laenge_km = 15
    wind_arrow_scale_factor = 3.0
    min_wind_arrow_length_km, max_wind_arrow_length_km = 5, 50

    session_osm_cache = {}
    gesammelte_verbrauchswerte_fuer_diese_karte = []

    for autobahn_name, autobahn_data_definition_loop in aktuelle_autobahn_definition.items():
        osm_ref = autobahn_data_definition_loop['osm_ref']
        if osm_ref not in session_osm_cache:
            if not FORCE_OSM_REFRESH and osm_ref in osm_geometries_cache_data:
                session_osm_cache[osm_ref] = osm_geometries_cache_data[osm_ref]
            else:
                all_osm_ways_for_this_autobahn = get_osm_autobahn_geometry_by_ref(osm_ref)
                if all_osm_ways_for_this_autobahn:
                    session_osm_cache[osm_ref] = all_osm_ways_for_this_autobahn
                    if FORCE_OSM_REFRESH or osm_ref not in osm_geometries_cache_data:
                        osm_geometries_cache_data[osm_ref] = all_osm_ways_for_this_autobahn
                else:
                    print(f"WARNUNG: Keine OSM-Geometrie für {autobahn_name} (Ref: {osm_ref}). Überspringe Autobahn.");
                    continue

        complete_osm_line_segments_for_autobahn = session_osm_cache.get(osm_ref)
        if not complete_osm_line_segments_for_autobahn:
            print(f"WARNUNG: Keine OSM Ways für {autobahn_name} im Sitzungscache. Überspringe Autobahn.");
            continue

        # Erstelle eine Liste der definierten Hauptabschnitte für die aktuelle Autobahn und aktuelle Richtung
        definierte_hauptabschnitte_aktuell = []
        for abschnitt_def in autobahn_data_definition_loop['abschnitte']:
            start_c = staedte_koordinaten_dict.get(abschnitt_def["start_stadt_name"])
            end_c = staedte_koordinaten_dict.get(abschnitt_def["end_stadt_name"])
            mid_p = get_midpoint_of_defined_abschnitt(start_c, end_c)
            if mid_p and start_c and end_c:
                definierte_hauptabschnitte_aktuell.append({
                    "start_stadt_name": abschnitt_def["start_stadt_name"],
                    "end_stadt_name": abschnitt_def["end_stadt_name"],
                    "start_coords": (start_c['lat'], start_c['lon']),
                    "end_coords": (end_c['lat'], end_c['lon']),
                    "midpoint": mid_p,
                    "fahrtrichtung": abschnitt_def["fahrtrichtung_grad"],
                    # Für Option 1 der Gegenrichtung: Speichere die Original-Startstadt für Wetterdaten
                    "wetter_daten_stadt": abschnitt_def.get("original_start_stadt_name_fuer_wetter",
                                                            abschnitt_def["start_stadt_name"])
                })

        for osm_way_coords in complete_osm_line_segments_for_autobahn:
            if not osm_way_coords or len(osm_way_coords) < 2: continue
            osm_way_midpoint = get_midpoint_of_way(osm_way_coords)
            if not osm_way_midpoint: continue

            best_matching_hauptabschnitt = None
            min_dist_sq_to_hauptabschnitt_mid = float('inf')
            for hauptabschnitt_data in definierte_hauptabschnitte_aktuell:
                dist_sq = calculate_distance_sq(osm_way_midpoint, hauptabschnitt_data["midpoint"])
                if dist_sq < min_dist_sq_to_hauptabschnitt_mid:
                    min_dist_sq_to_hauptabschnitt_mid = dist_sq
                    best_matching_hauptabschnitt = hauptabschnitt_data

            abschnitt_farbe = "lightgray"
            tooltip_text_abschnitt = (
                f"Autobahn: {autobahn_name}<br>"
                f"OSM Way Mid: ({osm_way_midpoint[0]:.3f}, {osm_way_midpoint[1]:.3f})"
            )
            if best_matching_hauptabschnitt:
                stadt_fuer_wetter = best_matching_hauptabschnitt["wetter_daten_stadt"]
                display_start_stadt = best_matching_hauptabschnitt["start_stadt_name"]  # Für Anzeige im Tooltip
                car_direction_deg = best_matching_hauptabschnitt["fahrtrichtung"]

                tooltip_text_abschnitt += (
                    f"<br>Hauptabschnitt (Display): {display_start_stadt} -> {best_matching_hauptabschnitt['end_stadt_name']}"
                    f"<br>Wetterdaten von: {stadt_fuer_wetter}"
                )

                wetter_eintrag = wetterdaten_aller_startstaedte.get(stadt_fuer_wetter)
                if wetter_eintrag:
                    temp_c = wetter_eintrag.get("main", {}).get("temp", 15)
                    druck_hpa = wetter_eintrag.get("main", {}).get("pressure", 1013)
                    wind_speed_mps = wetter_eintrag.get("wind", {}).get("speed", 0)
                    wind_direction_deg = wetter_eintrag.get("wind", {}).get("deg", 0)
                    wind_speed_kmh = wind_speed_mps * 3.6

                    verbrauch_l_100km, effizienz_score = calc_fuel_rating(
                        temp_c, wind_speed_kmh, wind_direction_deg, car_direction_deg, druck_hpa
                    )
                    gesammelte_verbrauchswerte_fuer_diese_karte.append(verbrauch_l_100km)
                    abschnitt_farbe = get_verbrauch_farbe(verbrauch_l_100km)
                    tooltip_text_abschnitt += (
                        f"<br>--- Eingabewerte ({stadt_fuer_wetter}) ---"
                        f"<br>Temp: {temp_c:.1f}°C, Druck: {druck_hpa} hPa"
                        f"<br>Wind: {wind_speed_mps:.2f} m/s ({wind_speed_kmh:.1f} km/h) aus {wind_direction_deg}°"
                        f"<br>Fahrtrichtung (Abschnitt): {car_direction_deg}°"
                        f"<br>--- Ergebnis ---"
                        f"<br>Verbrauch: {verbrauch_l_100km:.2f} l/100km, Score: {effizienz_score}"
                    )
                else:
                    abschnitt_farbe = "silver";
                    tooltip_text_abschnitt += f"<br>(Keine Wetterdaten für {stadt_fuer_wetter})"
            else:
                tooltip_text_abschnitt += "<br>(Kein passender Hauptabschnitt gefunden)"

            folium.PolyLine(
                locations=osm_way_coords, color=abschnitt_farbe, weight=5, opacity=0.7,
                tooltip=folium.Tooltip(tooltip_text_abschnitt)
            ).add_to(karte)

        # Fahrtrichtungspfeile für die aktuelle Definition
        for hauptabschnitt_data in definierte_hauptabschnitte_aktuell:
            pfeil_mid_lat, pfeil_mid_lon = hauptabschnitt_data["midpoint"]
            fahrtrichtung = hauptabschnitt_data["fahrtrichtung"]
            pfeil_start_fahrt = calculate_destination_point(pfeil_mid_lat, pfeil_mid_lon, (fahrtrichtung + 180) % 360,
                                                            fahrtrichtung_pfeil_laenge_km / 2)
            pfeil_ende_fahrt = calculate_destination_point(pfeil_mid_lat, pfeil_mid_lon, fahrtrichtung,
                                                           fahrtrichtung_pfeil_laenge_km / 2)
            pfeil_farbe = "black" if not ist_gegenrichtung_flag else "darkmagenta"  # Unterschiedliche Farbe für Pfeile der Gegenrichtung
            folium.PolyLine(locations=[pfeil_start_fahrt, pfeil_ende_fahrt], color=pfeil_farbe, weight=2,
                            opacity=0.6).add_to(karte)
            folium.RegularPolygonMarker(location=pfeil_ende_fahrt, fill_color=pfeil_farbe, color=pfeil_farbe,
                                        number_of_sides=3, radius=5, rotation=(fahrtrichtung - 90 + 360) % 360,
                                        opacity=0.6).add_to(karte)

    # Windpfeile (einmal pro Karte, da sie absolut sind)
    unique_wind_cities = set()
    for ab_data in original_autobahn_abschnitte_definition.values():
        for abschnitt_def in ab_data['abschnitte']:
            start_stadt_name = abschnitt_def["start_stadt_name"]
            if start_stadt_name not in unique_wind_cities:
                unique_wind_cities.add(start_stadt_name)
                start_stadt_coords = staedte_koordinaten_dict.get(start_stadt_name)
                if not start_stadt_coords: continue
                wetter_eintrag = wetterdaten_aller_startstaedte.get(start_stadt_name)
                if wetter_eintrag:
                    wind_speed_mps = wetter_eintrag.get("wind", {}).get("speed")
                    wind_deg_meteo = wetter_eintrag.get("wind", {}).get("deg")
                    if wind_speed_mps is not None and wind_deg_meteo is not None:
                        wind_pfeil_richtung_kompass = (wind_deg_meteo + 180) % 360
                        wind_pfeil_laenge_km = max(min_wind_arrow_length_km,
                                                   min(wind_speed_mps * wind_arrow_scale_factor,
                                                       max_wind_arrow_length_km))
                        pfeil_ende_wind = calculate_destination_point(start_stadt_coords['lat'],
                                                                      start_stadt_coords['lon'],
                                                                      wind_pfeil_richtung_kompass, wind_pfeil_laenge_km)
                        folium.PolyLine(
                            locations=[(start_stadt_coords['lat'], start_stadt_coords['lon']), pfeil_ende_wind],
                            color="darkblue", weight=2.5, opacity=0.8,
                            tooltip=f"Wind in {start_stadt_name}: {wind_speed_mps:.1f} m/s aus {wind_deg_meteo}°").add_to(
                            karte)
                        folium.RegularPolygonMarker(location=pfeil_ende_wind, fill_color='darkblue', color='darkblue',
                                                    number_of_sides=3, radius=6,
                                                    rotation=(wind_pfeil_richtung_kompass - 90 + 360) % 360).add_to(
                            karte)

    if gesammelte_verbrauchswerte_fuer_diese_karte:
        min_v = min(gesammelte_verbrauchswerte_fuer_diese_karte);
        max_v = max(gesammelte_verbrauchswerte_fuer_diese_karte)
        avg_v = sum(gesammelte_verbrauchswerte_fuer_diese_karte) / len(gesammelte_verbrauchswerte_fuer_diese_karte)
        print(f"\n--- Verbrauchsanalyse für {karten_dateiname_suffix} (l/100km) ---")
        print(f"  Min: {min_v:.2f}, Max: {max_v:.2f}, Avg: {avg_v:.2f}")
    else:
        print(f"\nKeine Verbrauchswerte für {karten_dateiname_suffix} berechnet.")

    karte.save(f"templates/autobahn_wetter_{karten_dateiname_suffix}.html")
    print(f"\n✅ Karte erfolgreich als 'autobahn_wetter_{karten_dateiname_suffix}.html' gespeichert.")


# --- HAUPTAUSFÜHRUNG ---
print("--- Erstelle Karte für ORIGINALFAHRTRICHTUNG ---")
erstelle_karte(original_autobahn_abschnitte_definition, "originalrichtung", ist_gegenrichtung_flag=False)

# Erstelle Definition für Gegenrichtung (Option 1: Gleiche Wetterdaten, nur Richtung gedreht)
gegenrichtung_definition = json.loads(json.dumps(original_autobahn_abschnitte_definition))  # Tiefe Kopie
for ab_name, ab_data in gegenrichtung_definition.items():
    for abschnitt in ab_data["abschnitte"]:
        # WICHTIG für Option 1: Die Stadt für die Wetterdaten bleibt die ursprüngliche Startstadt.
        # Wir fügen ein Feld hinzu, um dies in der `erstelle_karte` Funktion zu kennzeichnen.
        abschnitt["original_start_stadt_name_fuer_wetter"] = abschnitt["start_stadt_name"]
        # Die angezeigten Start/End-Städte und die Fahrtrichtung werden gedreht.
        original_start_fuer_anzeige = abschnitt["start_stadt_name"]
        abschnitt["start_stadt_name"] = abschnitt["end_stadt_name"]
        abschnitt["end_stadt_name"] = original_start_fuer_anzeige
        abschnitt["fahrtrichtung_grad"] = (abschnitt["fahrtrichtung_grad"] + 180) % 360

print("\n--- Erstelle Karte für GEGENFAHRTRICHTUNG (Wetterdaten von Original-Start, Richtung gedreht) ---")
erstelle_karte(gegenrichtung_definition, "gegenrichtung_option1", ist_gegenrichtung_flag=True)

# --- OSM Geometrie Cache speichern ---
if FORCE_OSM_REFRESH or not os.path.exists(OSM_GEOMETRY_CACHE_FILE) or osm_geometries_cache_data:
    if osm_geometries_cache_data:
        try:
            with open(OSM_GEOMETRY_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(osm_geometries_cache_data, f)
            print(f"INFO: OSM Geometrien erfolgreich in {OSM_GEOMETRY_CACHE_FILE} gespeichert/aktualisiert.")
        except Exception as e:
            print(f"FEHLER beim Speichern der OSM Geometrien in Cache {OSM_GEOMETRY_CACHE_FILE}: {e}")
    elif not os.path.exists(OSM_GEOMETRY_CACHE_FILE) and not FORCE_OSM_REFRESH:
        try:
            with open(OSM_GEOMETRY_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
            print(f"INFO: Leere OSM Geometrie-Cache-Datei {OSM_GEOMETRY_CACHE_FILE} erstellt.")
        except Exception as e:
            print(f"FEHLER beim Erstellen der leeren OSM Cache-Datei {OSM_GEOMETRY_CACHE_FILE}: {e}")

print("\nSkriptausführung beendet.")