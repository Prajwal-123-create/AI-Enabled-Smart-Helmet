
from flask import Flask, render_template, jsonify, request
import serial
import threading
import json
import time
import os

app = Flask(__name__)

latest = {
    "temperature": "--",
    "humidity": "--",
    "motion": "WAITING",
    "gas": "--",
    "alert": "WAITING"
}

# Local USB connection (works only on your computer)
def read_esp32():
    while True:
        try:
            with serial.Serial("COM7", 115200, timeout=2) as ser:
                time.sleep(2)
                while True:
                    line = ser.readline().decode(
                        "utf-8", errors="ignore"
                    ).strip()
                    if line.startswith("{"):
                        try:
                            data = json.loads(line)
                            update_data(data)
                        except json.JSONDecodeError:
                            pass
        except (serial.SerialException, OSError) as e:
            print("Local USB unavailable:", e)
            time.sleep(5)

def update_data(data):
    latest.update({
        "temperature": data.get("temperature", "--"),
        "humidity": data.get("humidity", "--"),
        "motion": data.get("motion", "WAITING"),
        "gas": data.get("gas", "--"),
        "alert": (
            "MOTION ALERT"
            if data.get("motion") == "ALERT"
            else "SAFE"
        )
    })

# Online endpoint: ESP32 sends JSON here over Wi-Fi
@app.route("/api/update", methods=["POST"])
def update():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send JSON data"}), 400

    update_data(data)
    return jsonify({"status": "ok"})

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/data")
def get_data():
    return jsonify(latest)

if __name__ == "__main__":
    # Render sets PORT automatically; local testing uses 5000
    port = int(os.environ.get("PORT", 5000))

    # Don't try opening COM7 on Render's remote server
    if os.name == "nt":
        threading.Thread(target=read_esp32, daemon=True).start()

    app.run(host="0.0.0.0", port=port, debug=False)
