import os
import smtplib
import uuid
import threading
import time

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import deque
from email.message import EmailMessage

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from twilio.rest import Client

from ml_model import predict_tampering


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv(
    dotenv_path=Path(__file__).with_name(".env")
)


# ==========================================
# FLASK CONFIGURATION
# ==========================================

app = Flask(__name__)

history = deque(maxlen=100)

history_lock = threading.Lock()
latest_lock = threading.Lock()
alert_lock = threading.Lock()
dashboard_alert_lock = threading.Lock()

latest_data = {}
alert_is_active = False

# Dashboard alert memory
dashboard_alert_until = 0.0
last_tampering_event = {}


# ==========================================
# EMAIL CONFIGURATION
# ==========================================

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# ==========================================
# TWILIO CONFIGURATION
# ==========================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER")


# ==========================================
# PROJECT CONFIGURATION
# ==========================================

ATM_LOCATION = os.getenv(
    "ATM_LOCATION",
    "ATM Prototype - Laboratory"
)


print("\n================================")
print("     ATM SECURITY SYSTEM")
print("================================")

print(
    "Gmail:",
    "Configured" if all([
        EMAIL_FROM,
        EMAIL_TO,
        GMAIL_APP_PASSWORD
    ]) else "Missing credentials"
)

print(
    "Twilio:",
    "Configured" if all([
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_FROM_NUMBER,
        TWILIO_TO_NUMBER
    ]) else "Missing credentials"
)

print("ML Model: Loaded")
print("================================\n")


# ==========================================
# EMAIL NOTIFICATION
# ==========================================

def send_email(
    alert_id,
    current_time,
    vibration,
    door,
    alarm,
    ml_prediction,
    detection_type,
    history_records
):

    if not all([
        EMAIL_FROM,
        EMAIL_TO,
        GMAIL_APP_PASSWORD
    ]):
        print("Email skipped: Missing credentials")
        return

    vibration_status = (
        "DETECTED" if vibration == 1 else "NORMAL"
    )

    door_status = (
        "OPEN" if door == 1 else "CLOSED"
    )

    ml_status = (
        "TAMPERING DETECTED"
        if ml_prediction == 1
        else "NORMAL"
    )

    # Only latest 3 records
    history_text = ""

    for record in history_records[-3:]:

        history_text += (
            f"Time: {record['timestamp']}\n"
            f"Vibration: {record['vibration']}\n"
            f"Door: {record['door']}\n"
            f"Alarm: {record['alarm']}\n"
            "-------------------------\n"
        )

    msg = EmailMessage()

    msg["Subject"] = (
        f"ATM SECURITY ALERT - {alert_id}"
    )

    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    msg.set_content(f"""
========================================
       ATM SECURITY MONITORING SYSTEM
========================================

SECURITY ALERT: TAMPERING DETECTED

ALERT INFORMATION
----------------------------------------
Alert ID       : {alert_id}
Date and Time  : {current_time}
Location       : {ATM_LOCATION}

SENSOR INFORMATION
----------------------------------------
Vibration      : {vibration_status} ({vibration})
Door Status    : {door_status} ({door})

DETECTION DETAILS
----------------------------------------
Detection Type : {detection_type}

ML PREDICTION
----------------------------------------
Model Result   : {ml_status}

LATEST 3 SENSOR HISTORY RECORDS
----------------------------------------
{history_text}

RECOMMENDED ACTION
----------------------------------------
Please inspect the ATM prototype
and verify the sensor readings.

Automated notification from
ATM Security Monitoring System.

========================================
""")

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=15
        ) as server:

            server.starttls()

            server.login(
                EMAIL_FROM,
                GMAIL_APP_PASSWORD
            )

            server.send_message(msg)

        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:

        print("EMAIL FAILED:", repr(e))


# ==========================================
# SMS NOTIFICATION
# ==========================================

def send_sms(
    alert_id,
    current_time,
    vibration,
    door,
    detection_type
):

    if not all([
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_FROM_NUMBER,
        TWILIO_TO_NUMBER
    ]):

        print("SMS skipped: Missing credentials")
        return

    try:

        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

        message = client.messages.create(

            body=f"""
ATM SECURITY ALERT!

Alert ID: {alert_id}
Time: {current_time}
Location: {ATM_LOCATION}

Detection: {detection_type}
Vibration: {vibration}
Door: {door}

Please inspect the ATM prototype.
""",

            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )

        print("SMS SUBMITTED:", message.sid)

    except Exception as e:

        print("SMS FAILED:", repr(e))


# ==========================================
# BACKGROUND NOTIFICATIONS
# ==========================================

def send_notifications(
    alert_id,
    current_time,
    vibration,
    door,
    alarm,
    ml_prediction,
    detection_type,
    history_records
):

    send_email(
        alert_id,
        current_time,
        vibration,
        door,
        alarm,
        ml_prediction,
        detection_type,
        history_records
    )

    send_sms(
        alert_id,
        current_time,
        vibration,
        door,
        detection_type
    )


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "system": "ATM Security Monitoring System",
        "status": "Server Running",
        "message": "ESP32 server is ready"
    })


