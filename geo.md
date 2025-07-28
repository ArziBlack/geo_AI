# geo_ai_corrected_two_functions.py
import modal

# --- Modal App and Image Definition ---
app = modal.App("geo-ai")

image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "fastapi[standard]", "geoai-py"
)

# --- Modal Function: download_satellite_image ---
# This function performs the work: search, download, zip.
# It should be 'def' if it doesn't use 'await', 'async def' otherwise.
# Based on previous analysis, geoai.pc_stac_download seems synchronous.
@app.function(image=image)
def download_satellite_image( # <-- Use 'def' if synchronous
    bbox=[-47.021, -3.854, -46.625, -3.403],
    time_range="2024-06-01/2024-06-15",
    collection="naip",
    max_items=10,
    assets=["image", "thumbnail", "metadata", "rendered_preview"]
):
    """
    Searches for, downloads, and zips satellite image assets.
    Returns the path to the created zip file.
    Raises ValueError or RuntimeError for specific issues.
    """
    import geoai
    import os
    import zipfile
    import logging

    # Setup logging for this function if needed
    # logging.basicConfig(level=logging.INFO) # Or use Modal's logging setup

    # Create output directory
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    # Search for satellite images
    items = geoai.pc_stac_search(
        collection=collection, bbox=bbox, time_range=time_range, max_items=max_items
    )

    if not items:
        raise ValueError(f"No items found for collection '{collection}' with the given parameters")

    # Download assets for the first item (synchronous call based on previous error)
    try:
        download_result = geoai.pc_stac_download( # No 'await'
            items[0],
            output_dir=output_dir,
            assets=assets,
        )
        logging.info(f"Downloaded bands to {output_dir}. Result: {download_result}")
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")

    # Create a zip file
    zip_filename = "satellite_data.zip"
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname=arcname)
        # Return the path to the zip file created locally within this Modal container
        logging.info(f"Successfully created zip file: {zip_filename}")
        return zip_filename # Return the string path
    except Exception as e:
        logging.error(f"Zipping failed: {str(e)}")
        raise RuntimeError(f"Failed to create zip file: {str(e)}")

# --- ASGI App: fastapi_app ---
# This function defines the FastAPI web application.
# It handles HTTP requests and interacts with the download_satellite_image function.
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    """
    Defines the FastAPI application with the /download-satellite-image endpoint.
    """
    # --- IMPORTANT: Import ALL necessary modules for THIS function's scope ---
    import logging
    import os  # <-- Import os (though we'll remove the check)
    # --- FIX 1: Import HTTPException ---
    from fastapi import FastAPI, Request, HTTPException # <-- ADDED HTTPException
    from fastapi.responses import FileResponse, JSONResponse
    # ------------------------------------

    web_app = FastAPI()

    @web_app.post("/download-satellite-image")
    async def download_endpoint(request: Request):
        """
        Handles POST requests to download and zip satellite imagery.
        """
        try:
            # --- Parse Request ---
            data = await request.json()
            logging.info(f"Received request: {data}")
            
            # Extract parameters with defaults
            bbox = data.get("bbox", [-47.021, -3.854, -46.625, -3.403])
            time_range = data.get("time_range", "2023-07-01/2023-07-15")
            collection = data.get("collection", "naip")
            max_items = data.get("max_items", 10)
            assets = data.get("assets", ["image", "thumbnail", "metadata", "rendered_preview"])

            # --- Validate Input ---
            supported_collections = ["naip", "sentinel-2-l2a", "landsat-c2-l2"]
            if collection not in supported_collections:
                return JSONResponse(
                    content={"error": f"Unsupported collection. Choose from: {', '.join(supported_collections)}"},
                    status_code=400
                )

            # --- Core Logic: Call the separate Modal Function ---
            # Using spawn/get as you preferred in the last iteration
            logging.info("Spawning download_satellite_image function...")
            function_call = download_satellite_image.spawn(
                bbox=bbox,
                time_range=time_range,
                collection=collection,
                max_items=max_items,
                assets=assets
            )
            
            # Block and wait for the result (the zip filename string)
            logging.info("Waiting for download_satellite_image function to complete...")
            zip_file_path = function_call.get() # <-- Gets the string result
            logging.info(f"Received zip file path from Modal function: {zip_file_path}")

            # --- Return File ---
            # --- FIX 2: Remove os.path.exists check ---
            # DO NOT check os.path.exists here. The file exists in the
            # download_satellite_image function's container, not this one's.
            # Modal handles transferring the file content for FileResponse.
            
            # Return the file. Modal ensures the content is available.
            return FileResponse(
                path=zip_file_path,              # The string path returned by .get()
                media_type="application/zip",   # Correct MIME type
                filename="satellite_data.zip"   # Suggested filename for download
            )
            # --- End Return File ---

        # --- Error Handling ---
        except ValueError as ve: # Catches errors raised by download_satellite_image
            logging.warning(f"ValueError from download_satellite_image: {str(ve)}")
            return JSONResponse(content={"error": str(ve)}, status_code=404)
        except RuntimeError as re: # Catches errors raised by download_satellite_image
            logging.error(f"RuntimeError from download_satellite_image: {str(re)}")
            return JSONResponse(content={"error": str(re)}, status_code=500)
        except Exception as e: # Catches unexpected errors in this endpoint
            logging.error(f"Unexpected error in fastapi_app download_endpoint: {str(e)}", exc_info=True)
            return JSONResponse(content={"error": "Internal server error"}, status_code=500)
        # --- End Error Handling ---

    return web_app

# --- End of File ---