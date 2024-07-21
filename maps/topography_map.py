import ee
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from tqdm import tqdm
import requests
from utils.constants import TILES, FRANCE, EE_PROJECT

# Initialize the Earth Engine library
ee.Initialize(project=EE_PROJECT)

def generate_topography_map(static_dir):
    # Load topographic data
    topography = ee.Image('USGS/SRTMGL1_003')
    elevation = topography.select('elevation')

    # Define visualization parameters for elevation
    elevation_vis_params = {
        'min': 0,
        'max': 4000,
        'palette': ['0000ff', '00ff00', 'ffff00', 'ff0000', 'ffffff']
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
        url = elevation.getThumbURL({
            'region': ee.Geometry.Polygon([tile]),
            'dimensions': '512x512',  # Smaller dimensions for each tile
            'format': 'png',
            'min': elevation_vis_params['min'],
            'max': elevation_vis_params['max'],
            'palette': elevation_vis_params['palette']
        })
        urls.append(url)
        print(f'URL de l\'image topographique pour la tuile {idx + 1} : {url}')

    # Download images with progress bar
    for idx, url in enumerate(tqdm(urls, desc="Téléchargement des tuiles topographiques")):
        response = session.get(url)
        png_path = os.path.join(static_dir, f'topography_tile_{idx + 1}.png')
        with open(png_path, 'wb') as file:
            file.write(response.content)

    # Combine the images in the correct order
    order = [1, 2, 7, 4, 3, 8, 6, 5, 9]
    tiles_images = [Image.open(os.path.join(static_dir, f'topography_tile_{i}.png')) for i in order]

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
    legend_labels = ['0m', '1000m', '2000m', '3000m', '4000m']
    colors = ['0000ff', '00ff00', 'ffff00', 'ff0000', 'ffffff']
    patches = [mpatches.Patch(color=f'#{colors[i]}', label=legend_labels[i]) for i in range(len(legend_labels))]
    plt.legend(handles=patches, loc='lower right', borderaxespad=0., fontsize='large')

    # Save the image with the legend
    plt.axis('off')
    legend_image_path = os.path.join(static_dir, 'topography_map_with_legend.png')
    plt.savefig(legend_image_path, bbox_inches='tight', pad_inches=0)
    plt.close()
