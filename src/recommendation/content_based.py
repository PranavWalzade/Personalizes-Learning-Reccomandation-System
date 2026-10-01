import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    ENGINEERING_COURSES_FILE,
    PROCESSED_DIR,
    MODELS_DIR,
    RESULTS_DIR,
)


# ============================================================
# SETTINGS
# ============================================================

TOP_N = 10


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    courses = pd.read_csv(ENGINEERING_COURSES_FILE)

    students = pd.read_csv(
        PROCESSED_DIR / "student_features.csv"
    )

    compatibility = pd.read_csv(
        PROCESSED_DIR / "student_engineering_compatibility.csv"
    )

    print("Engineering courses:", courses.shape)
    print("Student features:", students.shape)
    print("Compatibility:", compatibility.shape)

    return courses, students, compatibility


# ============================================================
# CLEAN COURSE DATA
# ============================================================

def prepare_course_text(courses):

    text_columns = [
        "course_name",
        "branch",
        "category",
        "skills",
        "prerequisites",
        "course_level",
    ]

    for column in text_columns:

        if column not in courses.columns:
            courses[column] = ""

        courses[column] = (
            courses[column]
            .fillna("")
            .astype(str)
            .str.lower()
        )

    courses["course_text"] = (
        courses["course_name"] + " "
        + courses["branch"] + " "
        + courses["category"] + " "
        + courses["skills"] + " "
        + courses["prerequisites"] + " "
        + courses["course_level"]
    )

    return courses


# ============================================================
# BUILD TF-IDF MODEL
# ============================================================

