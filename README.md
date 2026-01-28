# geo_AI Project

This project, `geo_AI`, is a Python-based setup for working with geospatial AI data using the `geoai-py` package. It includes an example implementation for searching, visualizing, and downloading Sentinel-2 imagery from Microsoft’s Planetary Computer, as outlined in the [GeoAI Planetary Computer example](https://geoai.gishub.org/examples/planetary_computer/).

## Prerequisites

- **Python**: Version 3.8 or higher.
- **Operating System**: Windows, macOS, or Linux.
- **Internet Connection**: Required for installing packages and accessing the Planetary Computer API.

## Installation

Follow these steps to set up the `geo_AI` project on your local machine.

### Step 1: Create the Project Directory
Create a dedicated directory for the project and navigate into it:

```bash
mkdir geo_AI
cd geo_AI
```

### Step 2: Set Up a Virtual Environment
Create and activate a virtual environment to isolate project dependencies:

- **Create**:
  ```bash
  python -m venv venv
  ```
- **Activate**:
  - On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```
  - On Windows:
    ```bash
    venv/Scripts/activate
    ```

### Step 3: Install the GeoAI Package
With the virtual environment active, install the `geoai-py` package using pip:

```bash
pip install geoai-py
```

Optionally, ensure dependencies are up-to-date:

```bash
pip install --upgrade geoai-py torchgeo
```

### Step 4: Verify Installation
Confirm that `geoai-py` is installed by checking its version:

```bash
python -c "import geoai; print(geoai.__version__)"
```

## Usage

The project includes an example script to interact with Microsoft’s Planetary Computer, specifically for searching, visualizing, and downloading Sentinel-2 imagery. Follow these steps to use it.

### Step 1: Create the Example Script
Create a file named `planetary_computer.py` in the `geo_AI` directory with the following content:

```python
import geoai
import os

# Define the geographic bounding box (example: area in Brazil)
bbox = [-47.021, -3.854, -46.625, -3.403]  # [min_lon, min_lat, max_lon, max_lat]

# Search for Sentinel-2 Level-2A data with low cloud cover
items = geoai.pc_stac_search(
    collection="sentinel-2-l2a",
    bbox=bbox,
    time_range="2023-07-01/2023-07-15",
    query={"eo:cloud_cover": {"lt": 1}},  # Less than 1% cloud cover
    max_items=10
)

# Check if items were found
if not items:
    print("No items found for the specified criteria.")
    exit()

# Visualize the first item with NDVI
geoai.view_pc_item(
    item=items[0],
    expression="(B08-B04)/(B08+B04)",  # NDVI formula: (NIR - Red) / (NIR + Red)
    rescale="-1,1",
    colormap_name="greens",
    name="NDVI Green"
)

# Create output directory for downloaded data
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

# Download specific bands (e.g., NIR, Red, Green, Blue)
geoai.pc_stac_download(
    items[0],
    output_dir=output_dir,
    assets=["B08", "B04", "B03", "B02"],  # NIR, Red, Green, Blue
    max_workers=1
)

print(f"Downloaded bands to {output_dir}")
```

### Step 2: Run the Script
Ensure the virtual environment is active, then run the script:

```bash
python planetary_computer.py
```

### Expected Output
- **Visualization**: An interactive map displaying the NDVI (Normalized Difference Vegetation Index) for the selected Sentinel-2 item, using a green colormap.
- **Files**: GeoTIFF files for the specified bands (e.g., `B08.tif`, `B04.tif`, `B03.tif`, `B02.tif`) saved in the `geo_AI/data` directory.
- **Console**: A message confirming the download, such as `Downloaded bands to data`.

### Customizations
- **Bounding Box**: Modify `bbox` to target a different area (e.g., `[-122.5, 37.7, -122.3, 37.9]` for San Francisco).
- **Time Range**: Change `time_range` to a different period (e.g., `"2024-01-01/2024-01-31"`).
- **Bands**: Adjust `assets` to download other Sentinel-2 bands (e.g., `["B01", "B11"]` for coastal aerosol or SWIR).
- **Visualization**: Experiment with different expressions or colormaps (see [GeoAI documentation](https://geoai.gishub.org)).

## Troubleshooting

- **No Items Found**: If the script returns "No items found," adjust the `bbox`, `time_range`, or increase the cloud cover limit (e.g., `{"eo:cloud_cover": {"lt": 10}}`).
- **Dependency Issues**: Update dependencies with `pip install --upgrade geoai-py torchgeo`.
- **Visualization Errors**: If the map doesn’t display, try running the script in a Jupyter notebook or install `ipympl` (`pip install ipympl`).
- **Authentication**: Some Planetary Computer features may require AWS credentials or a Planetary Computer account. Refer to the [Planetary Computer documentation](https://planetarycomputer.microsoft.com/docs/overview/) for setup instructions.

## Resources

- **GeoAI Documentation**: [https://geoai.gishub.org](https://geoai.gishub.org)
- **Planetary Computer Example**: [https://geoai.gishub.org/examples/planetary_computer/](https://geoai.gishub.org/examples/planetary_computer/)
- **GeoAI Tutorials**: [https://geoai-tutorials.gishub.org](https://geoai-tutorials.gishub.org)
- **Planetary Computer Docs**: [https://planetarycomputer.microsoft.com/docs/overview/](https://planetarycomputer.microsoft.com/docs/overview/)
- **Contributing**: [https://geoai.gishub.org/contributing](https://geoai.gishub.org/contributing)

## License

The `geoai-py` package is licensed under the MIT License. See the [GeoAI website](https://geoai.gishub.org) for details.

## Notes

- The `geoai-py` package is under active development, so some features may evolve. Check the documentation for updates.
- For advanced usage, explore additional examples on the GeoAI website or video tutorials on [YouTube](https://bit.ly/GeoAI-Tutorials).