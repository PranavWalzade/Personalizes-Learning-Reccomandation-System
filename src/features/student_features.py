import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ============================================================
# ADD SRC TO PYTHON PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, REPORTS_DIR


# ============================================================
# LOAD DATA
# ============================================================

def load_datasets():

    files = {
        "student_profile":
            PROCESSED_DIR / "student_profile.csv",

        "student_course_performance":
            PROCESSED_DIR / "student_course_performance.csv",

        "student_skill_profile":
            PROCESSED_DIR / "student_skill_profile.csv",

        "student_course_strength":
            PROCESSED_DIR / "student_course_strength.csv",

        "student_skill_gap":
            PROCESSED_DIR / "student_skill_gap.csv",
    }

    data = {}

    for name, path in files.items():

        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

        data[name] = pd.read_csv(path)

        print(
            f"[OK] {name:<30} "
            f"Rows: {len(data[name]):,}"
        )

    return data


# ============================================================
# CLEAN NUMERIC COLUMN
# ============================================================

def numeric_column(df, column, default=0):

    if column not in df.columns:
        return pd.Series(
            default,
            index=df.index,
            dtype=float
        )

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(default)


# ============================================================
# BUILD STUDENT FEATURES
# ============================================================

def build_student_features(data):

    profile = data["student_profile"].copy()

    performance = data[
        "student_course_performance"
    ].copy()

    skill_profile = data[
        "student_skill_profile"
    ].copy()

    course_strength = data[
        "student_course_strength"
    ].copy()

    skill_gap = data[
        "student_skill_gap"
    ].copy()

    # --------------------------------------------------------
    # Make student IDs consistent
    # --------------------------------------------------------

    for df in [
        profile,
        performance,
        skill_profile,
        course_strength,
        skill_gap
    ]:

        if "id_student" in df.columns:

            df["id_student"] = pd.to_numeric(
                df["id_student"],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Aggregate course performance
    # --------------------------------------------------------

    performance_summary = (
        performance
        .groupby("id_student")
        .agg(
            courses_attempted=(
                "course_id",
                "nunique"
            ),

            average_course_score=(
                "average_score",
                "mean"
            ),

            best_course_score=(
                "maximum_score",
                "max"
            ),

            lowest_course_score=(
                "minimum_score",
                "min"
            ),

            average_pass_rate=(
                "pass_rate",
                "mean"
            ),

            total_assessments=(
                "assessments_completed",
                "sum"
            ),

            average_assessments_per_course=(
                "assessments_completed",
                "mean"
            ),

            academic_score=(
                "academic_score",
                "mean"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Course strength
    # --------------------------------------------------------

    strength_summary = (
        course_strength
        .groupby("id_student")
        .agg(
            average_strength=(
                "strength_score",
                "mean"
            ),

            strongest_course_score=(
                "strength_score",
                "max"
            ),

            weakest_course_score=(
                "strength_score",
                "min"
            ),

            strong_courses=(
                "strength_category",
                lambda x:
                (x.astype(str).str.lower() == "strong").sum()
            ),

            weak_courses=(
                "strength_category",
                lambda x:
                (x.astype(str).str.lower() == "weak").sum()
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Skill profile
    # --------------------------------------------------------

    skill_summary = (
        skill_profile
        .drop_duplicates("id_student")
        .copy()
    )

    skill_columns = [
        "learning_level",
        "academic_strength",
        "engagement_strength",
        "performance_category",
    ]

    available_skill_columns = [
        column
        for column in skill_columns
        if column in skill_summary.columns
    ]

    skill_summary = skill_summary[
        ["id_student"] + available_skill_columns
    ]

    # --------------------------------------------------------
    # Skill gap
    # --------------------------------------------------------

    gap_summary = (
        skill_gap
        .drop_duplicates("id_student")
        .copy()
    )

    gap_columns = [
        "readiness_score",
        "overall_gap_level",
    ]

    available_gap_columns = [
        column
        for column in gap_columns
        if column in gap_summary.columns
    ]

    gap_summary = gap_summary[
        ["id_student"] + available_gap_columns
    ]

    # --------------------------------------------------------
    # Student profile aggregation
    # --------------------------------------------------------

    profile_numeric = profile.copy()

    possible_numeric_columns = [
        "avg_score",
        "total_clicks",
        "active_days",
        "engagement_score",
        "engagement_rank",
        "final_result"
    ]

    available_numeric = [
        column
        for column in possible_numeric_columns
        if column in profile_numeric.columns
    ]

    if available_numeric:

        for column in available_numeric:

            profile_numeric[column] = pd.to_numeric(
                profile_numeric[column],
                errors="coerce"
            )

        profile_summary = (
            profile_numeric
            .groupby("id_student")[available_numeric]
            .mean()
            .reset_index()
        )

    else:

        profile_summary = (
            profile_numeric[["id_student"]]
            .drop_duplicates()
        )

    # --------------------------------------------------------
    # Merge all student information
    # --------------------------------------------------------

    student_features = performance_summary.merge(
        strength_summary,
        on="id_student",
        how="left"
    )

    student_features = student_features.merge(
        skill_summary,
        on="id_student",
        how="left"
    )

    student_features = student_features.merge(
        gap_summary,
        on="id_student",
        how="left"
    )

    student_features = student_features.merge(
        profile_summary,
        on="id_student",
        how="left"
    )

    # --------------------------------------------------------
    # Fill missing numeric values
    # --------------------------------------------------------

    numeric_columns = student_features.select_dtypes(
        include=[np.number]
    ).columns

    for column in numeric_columns:

        if column != "id_student":

            student_features[column] = (
                student_features[column]
                .replace([np.inf, -np.inf], np.nan)
                .fillna(0)
            )

    # --------------------------------------------------------
    # Create normalized features
    # --------------------------------------------------------

    student_features["score_normalized"] = (
        student_features["average_course_score"] / 100
    ).clip(0, 1)

    student_features["best_score_normalized"] = (
        student_features["best_course_score"] / 100
    ).clip(0, 1)

    student_features["pass_rate_normalized"] = (
        student_features["average_pass_rate"]
    ).clip(0, 1)

    student_features["assessment_activity_normalized"] = (
        student_features["average_assessments_per_course"] /
        max(
            student_features["average_assessments_per_course"].max(),
            1
        )
    ).clip(0, 1)

    student_features["course_experience_normalized"] = (
        student_features["courses_attempted"] /
        max(
            student_features["courses_attempted"].max(),
            1
        )
    ).clip(0, 1)

    # --------------------------------------------------------
    # Engagement normalization
    # --------------------------------------------------------

    if "engagement_score" in student_features.columns:

        max_engagement = max(
            student_features["engagement_score"].max(),
            1
        )

        student_features[
            "engagement_normalized"
        ] = (
            student_features["engagement_score"]
            / max_engagement
        ).clip(0, 1)

    else:

        student_features[
            "engagement_normalized"
        ] = 0

    # --------------------------------------------------------
    # Overall learning profile score
    # --------------------------------------------------------

    student_features["learning_profile_score"] = (
        0.30 *
        student_features["score_normalized"]

        + 0.20 *
        student_features["pass_rate_normalized"]

        + 0.15 *
        student_features["engagement_normalized"]

        + 0.15 *
        student_features["assessment_activity_normalized"]

        + 0.10 *
        student_features["course_experience_normalized"]

        + 0.10 *
        student_features["average_strength"].clip(0, 1)
    )

    student_features[
        "learning_profile_score"
    ] = student_features[
        "learning_profile_score"
    ].clip(0, 1)

    # --------------------------------------------------------
    # Readiness category
    # --------------------------------------------------------

    def readiness_category(score):

        if score < 0.40:
            return "Beginner"

        elif score < 0.70:
            return "Intermediate"

        else:
            return "Advanced"

    student_features["readiness_category"] = (
        student_features[
            "learning_profile_score"
        ].apply(readiness_category)
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Remove final_result from ML features
    #
    # It is an outcome variable and creates leakage.
    # --------------------------------------------------------

    if "final_result" in student_features.columns:

        student_features = student_features.drop(
            columns=["final_result"]
        )

    # --------------------------------------------------------
    # Remove duplicate students
    # --------------------------------------------------------

    student_features = (
        student_features
        .drop_duplicates("id_student")
        .reset_index(drop=True)
    )

    return student_features


# ============================================================
# SAVE DATA
# ============================================================

def save_features(student_features):

    output_file = (
        PROCESSED_DIR /
        "student_features.csv"
    )

    student_features.to_csv(
        output_file,
        index=False
    )

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("PHASE 3 — STUDENT FEATURE ENGINEERING")
    print("=" * 70)

    print("\n[1] Loading datasets...\n")

    data = load_datasets()

    print("\n[2] Building student features...")

    student_features = build_student_features(data)

    print(
        f"\n[3] Final student feature dataset:"
    )

    print(
        f"Rows    : {len(student_features):,}"
    )

    print(
        f"Columns : {len(student_features.columns)}"
    )

    print("\nFeature columns:")

    for column in student_features.columns:

        print(f"  - {column}")

    print("\n[4] Saving dataset...")

    output_file = save_features(
        student_features
    )

    print(f"\nSaved to:")
    print(output_file)

    print("\nPreview:")
    print(
        student_features.head().to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("PHASE 3 — STEP 3.1 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()