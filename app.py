import json
import numpy as np
import librosa
import tensorflow as tf
from flask import Flask, request, jsonify
import logging
import os

#this is the cmd line for deploying
# gcloud run deploy coeurai-api --source . --region asia-south2 --allow-unauthenticated --clear-base-image

# Suppress TensorFlow logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# --- Configuration ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(APP_DIR, "end_to_end_model_legacy.tflite")
LABELS = ["Normal", "Pneumonia", "TB"]
SAMPLE_RATE = 16000
AUDIO_LENGTH_SAMPLES = 32000 # 2 second

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Load TFLite Model ---
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("Model loaded successfully.")

# --- Prediction Function ---
def predict_audio(file_storage):
    # Load audio file from in-memory file
    y, sr = librosa.load(file_storage, sr=SAMPLE_RATE, mono=True)

    # Pad or truncate to the required length
    if len(y) < AUDIO_LENGTH_SAMPLES:
        y = np.pad(y, (0, AUDIO_LENGTH_SAMPLES - len(y)))
    else:
        y = y[:AUDIO_LENGTH_SAMPLES]

    # Add batch & channel dimension and ensure correct type
    y = np.expand_dims(y, axis=(0, -1)).astype(np.float32)

    # Set tensor, invoke interpreter, and get results
    interpreter.set_tensor(input_details[0]['index'], y)
    interpreter.invoke()
    pred = interpreter.get_tensor(output_details[0]['index'])

    return pred[0]

# --- API Endpoint ---
@app.route("/predict", methods=["POST"])
def handle_predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        prediction_probs = predict_audio(file)

        # Format results with labels
        results = {label: float(prob) * 100 for label, prob in zip(LABELS, prediction_probs)}

        return jsonify(results)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"error": "Failed to process audio file"}), 500
