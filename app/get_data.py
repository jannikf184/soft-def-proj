import json

import requests
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt



class DataObject():
    def __init__(self, query):
        self.query = query
        self.data = self.get_prometheus_data()  # Daten holen

    def get_prometheus_data(self):
        host = "localhost" #localhost from ide prometheus from docker
        url = f"http://{host}:9090/api/v1/query" #from docker
        params = {"query": self.query}
        response = requests.get(url, params=params)
        return response.json()

    def create_df(self):
        df = pd.DataFrame(columns=('location', 'time', 'temperature'))
        data = self.data["data"]["result"]
        for metric in data:
            temperature = metric["value"][1]
            new_row = {'location':metric["metric"]["city"],'time':metric["metric"]["hour"],'temperature' : float(temperature) }
            df = df._append(new_row, ignore_index=True)
        return df

    def plot_data(self):
        df = self.create_df()
        df['time'] = pd.to_datetime(df['time'])
        df["rolling_avg"] = df["temperature"].rolling(window=24).mean()

        plt.figure(figsize=(10, 5))
        plt.plot(df['time'], df['temperature'], label='Temperatur')
        plt.plot(df['time'], df["rolling_avg"], label="Ø letzte 24 h", linestyle='--', color='gold')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        return plt
    def get_results(self):
        data = self.data["data"]["result"]

        eintrag = {

        }
        for result in data:
            eintrag [result["metric"]["city"]] = result["value"][1]
        return eintrag

data = DataObject("weather_temperature")
plt = data.plot_data()
plt.show()




#run = True
#while run:
#    session = DataObject("weather_temperature")
#    with open('data.json', 'r') as outfile:
#        data = json.load(outfile)
#
#    result = session.get_results()
#    if not data or data[0] != result:
#        data.insert(0, result)
#        data.insert(1,{"timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
#        with open('data.json', 'w', encoding="utf-8") as outfile:
#            json.dump(data, outfile, indent=4)
#            print("written")
#    time.sleep(30)
