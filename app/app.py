from flask import Flask, render_template, request
from map_genarator import *
import io
import base64
app = Flask(__name__)

def refresh_maps():
    erstelle_karte(original_autobahn_abschnitte_definition, "originalrichtung", ist_gegenrichtung_flag=False)
    erstelle_karte(gegenrichtung_definition, "gegenrichtung_option1", ist_gegenrichtung_flag=True)


def plot_to_html_image(plt):
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/map1', methods=['GET', 'POST'])
def show_map():
    refresh_maps()
    return render_template("autobahn_wetter_originalrichtung.html")

@app.route('/map2', methods=['GET', 'POST'])
def show_map_gegen():
    refresh_maps()
    return render_template("autobahn_wetter_gegenrichtung_option1.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
