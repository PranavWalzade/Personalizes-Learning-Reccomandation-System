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

    student_file = (
        PROCESSED_DIR /
        "student_features.csv"
    )

    course_file = (
        PROCESSED_DIR /
        "course_features.csv"
    )

    if not student_file.exists():
        raise FileNotFoundError(
            f"Student feature file not found:\n{student_file}"
        )

    if not course_file.exists():
        raise FileNotFoundError(
            f"Course feature file not found:\n{course_file}"
        )

    students = pd.read_csv(student_file)
    courses = pd.read_csv(course_file)

    print(
        f"Students loaded : {len(students):,}"
    )

    print(
        f"Courses loaded  : {len(courses):,}"
    )

    return students, courses


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_series(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        (series - minimum) /
        (maximum - minimum)
    ).clip(0, 1)


# ============================================================
# PREPARE STUDENT FEATURES
# ============================================================

def prepare_students(students):

    df = students.copy()

    numeric_columns = [
        "learning_profile_score",
        "score_normalized",
        "pass_rate_normalized",
        "engagement_normalized",
        "average_strength",
        "courses_attempted",
    ]

    for column in numeric_columns:

        if column not in df.columns:

            df[column] = 0

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # Ensure values are within 0-1
    # --------------------------------------------------------

    for column in [
        "learning_profile_score",
        "score_normalized",
        "pass_rate_normalized",
        "engagement_normalized",
        "average_strength",
    ]:

        df[column] = df[column].clip(0, 1)

    return df


# ============================================================
# PREPARE COURSE FEATURES
# ============================================================

def prepare_courses(courses):

    df = courses.copy()

    numeric_columns = [
        "difficulty",
        "credits",
        "semester",
        "difficulty_norm",
        "credits_norm",
        "semester_norm",
    ]

    for column in numeric_columns:

        if column not in df.columns:

            df[column] = 0

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # Normalize difficulty
    # --------------------------------------------------------

    df["difficulty_score"] = (
        (df["difficulty"] - 1) / 4
    ).clip(0, 1)

    # --------------------------------------------------------
    # Skill complexity
    # --------------------------------------------------------

    if "skill_count" in df.columns:

        df["skill_complexity"] = (
            normalize_series(
                df["skill_count"]
            )
        )

    else:

        df["skill_complexity"] = 0.5

    # --------------------------------------------------------
    # Course level
    # --------------------------------------------------------

    if "semester" in df.columns:

        df["course_level_score"] = (
            (df["semester"] - 1) / 7
        ).clip(0, 1)

    else:

        df["course_level_score"] = 0.5

    return df


# ============================================================
# STUDENT → COURSE COMPATIBILITY
# ============================================================

