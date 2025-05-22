#
NEW: 
### Launch the all in one Docker including starting the eyporter, prometheus and grafana -> still testing (try restarting device)
## use docker compose up

--------------------------------------------------------------------

## IMPORTANT: be in the working dictionary for launching prometheus
+ create a keys.py including the var load_API_KEY = "your API Keygit"


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


#Flask app

not part of the docker yet(not working) -> start in IDE
if starting from docker be sure to change host in get_data.py




