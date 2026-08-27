from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
ROWS = 50_000

rng = np.random.default_rng(SEED)


def generate_normal(n: int) -> pd.DataFrame:
    amount = np.clip(
        rng.lognormal(mean=6.2, sigma=0.8, size=n),
        50,
        25_000,
    )

    transactions_1m = rng.poisson(0.35, n)
    transactions_5m = transactions_1m + rng.poisson(0.8, n)

    amount_5m = amount * rng.uniform(1.0, 4.0, n)

    new_device = rng.random(n) < 0.08
    new_ip = rng.random(n) < 0.05

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 0,
        }
    )


def generate_velocity_fraud(n: int) -> pd.DataFrame:
    amount = np.clip(
        rng.lognormal(mean=7.0, sigma=0.7, size=n),
        100,
        30_000,
    )

    transactions_1m = rng.integers(5, 15, n)
    transactions_5m = transactions_1m + rng.integers(5, 20, n)

    amount_5m = amount * rng.uniform(3.0, 10.0, n)

    new_device = rng.random(n) < 0.55
    new_ip = rng.random(n) < 0.45

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 1,
        }
    )


def generate_account_takeover(n: int) -> pd.DataFrame:
    amount = np.clip(
        rng.lognormal(mean=7.5, sigma=0.9, size=n),
        500,
        50_000,
    )

    transactions_1m = rng.poisson(1.5, n)
    transactions_5m = transactions_1m + rng.poisson(3, n)

    amount_5m = amount * rng.uniform(1.5, 5.0, n)

    # Account takeover often involves a new device/IP,
    # but not necessarily extreme velocity.
    new_device = rng.random(n) < 0.85
    new_ip = rng.random(n) < 0.75

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 1,
        }
    )


def generate_low_and_slow_fraud(n: int) -> pd.DataFrame:
    # Designed specifically so fraud is not synonymous
    # with high velocity.
    amount = np.clip(
        rng.lognormal(mean=6.8, sigma=0.8, size=n),
        100,
        20_000,
    )

    transactions_1m = rng.integers(0, 3, n)
    transactions_5m = transactions_1m + rng.integers(1, 5, n)

    amount_5m = amount * rng.uniform(1.0, 3.0, n)

    new_device = rng.random(n) < 0.35
    new_ip = rng.random(n) < 0.30

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 1,
        }
    )


def generate_legitimate_high_value(n: int) -> pd.DataFrame:
    # Important: high amount alone must NOT mean fraud.
    amount = np.clip(
        rng.lognormal(mean=9.0, sigma=0.5, size=n),
        5_000,
        100_000,
    )

    transactions_1m = rng.poisson(0.25, n)
    transactions_5m = transactions_1m + rng.poisson(0.7, n)

    amount_5m = amount * rng.uniform(1.0, 2.0, n)

    new_device = rng.random(n) < 0.12
    new_ip = rng.random(n) < 0.08

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 0,
        }
    )


def generate_legitimate_new_device(n: int) -> pd.DataFrame:
    amount = np.clip(
        rng.lognormal(mean=6.4, sigma=0.8, size=n),
        50,
        15_000,
    )

    transactions_1m = rng.poisson(0.4, n)
    transactions_5m = transactions_1m + rng.poisson(1.0, n)

    amount_5m = amount * rng.uniform(1.0, 3.0, n)

    new_device = rng.random(n) < 0.70
    new_ip = rng.random(n) < 0.40

    return pd.DataFrame(
        {
            "amount": amount,
            "transactions_1m": transactions_1m,
            "transactions_5m": transactions_5m,
            "amount_5m": amount_5m,
            "new_device": new_device.astype(int),
            "new_ip": new_ip.astype(int),
            "is_fraud": 0,
        }
    )


def main() -> None:
    fraud_count = int(ROWS * 0.25)
    normal_count = ROWS - fraud_count

    normal = generate_normal(int(normal_count * 0.65))
    high_value = generate_legitimate_high_value(int(normal_count * 0.20))
    new_device = generate_legitimate_new_device(
        normal_count
        - len(normal)
        - len(high_value)
    )

    velocity_fraud = generate_velocity_fraud(int(fraud_count * 0.40))
    takeover_fraud = generate_account_takeover(int(fraud_count * 0.30))
    low_slow_fraud = generate_low_and_slow_fraud(
        fraud_count
        - len(velocity_fraud)
        - len(takeover_fraud)
    )

    dataset = pd.concat(
        [
            normal,
            high_value,
            new_device,
            velocity_fraud,
            takeover_fraud,
            low_slow_fraud,
        ],
        ignore_index=True,
    )

    dataset = dataset.sample(
        frac=1,
        random_state=SEED,
    ).reset_index(drop=True)

    output_path = Path(__file__).parent / "transactions.csv"

    dataset.to_csv(
        output_path,
        index=False,
    )

    print(f"Generated: {len(dataset):,} transactions")
    print(f"Fraud: {dataset['is_fraud'].sum():,}")
    print(
        f"Fraud rate: "
        f"{dataset['is_fraud'].mean():.2%}"
    )
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()