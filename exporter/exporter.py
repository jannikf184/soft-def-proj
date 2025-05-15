from http.server import HTTPServer, BaseHTTPRequestHandler
from keys import *
import time
import requests

API_KEY = load_API_KEY
CITIES = {
    "Ingolstadt,de": (48.7656, 11.4237),
}

def fetch_history(lat, lon,k):
    end = int(time.time()) - k*86400
    start = end - (k+1)*86400
    url = (
        f"https://history.openweathermap.org/data/2.5/history/city"
        f"?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={API_KEY}&units=metric"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json()["list"]

def generate_metrics():
    metrics = ""
    for city, (lat, lon) in CITIES.items():
        try:
            entries = []
            for k in range(0, 8):
                hourly_data = fetch_history(lat, lon, k)
                entries.extend(hourly_data)

            entries.sort(key=lambda x: x["dt"])

            for entry in entries:
                timestamp = entry["dt"]
                hour = time.strftime("%Y-%m-%dT%H:00:00Z", time.gmtime(timestamp))
                main = entry["main"]
                wind = entry.get("wind", {})
                city_label = f'city="{city}",hour="{hour}"'
                metrics += (
                    f'weather_temperature{{{city_label}}} {main["temp"]}\n'
                    f'weather_humidity{{{city_label}}} {main["humidity"]}\n'
                    f'weather_pressure{{{city_label}}} {main["pressure"]}\n'
                    f'weather_wind_speed{{{city_label}}} {wind.get("speed", 0)}\n')

        except Exception as e:
            metrics += f"# ERROR fetching data for {city}: {e}\n"

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