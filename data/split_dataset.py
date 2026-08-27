from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


SEED = 42

DATA_DIR = Path(__file__).parent

INPUT_FILE = DATA_DIR / "transactions.csv"

TRAIN_FILE = DATA_DIR / "train.csv"
VALIDATION_FILE = DATA_DIR / "validation.csv"
TEST_FILE = DATA_DIR / "test.csv"


def main() -> None:
    dataset = pd.read_csv(INPUT_FILE)

    train, temp = train_test_split(
        dataset,
        test_size=0.30,
        random_state=SEED,
        stratify=dataset["is_fraud"],
    )

    validation, test = train_test_split(
        temp,
        test_size=0.50,
        random_state=SEED,
        stratify=temp["is_fraud"],
    )

    train.to_csv(TRAIN_FILE, index=False)
    validation.to_csv(VALIDATION_FILE, index=False)
    test.to_csv(TEST_FILE, index=False)

    print(f"Total:      {len(dataset):,}")
    print(f"Train:      {len(train):,}")
    print(f"Validation: {len(validation):,}")
    print(f"Test:       {len(test):,}")

    print("\nFraud distribution:")

    for name, data in [
        ("Train", train),
        ("Validation", validation),
        ("Test", test),
    ]:
        fraud_rate = data["is_fraud"].mean()

        print(
            f"{name}: "
            f"{fraud_rate:.2%} fraud"
        )


if __name__ == "__main__":
    main()