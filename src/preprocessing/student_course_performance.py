import sys
from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = SRC_DIR.parent

sys.path.insert(0, str(SRC_DIR))

from config import (
    OULAD_FILES,
    PROCESSED_DIR,
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\nLoading OULAD data...")

    student_assessment = pd.read_csv(
        OULAD_FILES["studentAssessment"]
    )

    assessments = pd.read_csv(
        OULAD_FILES["assessments"]
    )

    students = pd.read_csv(
        OULAD_FILES["studentInfo"]
    )

    print("Data loaded successfully.")

    return (
        student_assessment,
        assessments,
        students,
    )


# ============================================================
# CLEAN DATA
# ============================================================

def clean_data(
    student_assessment,
    assessments,
    students,
):

    print("\nCleaning data...")

    student_assessment = (
        student_assessment
        .drop_duplicates()
        .copy()
    )

    assessments = (
        assessments
        .drop_duplicates()
        .copy()
    )

    students = (
        students
        .drop_duplicates()
        .copy()
    )

    # Convert score to numeric
    student_assessment["score"] = pd.to_numeric(
        student_assessment["score"],
        errors="coerce"
    )

    # Convert assessment date
    assessments["date"] = pd.to_numeric(
        assessments["date"],
        errors="coerce"
    )

    # Convert weight
    assessments["weight"] = pd.to_numeric(
        assessments["weight"],
        errors="coerce"
    )

    # Convert student ID
    student_assessment["id_student"] = pd.to_numeric(
        student_assessment["id_student"],
        errors="coerce"
    )

    students["id_student"] = pd.to_numeric(
        students["id_student"],
        errors="coerce"
    )

    # Remove records without score
    student_assessment = (
        student_assessment[
            student_assessment["score"].notna()
        ]
        .copy()
    )

    print(
        "Student assessment records:",
        f"{len(student_assessment):,}"
    )

    return (
        student_assessment,
        assessments,
        students,
    )


# ============================================================
# CREATE STUDENT-COURSE DATA
# ============================================================

def create_student_course_performance(
    student_assessment,
    assessments,
    students,
):

    print("\nCreating student-course performance...")

    # --------------------------------------------------------
    # Join studentAssessment with assessments
    # --------------------------------------------------------

    merged = student_assessment.merge(
        assessments[
            [
                "id_assessment",
                "code_module",
                "code_presentation",
                "assessment_type",
                "date",
                "weight",
            ]
        ],
        on="id_assessment",
        how="left"
    )

    # --------------------------------------------------------
    # Create course ID
    # --------------------------------------------------------

    merged["course_id"] = (
        merged["code_module"].astype(str)
        + "_"
        + merged["code_presentation"].astype(str)
    )

    # --------------------------------------------------------
    # Add pass/fail
    # --------------------------------------------------------

    merged["is_pass"] = (
        merged["score"] >= 40
    ).astype(int)

    # --------------------------------------------------------
    # Add weighted score
    # --------------------------------------------------------

    merged["weighted_score"] = (
        merged["score"]
        * merged["weight"]
        / 100
    )

    # --------------------------------------------------------
    # Aggregate by student + course
    # --------------------------------------------------------

    performance = (
        merged
        .groupby(
            [
                "id_student",
                "course_id",
                "code_module",
                "code_presentation",
            ]
        )
        .agg(
            average_score=("score", "mean"),
            maximum_score=("score", "max"),
            minimum_score=("score", "min"),
            score_std=("score", "std"),

            weighted_score=(
                "weighted_score",
                "sum"
            ),

            assessments_completed=(
                "id_assessment",
                "nunique"
            ),

            pass_rate=(
                "is_pass",
                "mean"
            ),

            average_weight=(
                "weight",
                "mean"
            ),

            assessment_count=(
                "id_assessment",
                "count"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Fill standard deviation
    # --------------------------------------------------------

    performance["score_std"] = (
        performance["score_std"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # Add student final result
    # --------------------------------------------------------

    student_result = (
        students[
            [
                "id_student",
                "final_result",
                "highest_education",
                "gender",
                "region",
                "age_band",
            ]
        ]
        .drop_duplicates(
            subset=["id_student"]
        )
    )

    performance = performance.merge(
        student_result,
        on="id_student",
        how="left"
    )

    # --------------------------------------------------------
    # Performance level
    # --------------------------------------------------------

    def performance_level(score):

        if score >= 80:
            return "Excellent"

        elif score >= 60:
            return "Good"

        elif score >= 40:
            return "Average"

        else:
            return "Weak"

    performance["performance_level"] = (
        performance["average_score"]
        .apply(performance_level)
    )

    # --------------------------------------------------------
    # Academic score
    # --------------------------------------------------------

    performance["academic_score"] = (
        0.60
        * (performance["average_score"] / 100).clip(0, 1)
        +
        0.20
        * performance["pass_rate"]
        +
        0.20
        * (performance["maximum_score"] / 100).clip(0, 1)
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    performance = performance.sort_values(
        [
            "id_student",
            "course_id"
        ]
    )

    print(
        "\nStudent-course records created:",
        f"{len(performance):,}"
    )

    print(
        "Unique students:",
        f"{performance['id_student'].nunique():,}"
    )

    print(
        "Unique courses:",
        f"{performance['course_id'].nunique():,}"
    )

    return performance


# ============================================================
# SAVE
# ============================================================

def save_data(performance):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        PROCESSED_DIR
        / "student_course_performance.csv"
    )

    performance.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved:",
        output_file
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("STEP 2.8 - STUDENT COURSE PERFORMANCE")
    print("=" * 70)

    (
        student_assessment,
        assessments,
        students,
    ) = load_data()

    (
        student_assessment,
        assessments,
        students,
    ) = clean_data(
        student_assessment,
        assessments,
        students,
    )

    performance = (
        create_student_course_performance(
            student_assessment,
            assessments,
            students,
        )
    )

    save_data(
        performance
    )

    print("\n" + "=" * 70)
    print("STEP 2.8 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()