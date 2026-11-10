import streamlit as st
import pandas as pd
import requests
import plotly.express as px

from streamlit_autorefresh import st_autorefresh


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="ATM Security Dashboard",
    page_icon="🔐",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# Refresh dashboard every second
st_autorefresh(
    interval=1000,
    key="refresh"
)


# ==========================================
# DASHBOARD TITLE
# ==========================================

st.title("🔐 AI-Based ATM Tampering Detection")

st.caption(
    "Live ESP32 Monitoring | "
    "Vibration-Based Tampering Detection"
)


# ==========================================
# FETCH LATEST DATA
# ==========================================

try:

    response = requests.get(
        API_URL + "/latest",
        timeout=3
    )

    response.raise_for_status()

    latest = response.json()

    if not latest or "vibration" not in latest:

        st.info("Waiting for ESP32 sensor data...")
        st.stop()

    # ======================================
    # CONVERT SENSOR VALUES
    # ======================================

    vibration = int(latest.get("vibration", 0))
    door = int(latest.get("door", 0))
    alarm = int(latest.get("alarm", 0))

    # ======================================
    # LIVE SENSOR STATUS
    # ======================================

    st.subheader("Live Sensor Status")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Vibration",
        "DETECTED" if vibration == 1 else "NORMAL"
    )

    col2.metric(
        "ATM Door",
        "OPEN" if door == 1 else "CLOSED"
    )

    col3.metric(
        "Alarm",
        "ON" if alarm == 1 else "OFF"
    )

    # ======================================
    # SECURITY STATUS
    # ======================================

    st.subheader("Security Status")

    # Read the five-second alert memory
    tampering_alert_active = latest.get(
        "tampering_alert_active",
        vibration == 1
    )

    last_event = latest.get(
        "last_tampering_event",
        {}
    )

    if tampering_alert_active:

        st.error("🚨 TAMPERING DETECTED!")

        st.write(
            "**Detection Type:**",
            last_event.get(
                "detection_type",
                latest.get("detection_type", "Vibration detected")
            )
        )

        st.write(
            "**Event Time:**",
            last_event.get(
                "timestamp",
                latest.get("timestamp", "Unknown")
            )
        )

        st.warning(
            "Recent tampering event detected. "
            "The warning remains visible for 5 seconds."
        )

    else:

        st.success("✅ NORMAL ATM ACTIVITY")

        if door == 1:

            st.write(
                "Door is open, but no vibration detected. "
                "No tampering alert."
            )

        else:

            st.write("No vibration detected.")

    # ======================================
    # MACHINE LEARNING PREDICTION
    # ======================================

    st.subheader("Machine Learning Prediction")

    ml_prediction = latest.get(
        "ml_prediction",
        latest.get("prediction", 0)
    )

    if int(ml_prediction) == 1:

        st.warning("ML Model: TAMPERING DETECTED")

    else:

        st.info("ML Model: NORMAL")

    # ======================================
    # TIME AND DETECTION INFORMATION
    # ======================================

    st.subheader("Detection Information")

    info1, info2 = st.columns(2)

    info1.write(
        "**Current Detection Type:**"
    )

    info1.write(
        latest.get("detection_type", "Unknown")
    )

    info2.write(
        "**Last Server Reading:**"
    )

    info2.write(
        latest.get("timestamp", "Unknown")
    )

    # ======================================
    # SENSOR HISTORY
    # ======================================

    history_response = requests.get(
        API_URL + "/history",
        timeout=3
    )

    history_response.raise_for_status()

    history_data = history_response.json()

    records = history_data.get("history", [])

    if records:

        df = pd.DataFrame(records).tail(30).copy()

        # Convert sensor columns into numeric values
        for column in ["vibration", "door", "alarm"]:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        st.subheader("Recent Sensor Readings")

        fig = px.line(
            df,
            x="timestamp",
            y=["vibration", "door", "alarm"],
            title="Live Sensor History",
            markers=True
        )

        fig.update_layout(
            height=350,
            xaxis_title="Time",
            yaxis_title="Sensor Value",
            yaxis=dict(
                tickmode="array",
                tickvals=[0, 1]
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ==================================
        # RECENT ACTIVITY
        # ==================================

        st.subheader("Recent Activity")

        st.dataframe(
            df.tail(10).iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No sensor history available.")

    # ======================================
    # FOOTER
    # ======================================

    st.divider()

    st.caption(
        "ATM Security Monitoring System | "
        "ESP32 + IoT + Machine Learning"
    )

except requests.exceptions.ConnectionError:

    st.error(
        "Cannot connect to Flask server. "
        "Make sure receiver.py is running."
    )

except requests.exceptions.Timeout:

    st.error(
        "Flask server response timed out. "
        "Please check the server."
    )

except requests.exceptions.RequestException as e:

    st.error(
        "API Request Error: " + str(e)
    )

except Exception as e:

    st.error(
        "Dashboard Error: " + str(e)
    )