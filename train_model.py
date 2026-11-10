import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "atm_dataset_final.csv"
MODEL_PATH = BASE_DIR / "atm_decision_tree_model.pkl"

# Load dataset
df = pd.read_csv(DATASET_PATH)

# Check required columns
required = ["vibration", "door"]

for column in required:
    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

# Input features
X = df[["vibration", "door"]].copy()

# Alarm follows vibration only
X["alarm"] = X["vibration"]

# Target: vibration = 1 means tampering
y = (df["vibration"] == 1).astype(int)

if y.nunique() < 2:
    raise ValueError(
        "Dataset must contain both normal and tampering records."
    )

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Create model
model = DecisionTreeClassifier(
    criterion="entropy",
    max_depth=5,
    random_state=42
)

# Train
model.fit(X_train, y_train)

# Predict
predictions = model.predict(X_test)

# Evaluate
print("\nMODEL ACCURACY")
print(accuracy_score(y_test, predictions) * 100, "%")

print("\nCLASSIFICATION REPORT")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

print("\nCONFUSION MATRIX")
print(confusion_matrix(y_test, predictions))

# Save model
joblib.dump(model, MODEL_PATH)

print("\nModel saved successfully!")
print(MODEL_PATH)