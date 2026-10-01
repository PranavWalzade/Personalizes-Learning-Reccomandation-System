import pandas as pd

from config import (
    OULAD_FILES,
    ENGINEERING_COURSES_FILE,
)


def validate_dataframe(name, df):

    print("\n" + "=" * 70)
    print(f"DATASET: {name}")
    print("=" * 70)

    print(
        f"Rows    : {df.shape[0]:,}"
    )

    print(
        f"Columns : {df.shape[1]:,}"
    )

    print("\nColumns:")

    for column in df.columns:

        print(f"  - {column}")

    print("\nMissing values:")

    missing = (
        df.isnull()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    missing = missing[
        missing > 0
    ]

    if missing.empty:

        print("  No missing values")

    else:

        print(
            missing.to_string()
        )

    duplicates = (
        df.duplicated().sum()
    )

    print(
        f"\nDuplicate rows: "
        f"{duplicates:,}"
    )

    print("\nData types:")

    print(
        df.dtypes.to_string()
    )


def main():

    print("=" * 70)

    print(
        "PERSONALIZED LEARNING "
        "RECOMMENDATION SYSTEM"
    )

    print(
        "PHASE 1 - DATA VALIDATION"
    )

    print("=" * 70)

    for name, path in OULAD_FILES.items():

        df = pd.read_csv(path)

        validate_dataframe(
            name,
            df
        )

    engineering = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    validate_dataframe(
        "engineering_courses",
        engineering
    )

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    main()