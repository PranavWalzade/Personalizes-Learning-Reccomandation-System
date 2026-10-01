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
    PROCESSED_DIR,
    ENGINEERING_COURSES_FILE,
    REPORTS_DIR,
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\nLoading datasets...")

    student_profile = pd.read_csv(
        PROCESSED_DIR / "student_profile.csv"
    )

    student_course = pd.read_csv(
        PROCESSED_DIR / "student_course_performance.csv"
    )

    engineering = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    print("Datasets loaded successfully.")

    return (
        student_profile,
        student_course,
        engineering,
    )


# ============================================================
# CLEAN ENGINEERING SKILLS
# ============================================================

def prepare_engineering_courses(engineering):

    print("\nPreparing engineering course skills...")

    engineering = engineering.copy()

    engineering["skills"] = (
        engineering["skills"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    engineering["prerequisites"] = (
        engineering["prerequisites"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Convert skill string into list
    engineering["skill_list"] = (
        engineering["skills"]
        .apply(
            lambda x: [
                skill.strip().lower()
                for skill in x.split(";")
                if skill.strip()
            ]
        )
    )

    # Number of skills
    engineering["skill_count"] = (
        engineering["skill_list"]
        .apply(len)
    )

    print(
        "Engineering courses:",
        f"{len(engineering):,}"
    )

    print(
        "Unique skills:",
        f"{len(get_all_skills(engineering)):,}"
    )

    return engineering


# ============================================================
# GET ALL SKILLS
# ============================================================

def get_all_skills(engineering):

    skills = set()

    for skill_list in engineering["skill_list"]:

        for skill in skill_list:

            skills.add(skill)

    return sorted(skills)


# ============================================================
# SKILL FREQUENCY
# ============================================================

def create_skill_frequency_report(engineering):

    print("\nCreating engineering skill report...")

    skill_count = {}

    for skill_list in engineering["skill_list"]:

        for skill in skill_list:

            if skill not in skill_count:

                skill_count[skill] = 0

            skill_count[skill] += 1

    report = pd.DataFrame(
        [
            {
                "skill": skill,
                "course_count": count,
            }
            for skill, count in skill_count.items()
        ]
    )

    report = report.sort_values(
        "course_count",
        ascending=False
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        REPORTS_DIR
        / "engineering_skill_frequency.csv"
    )

    report.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )

    return report


# ============================================================
# STUDENT LEARNING LEVEL
# ============================================================

def classify_learning_level(score):

    if score >= 0.80:

        return "Advanced"

    elif score >= 0.60:

        return "Intermediate"

    else:

        return "Foundation"


# ============================================================
# STUDENT PROFILE FOR SKILLS
# ============================================================

def create_student_skill_profile(student_profile):

    print("\nCreating student skill profile...")

    df = student_profile.copy()

    # Ensure numeric columns
    numeric_columns = [
        "average_score",
        "pass_rate",
        "total_clicks",
        "active_days",
        "engagement_score",
        "academic_score",
        "overall_learning_score",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    # Learning level
    df["learning_level"] = (
        df["overall_learning_score"]
        .apply(classify_learning_level)
    )

    # Academic strength
    df["academic_strength"] = (
        df["academic_score"]
        .apply(classify_learning_level)
    )

    # Engagement strength
    df["engagement_strength"] = (
        df["engagement_score"]
        .apply(classify_learning_level)
    )

    # Performance category
    df["performance_category"] = pd.cut(
        df["average_score"],
        bins=[
            -1,
            39.99,
            59.99,
            79.99,
            100
        ],
        labels=[
            "At Risk",
            "Average",
            "Good",
            "Excellent"
        ]
    )

    output_file = (
        PROCESSED_DIR
        / "student_skill_profile.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )

    return df


# ============================================================
# STUDENT COURSE STRENGTH
# ============================================================

def create_student_course_strength(student_course):

    print("\nCreating student course strength data...")

    df = student_course.copy()

    df["academic_score"] = pd.to_numeric(
        df["academic_score"],
        errors="coerce"
    ).fillna(0)

    df["strength_score"] = (
        0.70 * df["academic_score"]
        +
        0.30 * df["pass_rate"]
    )

    def strength_category(score):

        if score >= 0.80:

            return "Strong"

        elif score >= 0.60:

            return "Moderate"

        elif score >= 0.40:

            return "Weak"

        else:

            return "At Risk"

    df["strength_category"] = (
        df["strength_score"]
        .apply(strength_category)
    )

    output_file = (
        PROCESSED_DIR
        / "student_course_strength.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )

    return df


# ============================================================
# COURSE DIFFICULTY GROUP
# ============================================================

def create_course_difficulty_report(engineering):

    print("\nCreating course difficulty report...")

    df = engineering.copy()

    difficulty_counts = (
        df.groupby(
            [
                "course_level",
                "difficulty"
            ]
        )
        .size()
        .reset_index(
            name="course_count"
        )
    )

    output_file = (
        REPORTS_DIR
        / "engineering_course_difficulty.csv"
    )

    difficulty_counts.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )


# ============================================================
# SKILL GAP PREPARATION
# ============================================================

def prepare_skill_gap_features(
    student_skill_profile,
    engineering,
):

    print("\nPreparing skill-gap features...")

    students = student_skill_profile.copy()

    courses = engineering.copy()

    # --------------------------------------------------------
    # Determine overall student learning level
    # --------------------------------------------------------

    level_strength = {
        "Foundation": 0.35,
        "Intermediate": 0.65,
        "Advanced": 0.85,
    }

    students["learning_level_score"] = (
        students["learning_level"]
        .map(level_strength)
        .fillna(0.35)
    )

    # --------------------------------------------------------
    # Student readiness score
    # --------------------------------------------------------

    students["readiness_score"] = (
        0.50 * students["academic_score"]
        +
        0.30 * students["engagement_score"]
        +
        0.20 * students["learning_level_score"]
    )

    # --------------------------------------------------------
    # Engineering course readiness
    # --------------------------------------------------------

    courses["difficulty_normalized"] = pd.to_numeric(
        courses["difficulty_normalized"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Create general skill gap categories
    # --------------------------------------------------------

    gap_records = []

    for _, student in students.iterrows():

        readiness = student["readiness_score"]

        if readiness < 0.40:

            gap_level = "High"

        elif readiness < 0.60:

            gap_level = "Medium"

        else:

            gap_level = "Low"

        gap_records.append(
            {
                "id_student": student["id_student"],
                "learning_level": student["learning_level"],
                "academic_strength": student[
                    "academic_strength"
                ],
                "engagement_strength": student[
                    "engagement_strength"
                ],
                "readiness_score": readiness,
                "overall_gap_level": gap_level,
            }
        )

    skill_gap = pd.DataFrame(
        gap_records
    )

    output_file = (
        PROCESSED_DIR
        / "student_skill_gap.csv"
    )

    skill_gap.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )

    return skill_gap


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("STEP 2.9 - SKILL MAPPING")
    print("=" * 70)

    (
        student_profile,
        student_course,
        engineering,
    ) = load_data()

    engineering = (
        prepare_engineering_courses(
            engineering
        )
    )

    create_skill_frequency_report(
        engineering
    )

    student_skill_profile = (
        create_student_skill_profile(
            student_profile
        )
    )

    create_student_course_strength(
        student_course
    )

    create_course_difficulty_report(
        engineering
    )

    skill_gap = (
        prepare_skill_gap_features(
            student_skill_profile,
            engineering,
        )
    )

    print("\n" + "=" * 70)
    print("STEP 2.9 COMPLETE")
    print("=" * 70)

    print(
        "\nStudents processed:",
        f"{len(student_skill_profile):,}"
    )

    print(
        "Skill-gap records:",
        f"{len(skill_gap):,}"
    )

    print(
        "Engineering courses:",
        f"{len(engineering):,}"
    )


if __name__ == "__main__":
    main()