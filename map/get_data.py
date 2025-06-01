import requests
def get_prometheus_data(query):
    host = "localhost"  # localhost from ide prometheus from docker
    url = f"http://{host}:9090/api/v1/query"  # from docker
    params = {"query": query}
    response = requests.get(url, params=params)
    return response.json()

for query in ["weather_temperature","weather_wind_speed","weather_wind_deg"]:
    result = get_prometheus_data(query)["data"]["result"]
    for i in range(len(result)):
        print(result[i]["metric"]["city"],":",result[i]["value"][1])
