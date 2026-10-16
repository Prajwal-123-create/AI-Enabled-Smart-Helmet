
from flask import Flask, render_template, jsonify
import serial
import threading
import json
import time

app = Flask(__name__)

latest = {
    "temperature": "--",
    "humidity": "--",
    "motion": "WAITING",
    "gas": "--",
    "alert": "WAITING"
}

def read_esp32():
    while True:
        try:
            print("Connecting to ESP32 on COM7...")
            with serial.Serial("COM7", 115200, timeout=2) as ser:
                time.sleep(2)
                print("ESP32 connected!")

                while True:
                    line = ser.readline().decode(
                        "utf-8", errors="ignore"
                    ).strip()

                    if not line.startswith("{"):
                        continue

                    try:
                        data = json.loads(line)

                        latest.update({
                            "temperature": data.get("temperature")
                                if data.get("temperature") is not None
                                else "--",
                            "humidity": data.get("humidity")
                                if data.get("humidity") is not None
                                else "--",
                            "motion": data.get("motion", "WAITING"),
                            "gas": data.get("gas", "--"),
                            "alert": (
                                "MOTION ALERT"
                                if data.get("motion") == "ALERT"
                                else "SAFE"
                            )
                        })

                        print("Sensor data:", latest)

                    except json.JSONDecodeError:
                        pass

        except (serial.SerialException, OSError) as e:
            print("Serial connection error:", e)
            time.sleep(3)

threading.Thread(target=read_esp32, daemon=True).start()

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/data")
def data():
    return jsonify(latest)

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )