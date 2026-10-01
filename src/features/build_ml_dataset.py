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
# FILE PATHS
# ============================================================

STUDENT_FEATURES_FILE = (
    PROCESSED_DIR / "student_features.csv"
)

COURSE_FEATURES_FILE = (
    PROCESSED_DIR / "course_features.csv"
)

COMPATIBILITY_FILE = (
    PROCESSED_DIR /
    "student_engineering_compatibility.csv"
)

INTERACTION_FILE = (
    PROCESSED_DIR /
    "student_course_interactions.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_datasets():

    print("\nLoading datasets...")

    students = pd.read_csv(
        STUDENT_FEATURES_FILE
    )

    courses = pd.read_csv(
        COURSE_FEATURES_FILE
    )

    compatibility = pd.read_csv(
        COMPATIBILITY_FILE
    )

    interactions = pd.read_csv(
        INTERACTION_FILE
    )

    print(
        f"Students       : {len(students):,}"
    )

    print(
        f"Engineering courses : {len(courses):,}"
    )

    print(
        f"Compatibility rows  : {len(compatibility):,}"
    )

    print(
        f"OULAD interactions  : {len(interactions):,}"
    )

    return (
        students,
        courses,
        compatibility,
        interactions
    )


# ============================================================
# STUDENT ML FEATURES
# ============================================================

def build_student_ml_features(
    students
):

    print(
        "\n[1] Building student ML features..."
    )

    df = students.copy()

    useful_columns = [
        "id_student",
        "learning_profile_score",
        "score_normalized",
        "best_score_normalized",
        "pass_rate_normalized",
        "assessment_activity_normalized",
        "course_experience_normalized",
        "engagement_normalized",
        "academic_score",
        "average_strength",
        "courses_attempted",
        "total_assessments",
        "active_days",
        "engagement_score",
        "learning_level",
        "academic_strength",
        "engagement_strength",
        "performance_category",
        "readiness_score",
        "overall_gap_level",
        "readiness_category",
    ]

    available_columns = [
        column
        for column in useful_columns
        if column in df.columns
    ]

    df = df[available_columns].copy()

    # --------------------------------------------------------
    # Remove duplicate students
    # --------------------------------------------------------

    df = (
        df
        .sort_values("id_student")
        .drop_duplicates(
            subset=["id_student"],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # Convert numeric columns
    # --------------------------------------------------------

    for column in df.columns:

        if column == "id_student":
            continue

        if df[column].dtype != "object":

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns

    df[numeric_columns] = (
        df[numeric_columns]
        .fillna(0)
    )

    return df


# ============================================================
# ENGINEERING COURSE ML FEATURES
# ============================================================

def build_course_ml_features(
    courses
):

    print(
        "\n[2] Building engineering course ML features..."
    )

    df = courses.copy()

    useful_columns = [
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "skills",
        "prerequisites",
        "difficulty",
        "credits",
        "course_level",
        "is_core",
        "skill_count",
        "difficulty_normalized",
        "difficulty_norm",
        "credits_norm",
        "semester_norm",
    ]

    available_columns = [
        column
        for column in useful_columns
        if column in df.columns
    ]

    df = df[available_columns].copy()

    df = (
        df
        .drop_duplicates(
            subset=["course_id"]
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Numeric cleanup
    # --------------------------------------------------------

    numeric_columns = [
        "semester",
        "difficulty",
        "credits",
        "skill_count",
        "difficulty_normalized",
        "difficulty_norm",
        "credits_norm",
        "semester_norm",
        "is_core",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------------
    # Text cleanup
    # --------------------------------------------------------

    text_columns = [
        "course_name",
        "branch",
        "category",
        "skills",
        "prerequisites",
        "course_level",
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return df


# ============================================================
# ENGINEERING CANDIDATE DATASET
# ============================================================

def build_engineering_candidates(
    students,
    compatibility,
    courses,
    top_k=20
):

    print(
        f"\n[3] Selecting top {top_k} engineering "
        "course candidates per student..."
    )

    # --------------------------------------------------------
    # Keep only required compatibility columns
    # --------------------------------------------------------

    compatibility_columns = [
        "id_student",
        "course_id",
        "student_readiness",
        "student_academic_score",
        "student_pass_rate",
        "student_engagement",
        "difficulty_fit",
        "level_fit",
        "academic_fit",
        "complexity_fit",
        "compatibility_score",
    ]

    available_columns = [
        column
        for column in compatibility_columns
        if column in compatibility.columns
    ]

    compatibility = compatibility[
        available_columns
    ].copy()

    # --------------------------------------------------------
    # Rank courses for each student
    # --------------------------------------------------------

    compatibility["candidate_rank"] = (
        compatibility
        .groupby("id_student")[
            "compatibility_score"
        ]
        .rank(
            ascending=False,
            method="first"
        )
        .astype(int)
    )

    candidates = compatibility[
        compatibility["candidate_rank"] <= top_k
    ].copy()

    # --------------------------------------------------------
    # Add course metadata
    # --------------------------------------------------------

    course_columns = [
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "skills",
        "prerequisites",
        "difficulty",
        "credits",
        "course_level",
        "is_core",
        "skill_count",
        "difficulty_normalized",
    ]

    available_course_columns = [
        column
        for column in course_columns
        if column in courses.columns
    ]

    course_metadata = courses[
        available_course_columns
    ].copy()

    candidates = candidates.merge(
        course_metadata,
        on="course_id",
        how="left"
    )

    # --------------------------------------------------------
    # Add student metadata
    # --------------------------------------------------------

    student_columns = [
        "id_student",
        "learning_level",
        "academic_strength",
        "engagement_strength",
        "performance_category",
        "readiness_score",
        "overall_gap_level",
        "readiness_category",
    ]

    available_student_columns = [
        column
        for column in student_columns
        if column in students.columns
    ]

    student_metadata = students[
        available_student_columns
    ].drop_duplicates(
        subset=["id_student"]
    )

    candidates = candidates.merge(
        student_metadata,
        on="id_student",
        how="left"
    )

    # --------------------------------------------------------
    # Final ordering
    # --------------------------------------------------------

    candidates = (
        candidates
        .sort_values(
            [
                "id_student",
                "candidate_rank"
            ]
        )
        .reset_index(drop=True)
    )

    return candidates


# ============================================================
# BUILD OULAD ML INTERACTION DATASET
# ============================================================

def build_oulad_ml_dataset(
    interactions
):

    print(
        "\n[4] Building OULAD ML interaction dataset..."
    )

    df = interactions.copy()

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required = [
        "id_student",
        "course_id",
        "interaction_score",
        "interaction",
    ]

    available = [
        column
        for column in required
        if column in df.columns
    ]

    df = df[available].copy()

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    if "id_student" in df.columns:

        df["id_student"] = pd.to_numeric(
            df["id_student"],
            errors="coerce"
        )

    if "interaction_score" in df.columns:

        df["interaction_score"] = pd.to_numeric(
            df["interaction_score"],
            errors="coerce"
        ).fillna(0)

    if "interaction" in df.columns:

        df["interaction"] = pd.to_numeric(
            df["interaction"],
            errors="coerce"
        ).fillna(0)

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
    # Remove duplicate student-course pairs
    # --------------------------------------------------------

    df = (
        df
        .sort_values(
            "interaction_score",
            ascending=False
        )
        .drop_duplicates(
            subset=[
                "id_student",
                "course_id"
            ]
        )
    )

    return df


# ============================================================
# DATASET SUMMARY
# ============================================================

def create_summary(
    students,
    courses,
    candidates,
    interactions
):

    print(
        "\n[5] Creating ML dataset summary..."
    )

    summary = pd.DataFrame({

        "dataset": [
            "Student ML Features",
            "Engineering Course ML Features",
            "Engineering Candidate Dataset",
            "OULAD Interaction Dataset",
        ],

        "rows": [
            len(students),
            len(courses),
            len(candidates),
            len(interactions),
        ],

        "unique_students": [
            students["id_student"].nunique(),
            0,
            candidates["id_student"].nunique(),
            interactions["id_student"].nunique(),
        ],

        "unique_courses": [
            0,
            courses["course_id"].nunique(),
            candidates["course_id"].nunique(),
            interactions["course_id"].nunique(),
        ],
    })

    return summary


# ============================================================
# SAVE DATASETS
# ============================================================

def save_datasets(
    students,
    courses,
    candidates,
    interactions,
    summary
):

    print(
        "\n[6] Saving ML datasets..."
    )

    student_file = (
        PROCESSED_DIR /
        "student_ml_features.csv"
    )

    course_file = (
        PROCESSED_DIR /
        "engineering_course_ml_features.csv"
    )

    candidate_file = (
        PROCESSED_DIR /
        "engineering_candidate_features.csv"
    )

    interaction_file = (
        PROCESSED_DIR /
        "oulad_ml_interactions.csv"
    )

    summary_file = (
        PROCESSED_DIR /
        "ml_dataset_summary.csv"
    )

    students.to_csv(
        student_file,
        index=False
    )

    courses.to_csv(
        course_file,
        index=False
    )

    candidates.to_csv(
        candidate_file,
        index=False
    )

    interactions.to_csv(
        interaction_file,
        index=False
    )

    summary.to_csv(
        summary_file,
        index=False
    )

    print(
        f"\nSaved:\n"
        f"  {student_file}\n"
        f"  {course_file}\n"
        f"  {candidate_file}\n"
        f"  {interaction_file}\n"
        f"  {summary_file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)

    print(
        "PHASE 3 — STEP 3.5 "
        "BUILD ML FEATURE DATASETS"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        students,
        courses,
        compatibility,
        interactions
    ) = load_datasets()

    # --------------------------------------------------------
    # Student features
    # --------------------------------------------------------

    student_ml = build_student_ml_features(
        students
    )

    # --------------------------------------------------------
    # Course features
    # --------------------------------------------------------

    course_ml = build_course_ml_features(
        courses
    )

    # --------------------------------------------------------
    # Candidate features
    # --------------------------------------------------------

    candidates = build_engineering_candidates(
        students,
        compatibility,
        courses,
        top_k=20
    )

    # --------------------------------------------------------
    # OULAD interaction data
    # --------------------------------------------------------

    oulad_ml = build_oulad_ml_dataset(
        interactions
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = create_summary(
        student_ml,
        course_ml,
        candidates,
        oulad_ml
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_datasets(
        student_ml,
        course_ml,
        candidates,
        oulad_ml,
        summary
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        "\nML DATASET SUMMARY"
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)

    print(
        "PHASE 3 — STEP 3.5 COMPLETE"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()