# main.py

import os
from maps.vegetation_map import generate_vegetation_map
from maps.topography_map import generate_topography_map
from maps.temperature_map import generate_temperature_map
from maps.moisture_map import generate_moisture_map
from flask import Flask, render_template

# Ensure the static directory exists
static_dir = os.path.join(os.getcwd(), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Generate maps
generate_vegetation_map(static_dir)
generate_topography_map(static_dir)
generate_temperature_map(static_dir)
generate_moisture_map(static_dir)

# Set up Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
                           vegetation_map='static/vegetation_map_with_legend.png',
                           topography_map='static/topography_map_with_legend.png',
                           temperature_map='static/temperature_map_with_legend.png',
                           moisture_map='static/moisture_map_with_legend.png')

if __name__ == '__main__':
    app.run()
