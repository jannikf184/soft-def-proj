import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from get_data import *
from flask import Flask, render_template, request
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
    data = DataObject("weather_temperature")
    plt = data.plot_data()
    graph_html = plot_to_html_image(plt)
    return render_template('index.html',graph_html=graph_html)

if __name__ == '__main__':
    app.run(debug=True)
