import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Add src folder to Python path
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    OULAD_FILES,
    ENGINEERING_COURSES_FILE,
    PROCESSED_DIR,
)
# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\nLoading OULAD datasets...")

    data = {}

    for name, path in OULAD_FILES.items():

        print(f"Loading {name}.csv")

        data[name] = pd.read_csv(path)

    print("All OULAD datasets loaded.")

    return data


# ============================================================
# CLEAN STUDENT DATA
# ============================================================

def clean_students(df):

    print("\nCleaning student information...")

    df = df.copy()

    # Remove completely duplicated rows
    df = df.drop_duplicates()

    # Standardize text columns
    text_columns = [
        "code_module",
        "code_presentation",
        "gender",
        "region",
        "highest_education",
        "imd_band",
        "age_band",
        "disability",
        "final_result",
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # Convert date if available
    if "date_registration" in df.columns:

        df["date_registration"] = pd.to_numeric(
            df["date_registration"],
            errors="coerce"
        )

    print(
        f"Clean students: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# CLEAN COURSE DATA
# ============================================================

def clean_courses(df):

    print("\nCleaning course information...")

    df = df.copy()

    df = df.drop_duplicates()

    # Create a unique course presentation ID
    df["course_id"] = (
        df["code_module"].astype(str)
        + "_"
        + df["code_presentation"].astype(str)
    )

    df["module_presentation_length"] = pd.to_numeric(
        df["module_presentation_length"],
        errors="coerce"
    )

    print(
        f"Clean OULAD courses: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# CLEAN ASSESSMENTS
# ============================================================

def clean_assessments(df):

    print("\nCleaning assessment data...")

    df = df.copy()

    df = df.drop_duplicates()

    df["date"] = pd.to_numeric(
        df["date"],
        errors="coerce"
    )

    df["weight"] = pd.to_numeric(
        df["weight"],
        errors="coerce"
    )

    # Merge key
    df["course_id"] = (
        df["code_module"].astype(str)
        + "_"
        + df["code_presentation"].astype(str)
    )

    print(
        f"Clean assessments: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# CLEAN VLE DATA
# ============================================================

def clean_vle(df):

    print("\nCleaning VLE data...")

    df = df.copy()

    df = df.drop_duplicates()

    if "date" in df.columns:

        df["date"] = pd.to_numeric(
            df["date"],
            errors="coerce"
        )

    if "code_module" in df.columns:

        df["code_module"] = (
            df["code_module"]
            .astype("string")
            .str.strip()
        )

    if "code_presentation" in df.columns:

        df["code_presentation"] = (
            df["code_presentation"]
            .astype("string")
            .str.strip()
        )

    print(
        f"Clean VLE records: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# CREATE STUDENT PROFILE
# ============================================================

def create_student_profile(
    students,
    student_assessment,
    student_vle,
):

    print("\nCreating student profiles...")

    # --------------------------------------------------------
    # Academic performance
    # --------------------------------------------------------

    assessment = student_assessment.copy()

    assessment["score"] = pd.to_numeric(
        assessment["score"],
        errors="coerce"
    )

    assessment["is_pass"] = (
        assessment["score"] >= 40
    ).astype(int)

    performance = (
        assessment
        .groupby("id_student")
        .agg(
            average_score=("score", "mean"),
            maximum_score=("score", "max"),
            minimum_score=("score", "min"),
            score_std=("score", "std"),
            assessments_completed=("id_assessment", "nunique"),
            pass_rate=("is_pass", "mean"),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # VLE engagement
    # --------------------------------------------------------

    vle = student_vle.copy()

    vle["sum_click"] = pd.to_numeric(
        vle["sum_click"],
        errors="coerce"
    ).fillna(0)

    engagement = (
        vle
        .groupby("id_student")
        .agg(
            total_clicks=("sum_click", "sum"),
            interaction_records=("id_site", "count"),
            unique_resources=("id_site", "nunique"),
            active_days=("date", "nunique"),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    profile = students.merge(
        performance,
        on="id_student",
        how="left"
    )

    profile = profile.merge(
        engagement,
        on="id_student",
        how="left"
    )

    # --------------------------------------------------------
    # Missing numeric values
    # --------------------------------------------------------

    numeric_columns = [
        "average_score",
        "maximum_score",
        "minimum_score",
        "score_std",
        "assessments_completed",
        "pass_rate",
        "total_clicks",
        "interaction_records",
        "unique_resources",
        "active_days",
    ]

    for column in numeric_columns:

        if column in profile.columns:

            profile[column] = (
                profile[column]
                .fillna(0)
            )

    # --------------------------------------------------------
    # Learning engagement score
    # --------------------------------------------------------

    profile["click_score"] = (
        profile["total_clicks"]
        .rank(pct=True)
        .fillna(0)
    )

    profile["resource_score"] = (
        profile["unique_resources"]
        .rank(pct=True)
        .fillna(0)
    )

    profile["interaction_score"] = (
        profile["interaction_records"]
        .rank(pct=True)
        .fillna(0)
    )

    profile["active_day_score"] = (
        profile["active_days"]
        .rank(pct=True)
        .fillna(0)
    )

    profile["engagement_score"] = (
        0.30 * profile["click_score"]
        + 0.20 * profile["resource_score"]
        + 0.20 * profile["interaction_score"]
        + 0.30 * profile["active_day_score"]
    )

    # --------------------------------------------------------
    # Academic score
    # --------------------------------------------------------

    profile["performance_score"] = (
        profile["average_score"] / 100
    ).clip(0, 1)

    profile["academic_score"] = (
        0.50 * profile["performance_score"]
        + 0.30 * profile["pass_rate"]
        + 0.20 * (
            profile["maximum_score"] / 100
        ).clip(0, 1)
    )

    # --------------------------------------------------------
    # Overall learning score
    # --------------------------------------------------------

    profile["overall_learning_score"] = (
        0.60 * profile["academic_score"]
        + 0.40 * profile["engagement_score"]
    )

    print(
        f"Student profiles created: "
        f"{len(profile):,}"
    )

    return profile


# ============================================================
# CREATE COURSE PROFILE
# ============================================================

def create_course_profile(
    courses,
    assessments,
    vle,
    engineering,
):

    print("\nCreating course profiles...")

    # --------------------------------------------------------
    # OULAD course performance
    # --------------------------------------------------------

    assessment_scores = assessments.merge(
        pd.DataFrame(),
        how="left"
    ) if False else None

    # studentAssessment contains the actual scores,
    # so performance will be calculated separately later.

    course_profile = courses[
        [
            "course_id",
            "code_module",
            "code_presentation",
            "module_presentation_length",
        ]
    ].copy()

    # --------------------------------------------------------
    # VLE activity
    # --------------------------------------------------------

    vle_course = (
        vle
        .groupby(
            [
                "code_module",
                "code_presentation"
            ]
        )
        .agg(
            total_clicks=("sum_click", "sum"),
            interaction_records=("id_site", "count"),
            unique_resources=("id_site", "nunique"),
            active_days=("date", "nunique"),
        )
        .reset_index()
    )

    course_profile = course_profile.merge(
        vle_course,
        on=[
            "code_module",
            "code_presentation"
        ],
        how="left"
    )

    numeric_columns = [
        "total_clicks",
        "interaction_records",
        "unique_resources",
        "active_days",
    ]

    for column in numeric_columns:

        course_profile[column] = (
            course_profile[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # Engineering catalog
    # --------------------------------------------------------

    engineering = engineering.copy()

    engineering_summary = (
        engineering
        .groupby("branch")
        .agg(
            engineering_course_count=(
                "course_id",
                "count"
            )
        )
        .reset_index()
    )

    print(
        f"Engineering catalog: "
        f"{len(engineering):,} courses"
    )

    print(
        f"OULAD course profiles: "
        f"{len(course_profile):,}"
    )

    # Keep engineering summary separate.
    # OULAD course IDs and engineering course IDs
    # are NOT treated as direct matches.

    print(
        f"Engineering branches: "
        f"{len(engineering_summary):,}"
    )

    return course_profile


# ============================================================
# SAVE DATA
# ============================================================

def save_data(
    students,
    courses,
    assessments,
    vle,
    student_profile,
    course_profile,
    engineering,
):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    students.to_csv(
        PROCESSED_DIR / "clean_students.csv",
        index=False
    )

    courses.to_csv(
        PROCESSED_DIR / "clean_courses.csv",
        index=False
    )

    assessments.to_csv(
        PROCESSED_DIR / "clean_assessments.csv",
        index=False
    )

    vle.to_csv(
        PROCESSED_DIR / "clean_vle.csv",
        index=False
    )

    student_profile.to_csv(
        PROCESSED_DIR / "student_profile.csv",
        index=False
    )

    course_profile.to_csv(
        PROCESSED_DIR / "course_profile.csv",
        index=False
    )

    print("\nProcessed files saved successfully.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 2 - DATA PREPROCESSING")
    print("=" * 70)

    data = load_data()

    students = clean_students(
        data["studentInfo"]
    )

    courses = clean_courses(
        data["courses"]
    )

    assessments = clean_assessments(
        data["assessments"]
    )

    vle = clean_vle(
        data["studentVle"]
    )

    student_assessment = (
        data["studentAssessment"]
        .drop_duplicates()
        .copy()
    )

    engineering = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    student_profile = create_student_profile(
        students,
        student_assessment,
        vle,
    )

    course_profile = create_course_profile(
        courses,
        assessments,
        vle,
        engineering,
    )

    save_data(
        students,
        courses,
        assessments,
        vle,
        student_profile,
        course_profile,
        engineering,
    )

    print("\n" + "=" * 70)
    print("PHASE 2 PREPROCESSING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()