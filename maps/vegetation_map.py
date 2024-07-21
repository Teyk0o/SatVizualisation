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

def maskClouds(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

def generate_vegetation_map(static_dir):
    # Load the Sentinel-2 image collection for a given date range and region
    collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                  .filterDate(START_DATE, END_DATE)
                  .filterBounds(ee.Geometry.Polygon(FRANCE)))

    # Map the maskClouds function over the collection
    collection = collection.map(maskClouds)

    # Calculate the NDVI and take the mean over the collection
    def calculateNDVI(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    collection = collection.map(calculateNDVI)
    ndvi = collection.select('NDVI').mean()

    # Define visualization parameters for NDVI
    ndvi_vis_params = {
        'min': 0.0,
        'max': 1.0,
        'palette': ['blue', 'white', 'green']
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
        url = ndvi.getThumbURL({
            'region': ee.Geometry.Polygon([tile]),
            'dimensions': '512x512',  # Smaller dimensions for each tile
            'format': 'png',
            'min': ndvi_vis_params['min'],
            'max': ndvi_vis_params['max'],
            'palette': ndvi_vis_params['palette']
        })
        urls.append(url)
        print(f'URL de l\'image NDVI pour la tuile de végétation {idx + 1} : {url}')

    # Download images with progress bar
    for idx, url in enumerate(tqdm(urls, desc="Téléchargement des tuiles de végétation")):
        response = session.get(url)
        png_path = os.path.join(static_dir, f'vegetation_tile_{idx + 1}.png')
        with open(png_path, 'wb') as file:
            file.write(response.content)

    # Combine the images in the correct order
    order = [1, 2, 7, 4, 3, 8, 6, 5, 9]
    tiles_images = [Image.open(os.path.join(static_dir, f'vegetation_tile_{i}.png')) for i in order]

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
    legend_labels = ['Water/No Vegetation', 'Low Vegetation', 'High Vegetation']
    colors = ['blue', 'white', 'green']
    patches = [mpatches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(legend_labels))]
    plt.legend(handles=patches, loc='lower right', borderaxespad=0., fontsize='large')

    # Save the image with the legend
    plt.axis('off')
    legend_image_path = os.path.join(static_dir, 'vegetation_map_with_legend.png')
    plt.savefig(legend_image_path, bbox_inches='tight', pad_inches=0)
    plt.close()
