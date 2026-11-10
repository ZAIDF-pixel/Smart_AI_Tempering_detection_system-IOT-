from flask import Flask, request, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

CSV_FILE = "atm_dataset.csv"

# Create CSV file with headings
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "timestamp",
            "vibration",
            "door",
            "alarm",
            "label"
        ])

@app.route("/")
def home():
    return "ATM Security Monitoring Server is Running!"

@app.route("/sensor", methods=["POST"])
def receive_sensor_data():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    vibration = int(data.get("vibration", 0))
    door = int(data.get("door", 0))
    alarm = int(data.get("alarm", 0))

    # 0 = Normal, 1 = Tampering
    label = 1 if vibration == 1 or door == 1 else 0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp,
            vibration,
            door,
            alarm,
            label
        ])

    print(timestamp, vibration, door, alarm, label)

    return jsonify({"message": "Data saved successfully"}), 200

if __name__ == "__main__":
    print("ATM Security Server Started")
    app.run(host="0.0.0.0", port=8000)