
from http.server import HTTPServer, BaseHTTPRequestHandler
from keys import load_API_KEY
import requests
API_KEY = load_API_KEY
CITIES = ["Berlin,de", "Ingolstadt,de", "Hamburg,de","Koeln,de"]

def generate_metrics():
    metrics = ""
    for city in CITIES:
        try:
            r = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            )
            data = r.json()
            main = data['main']
            wind = data['wind']
            clouds = data.get('clouds', {}).get('all', 0)
            weather = data['weather'][0]['main']  # z. B. Clear, Rain, etc.

            temp = main['temp']
            humidity = main['humidity']
            pressure = main['pressure']
            wind_speed = wind['speed']

            city_label = f'city="{city}"'

            metrics += (
                f'# HELP weather_temperature Temperature in Celsius\n'
                f'# TYPE weather_temperature gauge\n'
                f'weather_temperature{{{city_label}}} {temp}\n'

                f'# HELP weather_humidity Relative humidity in %\n'
                f'# TYPE weather_humidity gauge\n'
                f'weather_humidity{{{city_label}}} {humidity}\n'

                f'# HELP weather_pressure Atmospheric pressure in hPa\n'
                f'# TYPE weather_pressure gauge\n'
                f'weather_pressure{{{city_label}}} {pressure}\n'

                f'# HELP weather_wind_speed Wind speed in m/s\n'
                f'# TYPE weather_wind_speed gauge\n'
                f'weather_wind_speed{{{city_label}}} {wind_speed}\n'

                f'# HELP weather_cloudiness Cloud cover in %\n'
                f'# TYPE weather_cloudiness gauge\n'
                f'weather_cloudiness{{{city_label}}} {clouds}\n'

                f'# HELP weather_condition Weather condition (as label)\n'
                f'# TYPE weather_condition gauge\n'
                f'weather_condition{{{city_label},condition="{weather}"}} 1\n'
            )

        except Exception as e:
            metrics += f'# ERROR fetching data for {city}: {e}\n'

    return metrics

def make_handler():
    def handler(*args):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/metrics':
                    response = generate_metrics()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; version=0.0.4')
                    self.end_headers()
                    self.wfile.write(response.encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()
        Handler(*args)
    return handler

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), make_handler())
    print("Exporter läuft auf http://localhost:8000/metrics")
    server.serve_forever()