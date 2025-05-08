## IMPORTANT: be in the working dictionary for launching prometheus
+ create a keys.py including the var load_API_KEY = "your API Key"


# Python/Flask
python wheather_exporter.py -> runs on http://localhost:8000/metrics
# Prometheus
### already done (config): 
nano prometheus.yml -> 
global:
  scrape_interval: 60s

scrape_configs:
  - job_name: 'weather_exporter'
    static_configs:
      - targets: ['localhost:8000']

### run prometheus:
prometheus --config.file=prometheus.yml -> Runs on http://localhost:9090/
Search in "enter expression" e.g. "wheater_temperature"

# Grafana
brew services start grafana -> Runs on http://localhost:3000
pw in passwords name admin




