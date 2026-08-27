from pathlib import Path

import joblib
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path(__file__).parent
MODEL_DIR = DATA_DIR / "models"

FEATURES = [
    "amount",
    "transactions_1m",
    "transactions_5m",
    "amount_5m",
    "new_device",
    "new_ip",
]

TARGET = "is_fraud"


def main() -> None:
    train = pd.read_csv(DATA_DIR / "train.csv")
    validation = pd.read_csv(DATA_DIR / "validation.csv")

    X_train = train[FEATURES]
    y_train = train[TARGET]

    X_validation = validation[FEATURES]
    y_validation = validation[TARGET]

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_validation_scaled = scaler.transform(X_validation)

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        X_train_scaled,
        y_train,
    )

    probabilities = model.predict_proba(
        X_validation_scaled
    )[:, 1]

    predictions = (probabilities >= 0.50).astype(int)

    print("\nValidation Metrics")
    print("==================")

    print(
        f"ROC-AUC: "
        f"{roc_auc_score(y_validation, probabilities):.4f}"
    )

    print(
        f"PR-AUC: "
        f"{average_precision_score(y_validation, probabilities):.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_validation, predictions):.4f}"
    )

    print(
        f"Recall: "
        f"{recall_score(y_validation, predictions):.4f}"
    )

    print("\nClassification Report")
    print("=====================")

    print(
        classification_report(
            y_validation,
            predictions,
            digits=4,
        )
    )

    MODEL_DIR.mkdir(exist_ok=True)

    joblib.dump(
        model,
        MODEL_DIR / "fraud_model.joblib",
    )

    joblib.dump(
        scaler,
        MODEL_DIR / "scaler.joblib",
    )

    print("\nSaved:")
    print(MODEL_DIR / "fraud_model.joblib")
    print(MODEL_DIR / "scaler.joblib")


if __name__ == "__main__":
    main()