# ==========================================
# RECEIVE SENSOR DATA
# ==========================================

@app.route("/sensor", methods=["POST"])
def receive_sensor():

    global alert_is_active
    global dashboard_alert_until
    global last_tampering_event

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Invalid JSON data"
        }), 400

    try:

        vibration = int(data.get("vibration"))
        door = int(data.get("door"))

        if vibration not in (0, 1) or door not in (0, 1):

            return jsonify({
                "error": "Sensor values must be 0 or 1"
            }), 400

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid sensor values"
        }), 400

    # ======================================
    # ALARM CONDITION
    # ======================================

    alarm = 1 if vibration == 1 else 0

    # ======================================
    # ML MODEL
    # ======================================

    ml_prediction = predict_tampering(
        vibration,
        door
    )

    # ======================================
    # FINAL DETECTION RULE
    # ======================================

    # Tampering is detected only when vibration = 1.
    # Door opening alone does not trigger tampering.

    tampering_detected = (vibration == 1)

    if vibration == 1 and door == 1:

        detection_type = "Vibration and door detected"

    elif vibration == 1:

        detection_type = "Vibration detected - Door closed"

    elif door == 1:

        detection_type = "Door opened - No tampering"

    else:

        detection_type = "No suspicious activity"

    # ======================================
    # INDIAN DATE AND TIME
    # ======================================

    current_time = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%d-%m-%Y %I:%M:%S %p")

    # ======================================
    # SENSOR HISTORY
    # ======================================

    record = {
        "timestamp": current_time,
        "time": current_time,
        "vibration": vibration,
        "door": door,
        "alarm": alarm,
        "prediction": ml_prediction,
        "ml_prediction": ml_prediction
    }

    with history_lock:

        history.append(record)

        history_snapshot = list(history)

    # ======================================
    # LATEST SENSOR DATA
    # ======================================

    current_status = (
        "TAMPERING DETECTED"
        if tampering_detected
        else "ATM NORMAL"
    )

    current_data = {
        **record,
        "status": current_status,
        "detection_type": detection_type
    }

    with latest_lock:

        latest_data.clear()
        latest_data.update(current_data)

    # ======================================
    # DASHBOARD ALERT MEMORY
    # ======================================

    # Keep the warning visible for 5 seconds
    # after the most recent vibration detection.

    if tampering_detected:

        with dashboard_alert_lock:

            dashboard_alert_until = time.monotonic() + 5

            last_tampering_event = {
                "timestamp": current_time,
                "detection_type": detection_type,
                "vibration": vibration,
                "door": door
            }

    # ======================================
    # ALERT CONTROL
    # ======================================

    with alert_lock:

        should_send_alert = (
            tampering_detected
            and not alert_is_active
        )

        if should_send_alert:

            alert_is_active = True

        elif not tampering_detected:

            alert_is_active = False

    # ======================================
    # SEND EMAIL AND SMS
    # ======================================

    alert_id = None

    if should_send_alert:

        alert_id = (
            "ATM-" +
            uuid.uuid4().hex[:8].upper()
        )

        print("\nTAMPERING DETECTED!")
        print("Alert ID:", alert_id)
        print("Time:", current_time)
        print("Detection:", detection_type)
        print("ML Prediction:", ml_prediction)

        recent_history = history_snapshot[-3:]

        threading.Thread(
            target=send_notifications,
            args=(
                alert_id,
                current_time,
                vibration,
                door,
                alarm,
                ml_prediction,
                detection_type,
                recent_history
            ),
            daemon=True
        ).start()

    else:

        print(
            "Vibration:", vibration,
            "| Door:", door,
            "| Alarm:", alarm,
            "| Status:", current_status,
            "| ML:", ml_prediction
        )

    return jsonify({

        "success": True,
        "vibration": vibration,
        "door": door,
        "alarm": alarm,
        "prediction": ml_prediction,
        "ml_prediction": ml_prediction,
        "timestamp": current_time,
        "status": current_status,
        "detection_type": detection_type,
        "alert_triggered": should_send_alert,
        "alert_id": alert_id

    }), 200


# ==========================================
# LATEST SENSOR DATA FOR DASHBOARD
# ==========================================

@app.route("/latest", methods=["GET"])
def get_latest():

    with latest_lock:
        response_data = dict(latest_data)

    with dashboard_alert_lock:

        alert_active = (
            time.monotonic() < dashboard_alert_until
        )

        event_data = dict(last_tampering_event)

    response_data["tampering_alert_active"] = alert_active

    response_data["last_tampering_event"] = event_data

    return jsonify(response_data)


# ==========================================
# SENSOR HISTORY
# ==========================================

@app.route("/history", methods=["GET"])
def get_history():

    with history_lock:

        records = list(history)

    return jsonify({
        "total_records": len(records),
        "history": records
    })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    print("Starting ATM Security Server...")
    print("Server: http://0.0.0.0:8000")
    print("Waiting for ESP32 sensor data...\n")

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
        threaded=True
    )