def build_tfidf(courses):

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_features=3000
    )

    tfidf_matrix = vectorizer.fit_transform(
        courses["course_text"]
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODELS_DIR / "content_based_tfidf.joblib"

    joblib.dump(
        vectorizer,
        model_path
    )

    print("\nTF-IDF model created.")
    print("Matrix shape:", tfidf_matrix.shape)
    print("Model saved:", model_path)

    return vectorizer, tfidf_matrix


# ============================================================
# COURSE SIMILARITY
# ============================================================

def calculate_course_similarity(tfidf_matrix):

    similarity_matrix = cosine_similarity(
        tfidf_matrix
    )

    similarity_path = (
        PROCESSED_DIR /
        "content_based_course_similarity.npz"
    )

    np.savez_compressed(
        similarity_path,
        similarity=similarity_matrix
    )

    print("Course similarity matrix saved:")
    print(similarity_path)

    return similarity_matrix


# ============================================================
# LEVEL SCORE
# ============================================================

def level_fit(student, course):

    readiness = float(
        student.get("learning_profile_score", 0.5)
    )

    level = str(
        course.get("course_level", "Intermediate")
    ).lower()

    if readiness < 0.40:

        if level == "foundation":
            return 1.0

        if level == "intermediate":
            return 0.60

        return 0.30

    elif readiness < 0.70:

        if level == "foundation":
            return 0.75

        if level == "intermediate":
            return 1.0

        return 0.65

    else:

        if level == "foundation":
            return 0.55

        if level == "intermediate":
            return 0.85

        return 1.0


# ============================================================
# DIFFICULTY SCORE
# ============================================================

def difficulty_fit(student, course):

    readiness = float(
        student.get("readiness_score", 0.5)
    )

    difficulty = float(
        course.get("difficulty_normalized", 0.5)
    )

    # Difference between student readiness
    # and course difficulty.
    difference = abs(
        readiness - difficulty
    )

    score = 1.0 - difference

    return max(
        0.0,
        min(1.0, score)
    )


# ============================================================
# ACADEMIC FIT
# ============================================================

def academic_fit(student):

    academic = float(
        student.get("academic_score", 0.5)
    )

    return max(
        0.0,
        min(1.0, academic)
    )


# ============================================================
# ENGAGEMENT FIT
# ============================================================

def engagement_fit(student):

    engagement = float(
        student.get("engagement_score", 0.5)
    )

    # engagement_score may have different
    # scales depending on preprocessing.

    if engagement > 1:
        engagement = engagement / 100.0

    return max(
        0.0,
        min(1.0, engagement)
    )


# ============================================================
# CONTENT RECOMMENDATION
# ============================================================

def recommend_for_student(
    student,
    courses,
    compatibility,
    tfidf_matrix,
    top_n=10
):

    student_id = student["id_student"]

    student_compatibility = compatibility[
        compatibility["id_student"] == student_id
    ].copy()

    if student_compatibility.empty:

        print(
            f"No compatibility data for student {student_id}"
        )

        return pd.DataFrame()

    recommendations = []

    for _, course in courses.iterrows():

        course_id = course["course_id"]

        match = student_compatibility[
            student_compatibility["course_id"] == course_id
        ]

        if match.empty:
            compatibility_score = 0.5
        else:
            compatibility_score = float(
                match.iloc[0]["compatibility_score"]
            )

        academic_score = academic_fit(student)

        engagement_score = engagement_fit(student)

        level_score = level_fit(
            student,
            course
        )

        difficulty_score = difficulty_fit(
            student,
            course
        )

        # ----------------------------------------------------
        # FINAL CONTENT-BASED SCORE
        # ----------------------------------------------------

        final_score = (
            0.35 * compatibility_score
            + 0.25 * academic_score
            + 0.15 * engagement_score
            + 0.15 * level_score
            + 0.10 * difficulty_score
        )

        recommendations.append({

            "id_student": student_id,

            "course_id": course["course_id"],

            "course_name": course["course_name"],

            "branch": course["branch"],

            "category": course["category"],

            "skills": course["skills"],

            "prerequisites": course["prerequisites"],

            "difficulty": course["difficulty"],

            "course_level": course["course_level"],

            "compatibility_score": round(
                compatibility_score,
                4
            ),

            "academic_fit": round(
                academic_score,
                4
            ),

            "engagement_fit": round(
                engagement_score,
                4
            ),

            "level_fit": round(
                level_score,
                4
            ),

            "difficulty_fit": round(
                difficulty_score,
                4
            ),

            "recommendation_score": round(
                final_score,
                4
            )
        })

    result = pd.DataFrame(
        recommendations
    )

    result = result.sort_values(
        "recommendation_score",
        ascending=False
    )

    result["recommendation_rank"] = range(
        1,
        len(result) + 1
    )

    return result.head(top_n)


# ============================================================
# EXPLANATION
# ============================================================

def create_reason(row):

    reasons = []

    if row["compatibility_score"] >= 0.70:
        reasons.append(
            "good profile compatibility"
        )

    if row["academic_fit"] >= 0.70:
        reasons.append(
            "strong academic readiness"
        )

    if row["engagement_fit"] >= 0.70:
        reasons.append(
            "good learning engagement"
        )

    if row["level_fit"] >= 0.80:
        reasons.append(
            f"suitable {row['course_level'].lower()} level"
        )

    if row["difficulty_fit"] >= 0.80:
        reasons.append(
            "difficulty matches the student's readiness"
        )

    if not reasons:
        reasons.append(
            "reasonable match with the student's current profile"
        )

    return "; ".join(reasons)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 4 - STEP 4.2")
    print("CONTENT-BASED RECOMMENDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    courses, students, compatibility = load_data()

    # --------------------------------------------------------
    # COURSE CONTENT
    # --------------------------------------------------------

    courses = prepare_course_text(courses)

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    vectorizer, tfidf_matrix = build_tfidf(
        courses
    )

    # --------------------------------------------------------
    # COURSE SIMILARITY
    # --------------------------------------------------------

    calculate_course_similarity(
        tfidf_matrix
    )

    # --------------------------------------------------------
    # SELECT SAMPLE STUDENT
    # --------------------------------------------------------

    student = students.iloc[0]

    print("\nSample student:")
    print(
        "Student ID:",
        student["id_student"]
    )

    # --------------------------------------------------------
    # RECOMMEND
    # --------------------------------------------------------

    result = recommend_for_student(
        student,
        courses,
        compatibility,
        tfidf_matrix,
        TOP_N
    )

    if result.empty:

        print(
            "\nNo recommendations generated."
        )

        return

    # --------------------------------------------------------
    # EXPLANATIONS
    # --------------------------------------------------------

    result["why_recommended"] = (
        result.apply(
            create_reason,
            axis=1
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        RESULTS_DIR /
        "content_based_sample_recommendations.csv"
    )

    result.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP RECOMMENDATIONS")
    print("=" * 70)

    display_columns = [
        "recommendation_rank",
        "course_id",
        "course_name",
        "branch",
        "course_level",
        "recommendation_score",
        "why_recommended"
    ]

    print(
        result[display_columns].to_string(
            index=False
        )
    )

    print("\nSaved result:")
    print(output_path)

    print("\nCONTENT-BASED RECOMMENDATION COMPLETE.")


if __name__ == "__main__":
    main()