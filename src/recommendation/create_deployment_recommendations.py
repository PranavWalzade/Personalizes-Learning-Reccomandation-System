import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import RESULTS_DIR


# ============================================================
# INPUT / OUTPUT
# ============================================================

INPUT_FILE = (
    RESULTS_DIR /
    "explainable_engineering_recommendations.csv"
)

OUTPUT_FILE = (
    RESULTS_DIR /
    "deployment_recommendations.csv"
)


# ============================================================
# SETTINGS
# ============================================================

TOP_N = 10


# ============================================================
# MAIN FUNCTION
# ============================================================

def create_deployment_file():

    print("=" * 70)
    print("STEP 4.15 - CREATE DEPLOYMENT RECOMMENDATIONS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\nLoading explainable recommendations...")

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"File not found:\n{INPUT_FILE}"
        )

    data = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Total recommendation records: {len(data)}"
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "id_student",
        "recommendation_rank",
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "difficulty",
        "credits",
        "course_level",
        "hybrid_score",
        "recommendation_reasons",
        "why_recommended"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    data = data.sort_values(
        [
            "id_student",
            "hybrid_score"
        ],
        ascending=[
            True,
            False
        ]
    )

    # --------------------------------------------------------
    # Keep TOP N for every student
    # --------------------------------------------------------

    deployment_data = (
        data
        .groupby(
            "id_student",
            group_keys=False
        )
        .head(TOP_N)
        .copy()
    )

    # --------------------------------------------------------
    # Recalculate rank
    # --------------------------------------------------------

    deployment_data[
        "recommendation_rank"
    ] = (
        deployment_data
        .groupby("id_student")
        .cumcount()
        + 1
    )

    # --------------------------------------------------------
    # Select columns
    # --------------------------------------------------------

    deployment_data = deployment_data[
        required_columns
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    deployment_data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    student_count = (
        deployment_data[
            "id_student"
        ]
        .nunique()
    )

    course_count = (
        deployment_data[
            "course_id"
        ]
        .nunique()
    )

    print("\n" + "=" * 70)
    print("DEPLOYMENT FILE CREATED")
    print("=" * 70)

    print(
        f"Students: {student_count}"
    )

    print(
        f"Courses appearing in recommendations: "
        f"{course_count}"
    )

    print(
        f"Recommendation records: "
        f"{len(deployment_data)}"
    )

    print(
        f"Recommendations per student: "
        f"up to {TOP_N}"
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # Sample
    # --------------------------------------------------------

    if not deployment_data.empty:

        sample_student = (
            deployment_data[
                "id_student"
            ].iloc[0]
        )

        sample = deployment_data[
            deployment_data[
                "id_student"
            ]
            == sample_student
        ]

        print(
            "\n" + "=" * 70
        )

        print(
            "SAMPLE DEPLOYMENT RECOMMENDATIONS"
        )

        print(
            "=" * 70
        )

        for _, row in sample.iterrows():

            print(
                f"\n{int(row['recommendation_rank'])}. "
                f"{row['course_name']}"
            )

            print(
                f"   Branch: {row['branch']}"
            )

            print(
                f"   Score: "
                f"{float(row['hybrid_score']):.4f}"
            )

            print(
                f"   Why: "
                f"{row['why_recommended']}"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "STEP 4.15 COMPLETED"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    create_deployment_file()