def calculate_compatibility(
    students,
    courses
):

    print(
        "\nCalculating student-course compatibility..."
    )

    results = []

    # --------------------------------------------------------
    # Create every student-course combination
    #
    # Number of rows:
    #
    # students × 155 courses
    # --------------------------------------------------------

    for _, student in students.iterrows():

        student_id = student["id_student"]

        readiness = float(
            student["learning_profile_score"]
        )

        academic = float(
            student["score_normalized"]
        )

        pass_rate = float(
            student["pass_rate_normalized"]
        )

        engagement = float(
            student["engagement_normalized"]
        )

        strength = float(
            student["average_strength"]
        )

        # ----------------------------------------------------
        # Student learning level
        # ----------------------------------------------------

        learning_level = str(
            student.get(
                "learning_level",
                "Intermediate"
            )
        ).lower()

        # ----------------------------------------------------
        # Evaluate every engineering course
        # ----------------------------------------------------

        for _, course in courses.iterrows():

            course_id = course["course_id"]

            difficulty = float(
                course["difficulty_score"]
            )

            complexity = float(
                course["skill_complexity"]
            )

            course_level = float(
                course["course_level_score"]
            )

            # ------------------------------------------------
            # Difficulty compatibility
            #
            # A beginner should prefer easier courses.
            # An advanced student can handle harder courses.
            # ------------------------------------------------

            difficulty_difference = abs(
                readiness -
                difficulty
            )

            difficulty_fit = (
                1 -
                difficulty_difference
            )

            difficulty_fit = np.clip(
                difficulty_fit,
                0,
                1
            )

            # ------------------------------------------------
            # Level compatibility
            # ------------------------------------------------

            level_difference = abs(
                readiness -
                course_level
            )

            level_fit = (
                1 -
                level_difference
            )

            level_fit = np.clip(
                level_fit,
                0,
                1
            )

            # ------------------------------------------------
            # Overall student strength
            # ------------------------------------------------

            academic_fit = (
                0.50 * academic
                + 0.25 * pass_rate
                + 0.25 * strength
            )

            academic_fit = np.clip(
                academic_fit,
                0,
                1
            )

            # ------------------------------------------------
            # Course complexity fit
            # ------------------------------------------------

            complexity_fit = (
                1 -
                abs(
                    readiness -
                    complexity
                )
            )

            complexity_fit = np.clip(
                complexity_fit,
                0,
                1
            )

            # ------------------------------------------------
            # Final compatibility
            #
            # This is a baseline score, NOT the final ML
            # recommendation score.
            # ------------------------------------------------

            compatibility = (
                0.35 * difficulty_fit
                + 0.25 * level_fit
                + 0.20 * academic_fit
                + 0.10 * complexity_fit
                + 0.10 * engagement
            )

            compatibility = float(
                np.clip(
                    compatibility,
                    0,
                    1
                )
            )

            results.append({

                "id_student":
                    student_id,

                "course_id":
                    course_id,

                "branch":
                    course.get(
                        "branch",
                        ""
                    ),

                "course_name":
                    course.get(
                        "course_name",
                        ""
                    ),

                "category":
                    course.get(
                        "category",
                        ""
                    ),

                "difficulty":
                    course.get(
                        "difficulty",
                        0
                    ),

                "semester":
                    course.get(
                        "semester",
                        0
                    ),

                "student_readiness":
                    readiness,

                "student_academic_score":
                    academic,

                "student_pass_rate":
                    pass_rate,

                "student_engagement":
                    engagement,

                "difficulty_fit":
                    difficulty_fit,

                "level_fit":
                    level_fit,

                "academic_fit":
                    academic_fit,

                "complexity_fit":
                    complexity_fit,

                "compatibility_score":
                    compatibility,
            })

    return pd.DataFrame(results)


# ============================================================
# CREATE TOP COURSE REPORT
# ============================================================

def create_top_courses(
    compatibility
):

    print(
        "\nCreating top-course report..."
    )

    top_courses = (
        compatibility
        .sort_values(
            [
                "id_student",
                "compatibility_score"
            ],
            ascending=[
                True,
                False
            ]
        )
        .groupby("id_student")
        .head(10)
        .reset_index(drop=True)
    )

    return top_courses


# ============================================================
# SAVE
# ============================================================

def save_outputs(
    compatibility,
    top_courses
):

    compatibility_file = (
        PROCESSED_DIR /
        "student_engineering_compatibility.csv"
    )

    top_file = (
        PROCESSED_DIR /
        "student_top_engineering_courses.csv"
    )

    compatibility.to_csv(
        compatibility_file,
        index=False
    )

    top_courses.to_csv(
        top_file,
        index=False
    )

    print(
        "\nSaved compatibility matrix:"
    )

    print(
        compatibility_file
    )

    print(
        "\nSaved top-course dataset:"
    )

    print(
        top_file
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.4 "
        "STUDENT → ENGINEERING COURSE COMPATIBILITY"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\n[1] Loading datasets...")

    students, courses = load_data()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    print("\n[2] Preparing student features...")

    students = prepare_students(
        students
    )

    print(
        "[3] Preparing course features..."
    )

    courses = prepare_courses(
        courses
    )

    # --------------------------------------------------------
    # Compatibility
    # --------------------------------------------------------

    compatibility = calculate_compatibility(
        students,
        courses
    )

    print(
        "\nCompatibility rows:",
        f"{len(compatibility):,}"
    )

    # --------------------------------------------------------
    # Top courses
    # --------------------------------------------------------

    top_courses = create_top_courses(
        compatibility
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print("\n[4] Saving outputs...")

    save_outputs(
        compatibility,
        top_courses
    )

    # --------------------------------------------------------
    # Display example
    # --------------------------------------------------------

    if len(top_courses) > 0:

        first_student = (
            top_courses["id_student"]
            .iloc[0]
        )

        print(
            "\nExample recommendations "
            f"for student {first_student}:"
        )

        example = top_courses[
            top_courses["id_student"]
            == first_student
        ]

        print(
            example[
                [
                    "course_id",
                    "course_name",
                    "branch",
                    "difficulty",
                    "compatibility_score"
                ]
            ].to_string(
                index=False
            )
        )

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.4 COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()