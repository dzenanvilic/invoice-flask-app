from flask import Flask, request, jsonify
import logging
import invoice_processor  # Import your Selenium module
import os

app = Flask(__name__)
API_KEY = os.environ.get("API_KEY", "1708990190042")
processing = False

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
        app.logger.info("Starting invoice generation process via Selenium...")
        result = invoice_processor.process_all_orders()  # Call your Selenium processing function
        app.logger.info("Invoice generation process completed. Result: %s", result)
    except Exception as e:
        app.logger.error("Error during invoice generation: %s", e)
        result = str(e)
    finally:
        set_processing(False)

    app.logger.info("Sending response.")
    return jsonify({"result": result}), 200

if __name__ == '__main__':
    app.run()
