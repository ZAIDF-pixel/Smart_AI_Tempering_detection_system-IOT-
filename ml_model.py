import joblib
import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "atm_decision_tree_model.pkl"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Model not found. Run train_model.py first."
    )

model = joblib.load(MODEL_PATH)

print("Trained ML model loaded successfully!")


def predict_tampering(vibration, door):

    alarm = vibration

    input_data = pd.DataFrame(
        [[vibration, door, alarm]],
        columns=["vibration", "door", "alarm"]
    )

    prediction = int(model.predict(input_data)[0])

    return prediction