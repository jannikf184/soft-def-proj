import json

import requests
import time
from datetime import datetime


# Schritt 1: Prometheus-Query
query = "weather_temperature"  # Oder deine konkrete Metrik

# Schritt 2: Anfrage senden


# Schritt 3: Ergebnisse ausgeben



class DataObject():
    def __init__(self, query):
        self.query = query
        self.data = self.get_prometheus_data()  # Daten holen

    def get_prometheus_data(self):
        url = "http://localhost:9090/api/v1/query"
        params = {"query": self.query}
        response = requests.get(url, params=params)
        return response.json()

    def get_results(self):
        data = self.data["data"]["result"]
        eintrag = {

        }
        for result in data:
            eintrag [result["metric"]["city"]] = result["value"][1]
        return eintrag

run = True
while run:
    session = DataObject("weather_temperature")
    with open('data.json', 'r') as outfile:
        data = json.load(outfile)

    result = session.get_results()
    if not data or data[0] != result:
        data.insert(0, result)
        data.insert(1,{"timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        with open('data.json', 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, indent=4)
            print("written")
    time.sleep(30)
