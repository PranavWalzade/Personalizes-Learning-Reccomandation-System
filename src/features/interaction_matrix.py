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
# LOAD PERFORMANCE DATA
# ============================================================

def load_performance():

    file = (
        PROCESSED_DIR /
        "student_course_performance.csv"
    )

    if not file.exists():
        raise FileNotFoundError(
            f"File not found:\n{file}"
        )

    df = pd.read_csv(file)

    print(
        f"Loaded performance data: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# CLEAN DATA
# ============================================================

def clean_data(df):

    df = df.copy()

    # --------------------------------------------------------
    # Student ID
    # --------------------------------------------------------

    df["id_student"] = pd.to_numeric(
        df["id_student"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    df["average_score"] = pd.to_numeric(
        df["average_score"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Pass rate
    # --------------------------------------------------------

    df["pass_rate"] = pd.to_numeric(
        df["pass_rate"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "id_student",
            "course_id"
        ]
    )

    # --------------------------------------------------------
    # Clip values
    # --------------------------------------------------------

    df["average_score"] = (
        df["average_score"]
        .clip(0, 100)
    )

    df["pass_rate"] = (
        df["pass_rate"]
        .clip(0, 1)
    )

    return df


# ============================================================
# CREATE INTERACTION SCORE
# ============================================================

def create_interaction_score(df):

    df = df.copy()

    # --------------------------------------------------------
    # Normalize academic score
    # --------------------------------------------------------

    score = (
        df["average_score"] / 100
    ).clip(0, 1)

    # --------------------------------------------------------
    # Weighted interaction score
    #
    # Academic performance = strongest signal
    # Pass rate = second signal
    # Assessment activity = supporting signal
    # --------------------------------------------------------

    assessments = pd.to_numeric(
        df["assessments_completed"],
        errors="coerce"
    ).fillna(0)

    max_assessments = max(
        assessments.max(),
        1
    )

    assessment_activity = (
        assessments /
        max_assessments
    ).clip(0, 1)

    df["interaction_score"] = (
        0.60 * score
        + 0.25 * df["pass_rate"]
        + 0.15 * assessment_activity
    )

    df["interaction_score"] = (
        df["interaction_score"]
        .clip(0, 1)
    )

    return df


# ============================================================
# CREATE IMPLICIT INTERACTION
# ============================================================

def create_implicit_interaction(df):

    df = df.copy()

    # --------------------------------------------------------
    # Interaction exists if student attempted the course.
    # --------------------------------------------------------

    df["interaction"] = 1

    return df


# ============================================================
# CREATE USER AND ITEM INDICES
# ============================================================

def create_indices(df):

    df = df.copy()

    students = sorted(
        df["id_student"]
        .unique()
    )

    courses = sorted(
        df["course_id"]
        .astype(str)
        .unique()
    )

    student_to_index = {
        student: index
        for index, student in enumerate(students)
    }

    course_to_index = {
        course: index
        for index, course in enumerate(courses)
    }

    df["user_index"] = (
        df["id_student"]
        .map(student_to_index)
    )

    df["item_index"] = (
        df["course_id"]
        .astype(str)
        .map(course_to_index)
    )

    # --------------------------------------------------------
    # Save mappings
    # --------------------------------------------------------

    student_mapping = pd.DataFrame({
        "user_index": range(len(students)),
        "id_student": students
    })

    course_mapping = pd.DataFrame({
        "item_index": range(len(courses)),
        "course_id": courses
    })

    student_mapping.to_csv(
        PROCESSED_DIR /
        "student_index_mapping.csv",
        index=False
    )

    course_mapping.to_csv(
        PROCESSED_DIR /
        "oulad_course_index_mapping.csv",
        index=False
    )

    return df


# ============================================================
# CREATE INTERACTION TABLE
# ============================================================

def create_interaction_table(df):

    interaction = df[
        [
            "id_student",
            "course_id",
            "user_index",
            "item_index",
            "average_score",
            "pass_rate",
            "assessments_completed",
            "interaction_score",
            "interaction",
        ]
    ].copy()

    interaction = interaction.sort_values(
        [
            "user_index",
            "item_index"
        ]
    )

    interaction = (
        interaction
        .drop_duplicates(
            subset=[
                "id_student",
                "course_id"
            ]
        )
        .reset_index(drop=True)
    )

    return interaction


# ============================================================
# CREATE MATRIX
# ============================================================

def create_matrix(interaction):

    print("\nCreating student × course matrix...")

    matrix = interaction.pivot(
        index="user_index",
        columns="item_index",
        values="interaction_score"
    )

    matrix = matrix.fillna(0)

    return matrix


# ============================================================
# SPARSITY
# ============================================================

def calculate_statistics(matrix):

    total = (
        matrix.shape[0] *
        matrix.shape[1]
    )

    non_zero = int(
        (matrix.values > 0).sum()
    )

    sparsity = (
        1 -
        non_zero / total
    )

    statistics = {
        "students": matrix.shape[0],
        "courses": matrix.shape[1],
        "total_possible_interactions": total,
        "actual_interactions": non_zero,
        "sparsity": sparsity,
        "density": 1 - sparsity,
    }

    return statistics


# ============================================================
# SAVE
# ============================================================

def save_outputs(
    interaction,
    matrix
):

    interaction_file = (
        PROCESSED_DIR /
        "student_course_interactions.csv"
    )

    matrix_file = (
        PROCESSED_DIR /
        "student_course_matrix.csv"
    )

    interaction.to_csv(
        interaction_file,
        index=False
    )

    matrix.to_csv(
        matrix_file
    )

    print(
        "\nSaved interaction table:"
    )

    print(interaction_file)

    print(
        "\nSaved interaction matrix:"
    )

    print(matrix_file)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.3 "
        "STUDENT × COURSE INTERACTION MATRIX"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_performance()

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    print("\nCleaning data...")

    df = clean_data(df)

    # --------------------------------------------------------
    # Interaction score
    # --------------------------------------------------------

    print(
        "Creating interaction scores..."
    )

    df = create_interaction_score(df)

    # --------------------------------------------------------
    # Implicit interaction
    # --------------------------------------------------------

    df = create_implicit_interaction(df)

    # --------------------------------------------------------
    # Indices
    # --------------------------------------------------------

    print(
        "Creating student/course indices..."
    )

    df = create_indices(df)

    # --------------------------------------------------------
    # Interaction table
    # --------------------------------------------------------

    interaction = create_interaction_table(
        df
    )

    # --------------------------------------------------------
    # Matrix
    # --------------------------------------------------------

    matrix = create_matrix(
        interaction
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    statistics = calculate_statistics(
        matrix
    )

    print("\n" + "-" * 70)
    print("MATRIX STATISTICS")
    print("-" * 70)

    for key, value in statistics.items():

        if key in [
            "sparsity",
            "density"
        ]:

            print(
                f"{key:<30}: "
                f"{value:.4f}"
            )

        else:

            print(
                f"{key:<30}: "
                f"{value:,}"
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_outputs(
        interaction,
        matrix
    )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print("\nInteraction table preview:")

    print(
        interaction.head(10)
        .to_string(index=False)
    )

    print("\nMatrix preview:")

    print(
        matrix.iloc[:5, :10]
        .to_string()
    )

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.3 COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()