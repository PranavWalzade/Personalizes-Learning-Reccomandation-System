import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    PROCESSED_DIR,
    RESULTS_DIR,
    ENGINEERING_COURSES_FILE,
)


# ============================================================
# SETTINGS
# ============================================================

TOP_N = 10

# Hybrid weights
CONTENT_WEIGHT = 0.25
COMPATIBILITY_WEIGHT = 0.30
READINESS_WEIGHT = 0.20
DIFFICULTY_WEIGHT = 0.15
POPULARITY_WEIGHT = 0.10


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def min_max_normalize(series):
    """
    Normalize values between 0 and 1.
    """
    series = pd.to_numeric(series, errors="coerce").fillna(0)

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            np.ones(len(series)),
            index=series.index
        )

    return (series - minimum) / (maximum - minimum)


def calculate_difficulty_fit(student_readiness, course_difficulty):
    """
    Calculate how well the course difficulty matches
    the student's readiness.

    This function works with a single course value.
    """

    try:
        student_readiness = float(student_readiness)
    except (ValueError, TypeError):
        student_readiness = 0.5

    try:
        course_difficulty = float(course_difficulty)
    except (ValueError, TypeError):
        course_difficulty = 0.5

    # Keep values between 0 and 1
    student_readiness = max(
        0.0,
        min(1.0, student_readiness)
    )

    course_difficulty = max(
        0.0,
        min(1.0, course_difficulty)
    )

    # Difference between readiness and difficulty
    distance = abs(
        student_readiness - course_difficulty
    )

    # Smaller difference = better fit
    fit = 1.0 - distance

    return max(
        0.0,
        min(1.0, fit)
    )

# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("HYBRID ENGINEERING RECOMMENDATION ENGINE")
    print("=" * 60)

    print("\nLoading student features...")

    student_file = PROCESSED_DIR / "student_features.csv"

    students = pd.read_csv(student_file)

    print("Students:", len(students))

    print("\nLoading engineering courses...")

    courses = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    print("Engineering courses:", len(courses))

    print("\nLoading compatibility scores...")

    compatibility_file = (
        PROCESSED_DIR /
        "student_engineering_compatibility.csv"
    )

    compatibility = pd.read_csv(
        compatibility_file
    )

    print(
        "Compatibility records:",
        len(compatibility)
    )

    return students, courses, compatibility


# ============================================================
# ENGINEERING POPULARITY
# ============================================================

def calculate_course_popularity(courses):

    print("\nCalculating engineering course popularity...")

    popularity = pd.DataFrame()

    popularity["course_id"] = courses["course_id"]

    # Core courses receive slightly higher baseline popularity.
    core_score = pd.to_numeric(
        courses["is_core"],
        errors="coerce"
    ).fillna(0)

    # Lower semester courses are generally more broadly applicable.
    semester = pd.to_numeric(
        courses["semester"],
        errors="coerce"
    ).fillna(1)

    semester_score = 1 / semester

    popularity["popularity_raw"] = (
        0.70 * core_score +
        0.30 * semester_score
    )

    popularity["popularity_score"] = (
        min_max_normalize(
            popularity["popularity_raw"]
        )
    )

    return popularity[
        ["course_id", "popularity_score"]
    ]


# ============================================================
# CONTENT SCORE
# ============================================================

def calculate_content_score(student, course):

    """
    Baseline content score.

    Because OULAD does not contain engineering branch/interests,
    this uses the student's academic and learning characteristics
    rather than pretending there is a direct skill mapping.
    """

    academic_strength = float(
        student.get("academic_strength", 0.5)
    )

    engagement_strength = float(
        student.get("engagement_strength", 0.5)
    )

    readiness_score = float(
        student.get("readiness_score", 0.5)
    )

    difficulty = float(
        course.get("difficulty_normalized", 0.5)
    )

    skill_count = float(
        course.get("skill_count", 1)
    )

    # More complex courses need stronger preparation.
    complexity = min(skill_count / 10, 1)

    difficulty_fit = 1 - abs(
        readiness_score - difficulty
    )

    difficulty_fit = max(
        0,
        min(1, difficulty_fit)
    )

    content_score = (
        0.40 * academic_strength +
        0.20 * engagement_strength +
        0.25 * difficulty_fit +
        0.15 * complexity
    )

    return max(
        0,
        min(1, content_score)
    )


# ============================================================
# BUILD HYBRID RECOMMENDATIONS
# ============================================================

