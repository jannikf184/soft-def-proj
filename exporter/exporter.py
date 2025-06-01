from http.server import HTTPServer, BaseHTTPRequestHandler
from keys import *
import time
import requests
import json
import sys
sys.path.append('../map')
API_KEY = load_API_KEY

with open ("staedte_koordinaten.json") as f:
    cities = json.load(f)


def fetch_history(lat, lon,k):
    end = int(time.time()) - k*3600
    start = end - (k+1)*3600
    url = (
        f"https://history.openweathermap.org/data/2.5/history/city"
        f"?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={API_KEY}&units=metric"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json()["list"]

def generate_metrics():
    metrics = ""
    for city in cities:
        lat = city["lat"]
        lon = city["lon"]
        city_name = city["name"]
        try:
            entries = []
            for k in range(0, 1):
                hourly_data = fetch_history(lat, lon, k)
                entries.extend(hourly_data)

            entries.sort(key=lambda x: x["dt"])
            latest = entries[-1]

            timestamp = latest["dt"]
            hour = time.strftime("%Y-%m-%dT%H:00:00Z", time.gmtime(timestamp))
            main = latest.get("main", {})
            wind = latest.get("wind", {})
            clouds = latest.get("clouds", {})
            weather = latest.get("weather", [{}])[0]  # 1. Eintrag aus Liste

            label = f'city="{city_name}",hour="{hour}"'

            metrics += (
                f'weather_temperature{{{label}}} {main.get("temp", 0)}\n'
                f'weather_feels_like{{{label}}} {main.get("feels_like", 0)}\n'
                f'weather_pressure{{{label}}} {main.get("pressure", 0)}\n'
                f'weather_humidity{{{label}}} {main.get("humidity", 0)}\n'
                f'weather_temp_min{{{label}}} {main.get("temp_min", 0)}\n'
                f'weather_temp_max{{{label}}} {main.get("temp_max", 0)}\n'
                f'weather_wind_speed{{{label}}} {wind.get("speed", 0)}\n'
                f'weather_wind_deg{{{label}}} {wind.get("deg", 0)}\n'
                f'weather_wind_gust{{{label}}} {wind.get("gust", 0)}\n'
                f'weather_clouds{{{label}}} {clouds.get("all", 0)}\n'
                f'weather_condition_id{{{label},main="{weather.get("main", "")}",desc="{weather.get("description", "")}"}} {weather.get("id", 0)}\n'
            )

        except Exception as e:
            metrics += f"# ERROR fetching data for {city_name}: {e}\n"

    return metrics

class PrometheusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(generate_metrics().encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), PrometheusHandler)
    print("Exporter läuft auf http://localhost:8000/metrics")
    server.serve_forever()