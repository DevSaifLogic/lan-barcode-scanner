# LAN Barcode Scanner

A local Windows app that scans a barcode using a phone camera and types the result, followed by Enter, on the host computer.

## Run locally

Run `run.bat`, or create a Python 3.10+ virtual environment and install `requirements.txt`. Open `http://127.0.0.1:5000` on the host computer.

Phone camera access requires HTTPS in a secure browser context. For phone use, create a local certificate for your LAN address and set `HOST=0.0.0.0`, `SSL_CERT_FILE`, and `SSL_KEY_FILE` before launching. Keep the certificate and private key outside Git.

The endpoint can type scanned input into the active desktop application. Do not expose it to the internet or an untrusted network.
