import map_genarator
test = ja.fetch_latest_weather_from_prometheus("Magdeburg")
print(test)

def fetch_latest_weather_datapoint_from_api(lat, lon, current_api_key):
    if not current_api_key or current_api_key == "YOUR_NEW_API_KEY": return None
    url = (
        f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={START_TIMESTAMP}&end={CURRENT_TIMESTAMP}&appid={current_api_key}&units=metric")
    try:
        r = requests.get(url, timeout=15);
        r.raise_for_status();
        api_response = r.json()
        hourly_data_list = api_response.get("list", []);
        return hourly_data_list[-1] if hourly_data_list else None
    except:
        return None

    @app.route('/auswertung', methods=['POST'])
    def auswertung():
        variables = request.form.getlist('option')
        graphs = []
        for variable in variables:
            session = DataObject(variable)
            plot = session.plot_data()
            plot_png = plot_to_html_image(plot)
            graphs.append([variable, plot_png])

        return render_template("auswertung.html", graphs=graphs)