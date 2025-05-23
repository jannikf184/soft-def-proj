from get_data import DataObject
from flask import Flask, render_template, request
from plotting_expl import plot_germany_weather
import io
import base64
app = Flask(__name__)

def plot_to_html_image(plt):
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
@app.route('/auswertung', methods=['POST'])
def auswertung():
    variables = request.form.getlist('option')
    graphs = []
    for variable in variables:
        session = DataObject(variable)
        plot = session.plot_data()
        plot_png = plot_to_html_image(plot)
        graphs.append([variable,plot_png])

    return render_template("auswertung.html",graphs=graphs)

@app.route('/map', methods=['POST'])
def mapping():
    weather_data = [
        {"city": "Köln", "lat": 50.9333, "lon": 6.9500, "temperature": 12},
        {"city": "Berlin", "lat": 52.5200, "lon": 13.4050, "temperature": 10},
        {"city": "Ingolstadt", "lat": 48.7651, "lon": 11.4237, "temperature": 11},
        {"city": "München", "lat": 48.1374, "lon": 11.5755, "temperature": 13},
        {"city": "Kassel", "lat": 51.3167, "lon": 9.5000, "temperature": 9},
        {"city": "Hamburg", "lat": 53.5511, "lon": 9.9937, "temperature": 10},
        {"city": "Leipzig", "lat": 51.3396, "lon": 12.3713, "temperature": 12}
    ]
    plot = plot_germany_weather(weather_data)
    plot_png = plot_to_html_image(plot)
    return render_template("map.html",plot = plot_png)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
