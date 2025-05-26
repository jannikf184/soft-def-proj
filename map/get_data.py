import requests
def get_prometheus_data(self):
    host = "localhost"  # localhost from ide prometheus from docker
    url = f"http://{host}:9090/api/v1/query"  # from docker
    params = {"query": self.query}
    response = requests.get(url, params=params)
    return response.json()