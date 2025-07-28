# geo_ai_single_function.py
import modal

# --- Modal App and Image Definition ---
app = modal.App("geo-ai-single")

# Define the base image with required dependencies
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "fastapi[standard]", "geoai-py"
)

# --- Single ASGI App Function ---
# This function defines the FastAPI web application AND performs the download/zip logic internally.
@app.function(image=image)
@modal.asgi_app()
def web_app_and_processor(): # <-- Single function name
    """
    A single Modal function that serves a FastAPI app and handles satellite image processing internally.
    """
    import geoai
    import os
    import zipfile
    import logging
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import FileResponse, JSONResponse

    # Create the FastAPI application instance
    web_app = FastAPI()

    # Define the POST endpoint
    @web_app.post("/download-satellite-image")
    async def download_endpoint(request: Request): # Handler function
        """
        Handles POST requests. Performs search, download, and zip all within this single function call.
        """
        # --- Internal Processing Logic ---
        # This block contains the logic previously in 'download_satellite_image'
        def _internal_download_and_zip( # Helper to encapsulate the logic
            bbox, time_range, collection, max_items, assets
        ):
            """Internal synchronous function to perform the download and zip."""
            # Create output directory
            output_dir = "data"
            os.makedirs(output_dir, exist_ok=True)

            # Search for satellite images
            items = geoai.pc_stac_search(
                collection=collection, bbox=bbox, time_range=time_range, max_items=max_items
            )

            if not items:
                raise ValueError(f"No items found for collection '{collection}' with the given parameters")

            # Download assets for the first item (synchronous call)
            try:
                geoai.pc_stac_download(
                    items[0],
                    output_dir=output_dir,
                    assets=assets,
                )
                logging.info(f"Downloaded bands to {output_dir}")
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
                logging.info(f"Successfully created zip file: {zip_filename}")
                return zip_filename
            except Exception as e:
                logging.error(f"Zipping failed: {str(e)}")
                raise RuntimeError(f"Failed to create zip file: {str(e)}")
        # --- End Internal Processing Logic ---

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
            supported_collections = ["naip", "sentinel-2-l2a", "landsat-c2-l2", "sentinel-2-l1c"]
            if collection not in supported_collections:
                return JSONResponse(
                    content={"error": f"Unsupported collection. Choose from: {', '.join(supported_collections)}"},
                    status_code=400
                )

            # --- Core Logic: Execute Processing Internally ---
            # Call the internal helper function directly within this Modal function's container.
            logging.info("Starting internal download and zip process...")
            zip_file_path = _internal_download_and_zip(
                bbox=bbox,
                time_range=time_range,
                collection=collection,
                max_items=max_items,
                assets=assets
            )
            logging.info(f"Internal process completed. Zip file path: {zip_file_path}")

            # --- Return File ---
            # The file 'zip_file_path' was created in this same container's filesystem.
            # We can check its existence and serve it directly.
            if os.path.exists(zip_file_path):
                return FileResponse(
                    path=zip_file_path,
                    media_type="application/zip",
                    filename="satellite_data.zip"
                )
            else:
                # This would be unexpected if _internal_download_and_zip succeeded
                error_msg = f"Expected zip file {zip_file_path} not found locally."
                logging.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        # --- Error Handling ---
        except ValueError as ve:
            logging.warning(f"ValueError during processing: {str(ve)}")
            return JSONResponse(content={"error": str(ve)}, status_code=404)
        except RuntimeError as re:
            logging.error(f"RuntimeError during processing: {str(re)}")
            return JSONResponse(content={"error": str(re)}, status_code=500)
        except Exception as e:
            logging.error(f"Unexpected error in download_endpoint: {str(e)}", exc_info=True)
            return JSONResponse(content={"error": "Internal server error"}, status_code=500)
        # --- End Error Handling ---

    # Return the configured FastAPI application instance
    return web_app

# --- End of File ---