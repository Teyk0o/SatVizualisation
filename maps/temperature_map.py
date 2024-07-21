# temperature_map.py

import ee
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from tqdm import tqdm
import requests
from utils.constants import TILES, START_DATE, END_DATE, FRANCE, EE_PROJECT

# Initialize the Earth Engine library
ee.Initialize(project=EE_PROJECT)

def generate_temperature_map(static_dir):
    # Load temperature data
    temperature_collection = (ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
                              .filterDate(START_DATE, END_DATE)
                              .filterBounds(ee.Geometry.Polygon(FRANCE)))
    temperature = temperature_collection.select('temperature_2m').mean().subtract(273.15)  # Convert from Kelvin to Celsius

    # Define visualization parameters for temperature
    temperature_vis_params = {
        'min': -10,
        'max': 30,
        'palette': ['0000ff', '00ffff', 'ffff00', 'ff0000']
    }

    # Create a session with retry logic
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    # Generate download URLs and download images for each tile
    urls = []
    for idx, tile in enumerate(TILES):
        url = temperature.getThumbURL({
            'region': ee.Geometry.Polygon([tile]),
            'dimensions': '512x512',  # Smaller dimensions for each tile
            'format': 'png',
            'min': temperature_vis_params['min'],
            'max': temperature_vis_params['max'],
            'palette': temperature_vis_params['palette']
        })
        urls.append(url)
        print(f'URL de l\'image de température pour la tuile {idx + 1} : {url}')

    # Download images with progress bar
    for idx, url in enumerate(tqdm(urls, desc="Téléchargement des tuiles de température")):
        response = session.get(url)
        png_path = os.path.join(static_dir, f'temperature_tile_{idx + 1}.png')
        with open(png_path, 'wb') as file:
            file.write(response.content)

    # Combine the images in the correct order
    order = [1, 2, 7, 4, 3, 8, 6, 5, 9]
    tiles_images = [Image.open(os.path.join(static_dir, f'temperature_tile_{i}.png')) for i in order]

    # Combine the images into a grid
    width, height = tiles_images[0].size
    combined_image = Image.new('RGB', (width * 3, height * 3))  # Adjust grid size

    for i, tile_image in enumerate(tiles_images):
        x = (i % 3) * width
        y = (i // 3) * height
        combined_image.paste(tile_image, (x, y))

    # Add a legend to the image
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(combined_image)

    # Create a custom legend
    legend_labels = ['-10°C', '0°C', '15°C', '30°C']
    colors = ['0000ff', '00ffff', 'ffff00', 'ff0000']
    patches = [mpatches.Patch(color=f'#{colors[i]}', label=legend_labels[i]) for i in range(len(legend_labels))]
    plt.legend(handles=patches, loc='lower right', borderaxespad=0., fontsize='large')

    # Save the image with the legend
    plt.axis('off')
    legend_image_path = os.path.join(static_dir, 'temperature_map_with_legend.png')
    plt.savefig(legend_image_path, bbox_inches='tight', pad_inches=0)
    plt.close()