from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)


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

THRESHOLD = 0.70


def main() -> None:
    test = pd.read_csv(
        DATA_DIR / "test.csv"
    )

    model = joblib.load(
        MODEL_DIR / "fraud_model.joblib"
    )

    scaler = joblib.load(
        MODEL_DIR / "scaler.joblib"
    )

    X_test = test[FEATURES]
    y_test = test[TARGET]

    X_test_scaled = scaler.transform(X_test)

    probabilities = model.predict_proba(
        X_test_scaled
    )[:, 1]

    predictions = (
        probabilities >= THRESHOLD
    ).astype(int)

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    print("\nFINAL TEST RESULTS")
    print("==================")

    print(f"Threshold: {THRESHOLD:.2f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"Precision:  {precision:.4f}")
    print(f"Recall:     {recall:.4f}")

    print("\nConfusion Matrix")
    print("================")

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        predictions,
    ).ravel()

    print(f"True Negatives:  {tn}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"True Positives:  {tp}")

    print("\nClassification Report")
    print("=====================")

    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
        )
    )


if __name__ == "__main__":
    main()