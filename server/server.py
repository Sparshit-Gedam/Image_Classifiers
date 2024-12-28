import base64
import io
from PIL import Image
from flask import Flask, request, jsonify, render_template
import util
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Log system information
print(f"Python Executable: {sys.executable}")
print(f"Current Working Directory: {os.getcwd()}")

# Flask app setup
app = Flask(__name__, static_folder="static")

# Upload folder setup
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Load artifacts during app startup
def load_saved_artifacts():
    try:
        logging.info("Loading saved artifacts...")
        util.load_saved_artifacts()
        logging.info("Artifacts loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load artifacts: {str(e)}")


# Favicon route (optional)
@app.route("/favicon.ico")
def favicon():
    return "", 204


# Home page route
@app.route("/")
def home():
    return render_template("app.html")


# File upload route for testing
@app.route("/file-upload", methods=["POST"])
def file_upload():
    if "file" not in request.files:
        logging.error("No file part in the request.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        logging.error("No file selected for upload.")
        return jsonify({"error": "No file selected for upload"}), 400

    # Save the file in the "uploads" folder
    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        logging.info(f"File uploaded successfully to {file_path}")
        return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Classification route
@app.route("/CLASSIFY_IMAGES", methods=["POST"])
def classify_image():
    try:
        # Extract image data from request
        image_data = request.form.get("image_data")
        logging.debug(f"Received image_data: {image_data}")
        if not image_data:
            logging.error("No image data provided.")
            return jsonify([{
              'class': None,
              'class_probability': [],
              'class_dictionary': {},
              'error': 'No image data provided'
            }])

        # Decode base64 image data
        if image_data.startswith("data:image"):
            image_data = image_data.split(',')[1]

        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        logging.debug("Image successfully decoded.")

        # Classify the image using util functions
        classification_result = util.classify_image(image)

        # Expected structure from `util.classify_image`:
        # classification_result = {
        #     "class": "lebron_james",
        #     "class_probability": [0.9, 0.05, 0.03, 0.02],
        #     "class_dictionary": {
        #         "cropped": 0,
        #         "lebron_james": 1,
        #         "michael_jordan": 2,
        #         "shaq": 3,
        #         "steph_curry": 4
        #     }
        # }

        # Ensure proper response format
        if not classification_result:
            return jsonify({"error": "No valid prediction found"}), 400

        # Wrap in a list as expected by the frontend
        response_data = [classification_result]

        logging.info(f"Classification result: {response_data}")

        # Return the result
        response = jsonify(response_data)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Endpoint for file upload testing
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        logging.error("No file part in the request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        logging.error("No file selected for upload.")
        return jsonify({"error": "No selected file"}), 400

    try:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        file_url = f"/static/uploads/{file.filename}"
        logging.info(f"File uploaded successfully to {filepath}")
        return jsonify({"file_url": file_url}), 200
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Main entry point
if __name__ == "__main__":
    logging.info("Starting Python Flask Server for NBA Players Image Classification")
    load_saved_artifacts()
    app.run(port=8000, debug=True)
