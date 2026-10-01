import pandas as pd

from config import (
    OULAD_FILES,
    ENGINEERING_COURSES_FILE,
)


def load_oulad():

    data = {}

    print("\nLoading OULAD datasets...\n")

    for name, path in OULAD_FILES.items():

        print(f"Loading: {name}.csv")

        df = pd.read_csv(path)

        data[name] = df

        print(
            f"    Shape: "
            f"{df.shape}"
        )

    return data


def load_engineering_courses():

    print(
        "\nLoading Engineering "
        "Course Catalog..."
    )

    df = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    print(
        f"    Shape: {df.shape}"
    )

    return df


def main():

    print("=" * 70)

    print(
        "PERSONALIZED LEARNING "
        "RECOMMENDATION SYSTEM"
    )

    print(
        "PHASE 1 - DATA LOADING"
    )

    print("=" * 70)

    oulad = load_oulad()

    engineering = (
        load_engineering_courses()
    )

    print("\n" + "=" * 70)
    print("OULAD SUMMARY")
    print("=" * 70)

    for name, df in oulad.items():

        print(
            f"{name:<25} "
            f"rows={len(df):,}, "
            f"columns={len(df.columns)}"
        )

    print("\n" + "=" * 70)
    print("ENGINEERING COURSE SUMMARY")
    print("=" * 70)

    print(
        f"Total courses: "
        f"{len(engineering):,}"
    )

    print(
        f"Total columns: "
        f"{len(engineering.columns)}"
    )

    print("\nColumns:")

    for column in engineering.columns:

        print(f"  - {column}")

    preview_columns = [
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "difficulty",
        "credits",
    ]

    available_columns = [
        column
        for column in preview_columns
        if column in engineering.columns
    ]

    print("\nFirst 5 engineering courses:")

    print(
        engineering[
            available_columns
        ].head().to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("DATA LOADING SUCCESSFUL")
    print("=" * 70)


if __name__ == "__main__":

    main()