def build_recommendations(
    students,
    courses,
    compatibility,
    popularity
):

    print("\nBuilding hybrid recommendations...")

    # --------------------------------------------------------
    # Merge compatibility with course information
    # --------------------------------------------------------

    data = compatibility.merge(
        courses,
        on="course_id",
        how="left",
        suffixes=("", "_course")
    )

    data = data.merge(
        popularity,
        on="course_id",
        how="left"
    )

    # --------------------------------------------------------
    # Merge student information
    # --------------------------------------------------------

    student_columns = [
        "id_student",
        "academic_strength",
        "engagement_strength",
        "readiness_score",
        "learning_level",
        "learning_profile_score"
    ]

    available_columns = [
        col
        for col in student_columns
        if col in students.columns
    ]

    student_data = students[
        available_columns
    ].drop_duplicates(
        subset=["id_student"]
    )

    data = data.merge(
        student_data,
        on="id_student",
        how="left"
    )

    print(
        "Candidate records:",
        len(data)
    )

    # --------------------------------------------------------
    # Numeric cleaning
    # --------------------------------------------------------

    numeric_columns = [
        "compatibility_score",
        "difficulty_normalized",
        "skill_count",
        "popularity_score",
        "academic_strength",
        "engagement_strength",
        "readiness_score",
        "learning_profile_score"
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------------
    # Calculate scores
    # --------------------------------------------------------

    content_scores = []
    difficulty_scores = []
    readiness_scores = []

    for _, row in data.iterrows():

        student = {
            "academic_strength":
                row.get("academic_strength", 0.5),

            "engagement_strength":
                row.get("engagement_strength", 0.5),

            "readiness_score":
                row.get("readiness_score", 0.5)
        }

        course = {
            "difficulty_normalized":
                row.get("difficulty_normalized", 0.5),

            "skill_count":
                row.get("skill_count", 1)
        }

        # Content suitability
        content_score = calculate_content_score(
            student,
            course
        )

        content_scores.append(
            content_score
        )

        # Difficulty fit
        difficulty_fit = calculate_difficulty_fit(
            student["readiness_score"],
            course["difficulty_normalized"]
        )

        difficulty_scores.append(
            difficulty_fit
        )

        # Readiness fit
        readiness_fit = (
            1 -
            abs(
                student["readiness_score"] -
                course["difficulty_normalized"]
            )
        )

        readiness_scores.append(
            max(0, min(1, readiness_fit))
        )

    data["content_score"] = content_scores

    data["difficulty_fit"] = difficulty_scores

    data["readiness_fit"] = readiness_scores

    # --------------------------------------------------------
    # Normalize compatibility
    # --------------------------------------------------------

    data["compatibility_normalized"] = (
        min_max_normalize(
            data["compatibility_score"]
        )
    )

    # --------------------------------------------------------
    # Final hybrid score
    # --------------------------------------------------------

    data["hybrid_score"] = (

        CONTENT_WEIGHT *
        data["content_score"]

        +

        COMPATIBILITY_WEIGHT *
        data["compatibility_normalized"]

        +

        READINESS_WEIGHT *
        data["readiness_fit"]

        +

        DIFFICULTY_WEIGHT *
        data["difficulty_fit"]

        +

        POPULARITY_WEIGHT *
        data["popularity_score"]
    )

    # --------------------------------------------------------
    # Rank courses for every student
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

    data["recommendation_rank"] = (
        data.groupby("id_student")
        .cumcount() + 1
    )

    recommendations = data[
        data["recommendation_rank"] <= TOP_N
    ].copy()

    return recommendations


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(recommendations):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        RESULTS_DIR /
        "hybrid_engineering_recommendations.csv"
    )

    recommendations.to_csv(
        output_file,
        index=False
    )

    print("\nRecommendations saved to:")

    print(output_file)

    # --------------------------------------------------------
    # Sample recommendations
    # --------------------------------------------------------

    if len(recommendations) > 0:

        first_student = recommendations[
            "id_student"
        ].iloc[0]

        sample = recommendations[
            recommendations["id_student"]
            == first_student
        ].copy()

        sample_file = (
            RESULTS_DIR /
            "hybrid_engineering_sample.csv"
        )

        sample[
            [
                "id_student",
                "course_id",
                "course_name",
                "branch",
                "category",
                "difficulty",
                "hybrid_score",
                "recommendation_rank"
            ]
        ].to_csv(
            sample_file,
            index=False
        )

        print(
            "Sample recommendations saved to:"
        )

        print(sample_file)

        print("\n" + "=" * 60)
        print("SAMPLE TOP RECOMMENDATIONS")
        print("=" * 60)

        print(
            sample[
                [
                    "course_id",
                    "course_name",
                    "branch",
                    "hybrid_score",
                    "recommendation_rank"
                ]
            ].to_string(
                index=False
            )
        )


# ============================================================
# MAIN
# ============================================================

def main():

    students, courses, compatibility = load_data()

    popularity = calculate_course_popularity(
        courses
    )

    recommendations = build_recommendations(
        students,
        courses,
        compatibility,
        popularity
    )

    save_results(
        recommendations
    )

    print("\n" + "=" * 60)
    print("STEP 4.11 COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()