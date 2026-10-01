import sys
from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    interaction_file = (
        PROCESSED_DIR /
        "oulad_ml_interactions.csv"
    )

    if not interaction_file.exists():

        raise FileNotFoundError(
            f"File not found:\n{interaction_file}"
        )

    df = pd.read_csv(
        interaction_file
    )

    print(
        f"Interactions loaded: {len(df):,}"
    )

    return df


# ============================================================
# CALCULATE COURSE POPULARITY
# ============================================================

def calculate_popularity(df):

    print(
        "\nCalculating course popularity..."
    )

    popularity = (
        df.groupby("course_id")
        .agg(
            unique_students=(
                "id_student",
                "nunique"
            ),

            total_interactions=(
                "interaction",
                "sum"
            ),

            average_interaction_score=(
                "interaction_score",
                "mean"
            ),

            total_interaction_score=(
                "interaction_score",
                "sum"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Number of students interacting with course
    # --------------------------------------------------------

    popularity["student_reach"] = (
        popularity["unique_students"]
        / popularity["unique_students"].max()
    )

    # --------------------------------------------------------
    # Normalize interaction score
    # --------------------------------------------------------

    maximum = (
        popularity[
            "total_interaction_score"
        ].max()
    )

    if maximum > 0:

        popularity["interaction_strength"] = (
            popularity[
                "total_interaction_score"
            ] / maximum
        )

    else:

        popularity["interaction_strength"] = 0

    # --------------------------------------------------------
    # Final popularity score
    # --------------------------------------------------------

    popularity["popularity_score"] = (
        0.60 *
        popularity["student_reach"]
        +
        0.40 *
        popularity["interaction_strength"]
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    popularity["popularity_rank"] = (
        popularity[
            "popularity_score"
        ]
        .rank(
            ascending=False,
            method="first"
        )
        .astype(int)
    )

    popularity = (
        popularity
        .sort_values(
            "popularity_rank"
        )
        .reset_index(drop=True)
    )

    return popularity


# ============================================================
# CREATE TOP POPULAR COURSES
# ============================================================

def create_top_courses(
    popularity,
    top_k=10
):

    return (
        popularity
        .head(top_k)
        .copy()
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    popularity,
    top_courses
):

    popularity_file = (
        PROCESSED_DIR /
        "oulad_course_popularity.csv"
    )

    top_file = (
        PROCESSED_DIR /
        "oulad_top_popular_courses.csv"
    )

    popularity.to_csv(
        popularity_file,
        index=False
    )

    top_courses.to_csv(
        top_file,
        index=False
    )

    print(
        f"\nSaved:\n"
        f"{popularity_file}\n"
        f"{top_file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)

    print(
        "PHASE 4 — STEP 4.1 "
        "POPULARITY BASELINE"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # Popularity
    # --------------------------------------------------------

    popularity = calculate_popularity(
        df
    )

    # --------------------------------------------------------
    # Top courses
    # --------------------------------------------------------

    top_courses = create_top_courses(
        popularity,
        top_k=10
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        popularity,
        top_courses
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        "\nTOP 10 POPULAR OULAD COURSES"
    )

    print(
        top_courses.to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)

    print(
        "PHASE 4 — STEP 4.1 COMPLETE"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()