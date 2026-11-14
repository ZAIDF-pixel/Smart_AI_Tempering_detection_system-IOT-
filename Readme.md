# Smart AI Tampering Detection System (IoT)

A real-time ATM security monitoring system that detects tampering using vibration and door sensor inputs, classifies the event using a machine learning model, and raises alerts through email and SMS notifications.

This project combines:
- IoT sensor data collection
- A decision-tree based tampering detection system
- A Flask API for receiving and processing sensor values
- A Streamlit dashboard for live monitoring
- Automated email and SMS alerting

## Overview

The system is designed for an ATM prototype environment where tampering is inferred from abnormal sensor behavior. It continuously monitors:
- Vibration sensor
- ATM door status
- Alarm condition

When vibration is detected, the server evaluates the current readings with a trained ML model and triggers a tampering alert. The alert remains active for a short period and is exposed through the dashboard for live monitoring.

## Features

- Real-time sensor ingestion through a Flask API
- Machine-learning-based tampering detection using a decision tree
- Email notification support using Gmail SMTP
- SMS notification support using Twilio
- Real-time Streamlit dashboard
- Sensor history retrieval API
- Model retraining pipeline using dataset updates

## Repository Structure

```text
.
├── atm_database_generator.py     # Generates and stores CSV-based sensor logs
├── atm_dataset_final.csv         # Final labeled dataset used for model training
├── atm_decision_tree_model.pkl   # Trained ML model
├── dashboard.py                  # Streamlit dashboard for live monitoring
├── ml_model.py                   # Loads the model and runs predictions
├── pyconnect/                    # Additional project-related connector files
├── receiver.py                   # Flask server for sensor ingestion and alert logic
├── train_model.py                # Trains and saves the ML model
├── README.md                    # Project documentation
└── .env                         # Local environment variables (not committed)
```

## System Workflow

1. An IoT device or ESP32 sends sensor data to the Flask server.
2. `receiver.py` validates the incoming JSON payload.
3. The system calculates the alarm state and runs prediction logic.
4. If vibration is detected, the system marks the event as tampering.
5. Email and SMS alerts are sent using configured credentials.
6. The Streamlit dashboard fetches live and historical data from the server.

## Tech Stack

- Python
- Flask
- Pandas
- Scikit-learn
- Joblib
- Streamlit
- Plotly
- Requests
- Twilio
- Gmail SMTP

## Prerequisites

- Python 3.9+
- pip
- Access to Gmail SMTP credentials
- Twilio account credentials (optional if SMS alerts are not needed)

## Installation

Clone the repository:

```bash
git clone https://github.com/ZAIDF-pixel/Smart_AI_Tempering_detection_system-IOT-.git
cd Smart_AI_Tempering_detection_system-IOT-
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

Install dependencies:

```bash
pip install flask python-dotenv twilio pandas scikit-learn joblib streamlit plotly requests streamlit-autorefresh
```

## Configuration

Create a `.env` file in the project root:

```env
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=target_email@example.com
GMAIL_APP_PASSWORD=your_gmail_app_password

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1987654321

ATM_LOCATION=ATM Prototype - Laboratory
```

If these values are missing, the system will still run, but email and SMS notifications will be skipped.

## Training the Model

Run:

```bash
python train_model.py
```

This script:
- Loads `atm_dataset_final.csv`
- Extracts the relevant sensor features
- Trains a Decision Tree classifier
- Prints evaluation metrics
- Saves the trained model as `atm_decision_tree_model.pkl`

## Starting the Server

Run:

```bash
python receiver.py
```

The Flask server starts on:

```text
http://0.0.0.0:8000
```

## API Endpoints

### GET `/`

Returns the server status.

### POST `/sensor`

Receives sensor data in JSON format.

Example payload:

```json
{
  "vibration": 1,
  "door": 0
}
```

### GET `/latest`

Returns the newest sensor reading and the current alert state.

### GET `/history`

Returns recent sensor records from the server memory.

## Launching the Dashboard

Start the UI using:

```bash
streamlit run dashboard.py
```

The dashboard shows:
- Live sensor status
- Current tampering status
- ML prediction result
- Recent event history
- Trend-based charts for sensor readings

## Example Workflow

1. Train the model once using `train_model.py`
2. Start the Flask receiver with `python receiver.py`
3. Send sensor data to `/sensor`
4. View the result on the Streamlit dashboard
5. Receive email/SMS alerts if a tampering event is detected

## Detection Logic

The project considers vibration as the primary tampering indicator. The logic is:

- Vibration = 1 → potential tampering
- Door status is analyzed alongside vibration
- Door open without vibration is treated as normal activity
- Tampering alerts are triggered when a vibration event occurs and the alert is not already active

## Notes

- This is intended for prototype or demonstration use in IoT and security monitoring applications.
- The project is optimized for a small ATM prototype environment rather than large-scale production deployment.
- Model performance depends on dataset quality and sensor calibration.

## License

This repository does not currently include a visible license file. Please check with the repository owner before using it for commercial or public distribution.

## Contributing

Contributions are welcome. If you want to improve the detection model, add more sensors, or enhance the alerting system, feel free to fork the repository and open a pull request.

## Contact

For questions or collaboration, please use the repository’s GitHub Issues page or contact the project owner through the repository profile.
