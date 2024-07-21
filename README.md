# Mapping Project with Google Earth Engine and Satellite Imagery

This project is designed to map different regions of France using satellite imagery. It utilizes Python for data processing and analysis, with a focus on leveraging the Google Earth Engine for satellite data acquisition.

## Getting Started

To use this project, you will need to have Python installed on your machine. Additionally, the project requires access to the Google Earth Engine, which necessitates setting up an Earth Engine project.

### Prerequisites

- Python 3.6 or higher
- Google Earth Engine account
- PIL (Python Imaging Library) for image processing
- Matplotlib for generating the map legends and visualizations

### Installation

1. Clone the repository to your local machine.
2. Install the required Python packages:

```bash
pip install earthengine-api Pillow matplotlib
```

#### Configuration
Before running the project, you need to specify your Google Earth Engine project name in the utils/constants.py file:
    
```python
# Earth Engine project name
EE_PROJECT = 'your-project-name-here'
```

Replace 'your-project-name-here' with the name of your Earth Engine project.

### Usage

After setting up, you can run the main script to start the mapping process. The script will generate four maps for France, each showing a different data. The maps will be saved in the 'static' folder.
