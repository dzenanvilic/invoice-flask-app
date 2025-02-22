import time
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
API_KEY = "1708990190042"  # Replace with a strong secret key
processing = False

# Configure logging to output INFO level messages
logging.basicConfig(level=logging.INFO)

def is_processing():
    global processing
    return processing

def set_processing(val):
    global processing
    processing = val

@app.route('/trigger-invoice', methods=['POST'])
def trigger_invoice():
    received_api_key = request.headers.get('X-API-Key')
    app.logger.info("Received API key: %s", received_api_key)

    if received_api_key != API_KEY:
        app.logger.warning("Unauthorized: API key does not match.")
        return jsonify({"error": "Unauthorized"}), 403

    if is_processing():
        app.logger.warning("Invoice processing already in progress.")
        return jsonify({"error": "Invoice processing already in progress"}), 429

    set_processing(True)
    try:
        app.logger.info("Starting invoice generation process...")
        time.sleep(30)  # Simulated processing time
        app.logger.info("Invoice generation process completed.")
    finally:
        set_processing(False)

    app.logger.info("Sending success response.")
    return jsonify({"result": "Invoice generated successfully"}), 200

if __name__ == '__main__':
    app.run()
