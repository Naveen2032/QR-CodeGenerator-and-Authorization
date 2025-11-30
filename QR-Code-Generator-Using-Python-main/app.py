from flask import Flask, render_template, jsonify, request, send_file
import qrcode
import os
import threading
import cv2
import numpy as np
from pyzbar.pyzbar import decode

app = Flask(__name__)

# Function to generate QR code and store text in a file
def generate_qr_code_and_store(text):
    qr = qrcode.make(text)
    qr.save('static/myQRCode.png')  # Save QR code image
    
    with open('static/myDataFile.txt', 'a') as f:
        f.write(text + '\n')  # Append text with a newline
    
    return text

# Route to render the index.html template
@app.route('/')
def index():
    return render_template('index.html')

# Route to render the scan.html template
@app.route('/scan')
def scan():
    return render_template('scan.html')
@app.route('/fetch_data')
def fetch_data():
    with open('static/myDataFile.txt') as f:
        myDataList = f.read().splitlines()
    return jsonify({"authorizedData": myDataList})
# Route to generate QR code from given text and return text
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    text = data.get('text')
    if text:
        generated_text = generate_qr_code_and_store(text)
        return jsonify({"text": generated_text})
    else:
        return jsonify({"error": "No text provided"}), 400

# Route to download QR code image
@app.route('/download_qr')
def download_qr():
    try:
        qr_code_path = 'static/myQRCode.png'
        
        if os.path.exists(qr_code_path):
            return send_file(qr_code_path, as_attachment=True)
        else:
            return jsonify({"error": "QR code image not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to start QR code scanning using OpenCV
@app.route('/start_scan')
def start_scan():
    def scan_qr_code():
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)  # Set width
        cap.set(4, 480)  # Set height

        with open('static/myDataFile.txt') as f:
            myDataList = f.read().splitlines()

        while True:
            success, img = cap.read()
            for barcode in decode(img):
                myData = barcode.data.decode('utf-8')
                print(myData)

                if myData in myDataList:
                    myOutput = 'Authorized'
                    myColor = (0, 255, 0)  # Green for authorized
                else:
                    myOutput = 'Un-Authorized'
                    myColor = (0, 0, 255)  # Red for unauthorized

                pts = np.array([barcode.polygon], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img, [pts], True, myColor, 5)
                pts2 = barcode.rect
                cv2.putText(img, myOutput, (pts2[0], pts2[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.9, myColor, 2)

            cv2.imshow('Result', img)
            cv2.waitKey(1)

    threading.Thread(target=scan_qr_code).start()
    return "QR Code scanning started."

if __name__ == '__main__':
    app.run(debug=True)
