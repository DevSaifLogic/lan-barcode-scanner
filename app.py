import os
import threading
import time
from flask import Flask, render_template_string, request, jsonify
import pyautogui

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

# HTML template with embedded JavaScript barcode scanner
# Updated HTML template with scan cooldown to prevent spamming
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LAN Barcode Scanner</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 20px; background-color: #f4f4f9; }
        #reader { width: 100%; max-width: 500px; margin: 0 auto; background: white; border-radius: 8px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        #result { margin-top: 20px; font-size: 1.2em; font-weight: bold; color: #2c3e50; }
        .status { color: #27ae60; margin-bottom: 10px; }
        .cooldown { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <h1>LAN Barcode Scanner</h1>
    <div class="status">Connected to PC</div>
    <div id="reader"></div>
    <div id="result">Scan a barcode to paste it on PC...</div>

    <script>
        let isCooldown = false;
        let cooldownTime = 3000; // 3 seconds cooldown

        function onScanSuccess(decodedText, decodedResult) {
            // Prevent double-firing if already in cooldown
            if (isCooldown) return;
            isCooldown = true;

            // Vibrate mobile if supported
            if (navigator.vibrate) navigator.vibrate(200);
            
            const resultElement = document.getElementById('result');
            resultElement.replaceChildren(
                document.createTextNode("Scanned: " + decodedText),
                document.createElement('br')
            );
            const cooldownLabel = document.createElement('span');
            cooldownLabel.className = 'cooldown';
            cooldownLabel.textContent = 'Pausing for 3s...';
            resultElement.append(cooldownLabel);

            // Safely pause the camera scan tracking without tearing down the DOM nodes
            try {
                html5QrcodeScanner.pause(true); // true safely pauses the video flash/interaction
            } catch (err) {
                console.log("Pause handled gracefully:", err);
            }

            // Send data to Python PC Server
            fetch('/send_barcode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode: decodedText })
            })
            .then(response => response.json())
            .then(data => console.log('PC received barcode:', data))
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('result').innerText = "Error sending to PC";
            });

            // Cooldown timer to resume safely
            setTimeout(() => {
                try {
                    html5QrcodeScanner.resume();
                    isCooldown = false;
                    document.getElementById('result').innerText = "Ready for next scan...";
                } catch (err) {
                    console.error("Error resuming scanner:", err);
                    // Fallback: If it gets stuck, just allow scanning again
                    isCooldown = false;
                }
            }, cooldownTime);
        }

        function onScanFailure(error) {
            // Noise handling
        }

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: {width: 250, height: 150} }, false);
        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_barcode', methods=['POST'])
def send_barcode():
    data = request.get_json(silent=True)
    barcode_text = data.get('barcode') if isinstance(data, dict) else None

    if isinstance(barcode_text, str) and 0 < len(barcode_text.strip()) <= 128:
        barcode_text = barcode_text.strip()
        print(f"[+] Received Barcode: {barcode_text}")
        
        # Run the typing action in a separate thread so it doesn't block the web server
        threading.Thread(target=type_barcode, args=(barcode_text,)).start()
        
        return jsonify({"status": "success", "message": "Barcode pasted"}), 200
    return jsonify({"status": "error", "message": "A barcode of 1 to 128 characters is required"}), 400

def type_barcode(text):
    # Small delay to ensure OS focus transitions smoothly if needed
    time.sleep(0.1)
    # Types the text and presses 'enter'
    pyautogui.write(text)
    pyautogui.press('enter')

if __name__ == '__main__':
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    cert_file = os.environ.get("SSL_CERT_FILE")
    key_file = os.environ.get("SSL_KEY_FILE")
    if bool(cert_file) != bool(key_file):
        raise SystemExit("Set both SSL_CERT_FILE and SSL_KEY_FILE to enable HTTPS.")
    ssl_context = (cert_file, key_file) if cert_file else None

    print(f"Barcode scanner server: {'https' if ssl_context else 'http'}://{host}:{port}")
    if host == "127.0.0.1":
        print("For phone access on a trusted LAN, set HOST=0.0.0.0 and configure HTTPS.")
    app.run(host=host, port=port, ssl_context=ssl_context, debug=False)
