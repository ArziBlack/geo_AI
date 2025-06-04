import geoai
import os

# Define the geographic bounding box (example: area in Brazil)
bbox = [-76.6657, 39.2648, -76.6478, 39.2724]  # [min_lon, min_lat, max_lon, max_lat]

# Search for Sentinel-2 Level-2A data with low cloud cover
items = geoai.pc_stac_search(
    collection="naip",
    bbox=bbox,
    time_range="2013-01-01/2014-12-31",
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
    assets=["image", "thumbnail", "metadata", "rendered_preview"],  # NIR, Red, Green, Blue
)

print(f"Downloaded bands to {output_dir}")