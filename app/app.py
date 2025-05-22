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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
