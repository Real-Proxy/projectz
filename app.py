# app.py

from flask import Flask, request, jsonify
import os
import json
from werkzeug.utils import secure_filename

from extract.preprocess import preprocess_document
from extract.fetch_html import extract_html
from extract.fetch_pdf import extract_pdf
from extract.llm_infer import extract_api_endpoints
from extract.postprocess import parse_llm_output

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

EXTRACTED_FILE = "output/extracted_endpoints.json"
SELECTED_FILE = "output/selected_apis.json"

# Upload route: accepts either PDF file or URL and runs the full pipeline
@app.route("/upload", methods=["POST"])
def upload():
    # Case 1: PDF file via form-data
    if request.content_type and "multipart/form-data" in request.content_type:
        if "file" not in request.files:
            return jsonify({"error": "No file part in form-data"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Proceed with PDF extraction
        extract_pdf(file_path, output_path="output/raw_input.json")

    # Case 2: JSON with URL
    elif request.is_json:
        json_data = request.get_json()
        if "url" not in json_data:
            return jsonify({"error": "Missing 'url' field in JSON"}), 400
        url = json_data["url"]
        extract_html(url, output_path="output/raw_input.json")

    else:
        return jsonify({"error": "Provide either a PDF file (form-data) or a JSON body with 'url'"}), 400

    # Run extraction pipeline
    chunks = preprocess_document("output/raw_input.json", chunk_size=12000, output_path="output/cleaned_input.json")
    if len(chunks) == 0:
        return jsonify({"error": "No usable content found in input."}), 400

    extract_api_endpoints("output/cleaned_input.json", "output/llm_output.txt")
    parse_llm_output("output/llm_output.txt", EXTRACTED_FILE)

    return jsonify({"message": "Upload and extraction successful."}), 200


# Get summarized list of extracted API endpoints
@app.route("/endpoint-list", methods=["GET"])
def list_endpoint_summaries():
    if not os.path.exists(EXTRACTED_FILE):
        return jsonify({"error": "No extracted data available."}), 404

    with open(EXTRACTED_FILE) as f:
        data = json.load(f)

    summarized = [
        {
            "id": i,
            "method": ep.get("method", "GET"),
            "path": ep.get("path", ""),
            "name": ep.get("name", f"Endpoint {i}")
        }
        for i, ep in enumerate(data)
    ]
    return jsonify(summarized), 200

# Select specific endpoints by ID and save them
@app.route("/select", methods=["POST"])
def select_endpoints():
    try:
        if not os.path.exists(EXTRACTED_FILE):
            return jsonify({"error": "No extracted data available."}), 404

        with open(EXTRACTED_FILE) as f:
            all_endpoints = json.load(f)

        request_data = request.json
        selected_ids = request_data.get("selected_ids", [])

        if not isinstance(selected_ids, list):
            return jsonify({"error": "'selected_ids' must be a list"}), 400

        selected = [all_endpoints[i] for i in selected_ids if i < len(all_endpoints)]

        with open(SELECTED_FILE, "w") as f:
            json.dump(selected, f, indent=2)

        return jsonify({"message": "Selected endpoints saved", "count": len(selected)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
