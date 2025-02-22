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
    logging.info("Received request for invoice generation.")

    # Simple API key check
    if request.headers.get('X-API-Key') != API_KEY:
        logging.warning("Unauthorized access attempt.")
        return jsonify({"error": "Unauthorized"}), 403

    # Prevent concurrent processing
    if is_processing():
        logging.warning("Invoice processing already in progress.")
        return jsonify({"error": "Invoice processing already in progress"}), 429

    set_processing(True)
    try:
        logging.info("Starting invoice generation process...")
        # Simulate invoice generation process (replace with your Selenium code)
        time.sleep(30)  # Simulate a 30-second process; adjust as needed
        logging.info("Invoice generation process completed.")
    finally:
        set_processing(False)

    logging.info("Sending success response.")
    return jsonify({"result": "Invoice generated successfully"}), 200

if __name__ == '__main__':
    app.run()
