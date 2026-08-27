from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
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


def main() -> None:
    validation = pd.read_csv(
        DATA_DIR / "validation.csv"
    )

    model = joblib.load(
        MODEL_DIR / "fraud_model.joblib"
    )

    scaler = joblib.load(
        MODEL_DIR / "scaler.joblib"
    )

    X = validation[FEATURES]
    y = validation[TARGET]

    X_scaled = scaler.transform(X)

    probabilities = model.predict_proba(X_scaled)[:, 1]

    results = []

    for threshold in [x / 100 for x in range(10, 91, 5)]:
        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y,
            predictions,
            zero_division=0,
        )

        results.append(
            {
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    results_df = pd.DataFrame(results)

    print("\nThreshold Analysis")
    print("==================")

    print(
        results_df.to_string(
            index=False,
            formatters={
                "threshold": "{:.2f}".format,
                "precision": "{:.4f}".format,
                "recall": "{:.4f}".format,
                "f1": "{:.4f}".format,
            },
        )
    )

    best = results_df.loc[
        results_df["f1"].idxmax()
    ]

    print("\nBest F1 Threshold")
    print("=================")

    print(
        f"Threshold: {best['threshold']:.2f}"
    )

    print(
        f"Precision: {best['precision']:.4f}"
    )

    print(
        f"Recall: {best['recall']:.4f}"
    )

    print(
        f"F1: {best['f1']:.4f}"
    )


if __name__ == "__main__":
    main()