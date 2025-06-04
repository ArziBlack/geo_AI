import geoai
import os
import zipfile
import io
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route("/api/download-satellite-image", methods=["POST"])
def download_satellite_image():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Extract parameters with defaults
        bbox = data.get("bbox", [-47.021, -3.854, -46.625, -3.403])  # Default: Brazil area
        time_range = data.get("time_range", "2023-07-01/2023-07-15")
        assets = data.get("assets", ["image", "thumbnail", "metadata", "rendered_preview"])  # NIR, Red, Green, Blue
        collection = data.get("collection", "naip")
        max_items = data.get("max_items", 10)

        # Validate bbox
        if not isinstance(bbox, list) or len(bbox) != 4:
            return jsonify({"error": "Invalid bbox format. Must be [min_lon, min_lat, max_lon, max_lat]"}), 400

        # Search for Sentinel-2 data
        items = geoai.pc_stac_search(
            collection=collection,
            bbox=bbox,
            time_range=time_range,
            max_items=max_items
        )

        if not items:
            return jsonify({"error": "No items found for the specified criteria"}), 404

        # Create temporary directory for downloads
        output_dir = "temp_downloads"
        os.makedirs(output_dir, exist_ok=True)

        # Download bands for the first item
        geoai.pc_stac_download(
            items[0],
            output_dir=output_dir,
            assets=assets,
            max_workers=1
        )

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                if os.path.isfile(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))

        # Reset buffer position
        zip_buffer.seek(0)

        # Clean up temporary directory
        for filename in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, filename))
        os.rmdir(output_dir)

        # Return ZIP file as response
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="satellite_data.zip"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)