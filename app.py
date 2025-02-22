from flask import Flask, request, jsonify
import time

app = Flask(__name__)
API_KEY = "1708990190042"  # Replace with a strong secret key
processing = False

def is_processing():
    global processing
    return processing

def set_processing(val):
    global processing
    processing = val

@app.route('/trigger-invoice', methods=['POST'])
def trigger_invoice():
    # Simple API key check
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    # Prevent concurrent processing
    if is_processing():
        return jsonify({"error": "Invoice processing already in progress"}), 429

    set_processing(True)
    try:
        # Simulate invoice generation process (replace with your Selenium code)
        time.sleep(30)  # Simulate a 30-second process; adjust as needed
    finally:
        set_processing(False)

    return jsonify({"result": "Invoice generated successfully"}), 200

if __name__ == '__main__':
    app.run()
