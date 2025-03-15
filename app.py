from flask import Flask, request, render_template, send_file
import os
import io
import requests
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API token from environment variable
API_TOKEN = os.getenv("HF_API_TOKEN")
if not API_TOKEN:
    raise ValueError("No Hugging Face API token found. Please set the HF_API_TOKEN environment variable.")

# API endpoint for the Stable Diffusion model
API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"

def query_huggingface_api(payload):
    """Send a request to the Hugging Face API and return the response."""
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)

    # Check if the response contains an image
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

@app.route("/", methods=["GET"])
def index():
    """Render the main page."""
    image_data = request.args.get("image_data")
    prompt = request.args.get("prompt", "")
    error = request.args.get("error")
    return render_template("index.html", image_data=image_data, prompt=prompt, error=error)

from flask import redirect, url_for

@app.route("/generate", methods=["POST"])
def generate():
    """Handle image generation requests."""
    prompt = request.form.get("prompt", "")
    error = None
    image_data = None

    if prompt:
        # Set parameters for the model
        payload = {
            "inputs": prompt,
            "parameters": {
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
        }

        try:
            # Get image from API
            image_bytes = query_huggingface_api(payload)

            # Convert bytes to base64 for displaying in HTML
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            error = str(e)

    # Redirect to the home page with the image data
    return redirect(url_for("index", image_data=image_data, prompt=prompt, error=error))

@app.route("/download", methods=["POST"])
def download_image():
    """Handle image download requests."""
    image_data = request.form.get("image_data", "")

    if image_data:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Create a file-like object in memory
        image_io = io.BytesIO(image_bytes)

        # Return the image file
        return send_file(image_io, mimetype="image/png", as_attachment=True,
                         download_name="generated_image.png")

    return "No image data provided", 400

if __name__ == "__main__":
    app.run(debug=True)