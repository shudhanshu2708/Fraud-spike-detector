from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "data" / "models"

MODEL_PATH = MODEL_DIR / "fraud_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"

FEATURE_NAMES = [
    "amount",
    "transactions_1m",
    "transactions_5m",
    "amount_5m",
    "new_device",
    "new_ip",
]


class FraudModel:
    def __init__(self) -> None:
        self.model = None
        self.scaler = None
        self.safe_threshold = 0.30
        self.block_threshold = 0.70

    def load(self) -> None:
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

    def predict_probability(
        self,
        amount: float,
        transactions_1m: int,
        transactions_5m: int,
        amount_5m: float,
        new_device: bool,
        new_ip: bool,
    ) -> float:
        if self.model is None or self.scaler is None:
            raise RuntimeError("Fraud model is not loaded")

        features = pd.DataFrame(
            [
                [
                    amount,
                    transactions_1m,
                    transactions_5m,
                    amount_5m,
                    int(new_device),
                    int(new_ip),
                ]
            ],
            columns=FEATURE_NAMES,
        )

        features_scaled = self.scaler.transform(features)

        probability = self.model.predict_proba(
            features_scaled
        )[0, 1]

        return round(float(probability), 4)

    def decide(self, probability: float) -> str:
        if probability >= self.block_threshold:
            return "BLOCK"

        if probability >= self.safe_threshold:
            return "REVIEW"

        return "SAFE"


fraud_model = FraudModel()