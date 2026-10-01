import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, RESULTS_DIR


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = (
    RESULTS_DIR /
    "hybrid_engineering_recommendations.csv"
)

OUTPUT_FILE = (
    RESULTS_DIR /
    "explainable_engineering_recommendations.csv"
)


# ============================================================
# EXPLANATION FUNCTION
# ============================================================

def generate_explanation(row):

    reasons = []

    # --------------------------------------------------------
    # Compatibility
    # --------------------------------------------------------

    compatibility = float(
        row.get("compatibility_normalized", 0)
    )

    if compatibility >= 0.70:
        reasons.append(
            "Strong match with your academic profile"
        )

    elif compatibility >= 0.50:
        reasons.append(
            "Good match with your academic profile"
        )

    else:
        reasons.append(
            "Provides a suitable learning opportunity"
        )

    # --------------------------------------------------------
    # Readiness
    # --------------------------------------------------------

    readiness_fit = float(
        row.get("readiness_fit", 0)
    )

    if readiness_fit >= 0.75:
        reasons.append(
            "Suitable for your current readiness level"
        )

    elif readiness_fit >= 0.50:
        reasons.append(
            "Reasonably aligned with your readiness level"
        )

    # --------------------------------------------------------
    # Difficulty
    # --------------------------------------------------------

    difficulty_fit = float(
        row.get("difficulty_fit", 0)
    )

    if difficulty_fit >= 0.75:
        reasons.append(
            "Course difficulty matches your current level"
        )

    elif difficulty_fit >= 0.50:
        reasons.append(
            "Course difficulty is appropriate for you"
        )

    # --------------------------------------------------------
    # Content
    # --------------------------------------------------------

    content_score = float(
        row.get("content_score", 0)
    )

    if content_score >= 0.70:
        reasons.append(
            "Course content is highly suitable for your profile"
        )

    elif content_score >= 0.50:
        reasons.append(
            "Course content fits your learning profile"
        )

    # --------------------------------------------------------
    # Course complexity / skills
    # --------------------------------------------------------

    skill_count = float(
        row.get("skill_count", 0)
    )

    if skill_count >= 5:
        reasons.append(
            "Builds multiple technical skills"
        )

    elif skill_count >= 3:
        reasons.append(
            "Helps develop several useful skills"
        )

    # --------------------------------------------------------
    # Core course
    # --------------------------------------------------------

    is_core = row.get("is_core", 0)

    try:
        is_core = int(is_core)
    except (ValueError, TypeError):
        is_core = 0

    if is_core == 1:
        reasons.append(
            "Important core engineering subject"
        )

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    if not reasons:
        reasons.append(
            "Recommended based on your overall learning profile"
        )

    return reasons


# ============================================================
# CREATE EXPLANATIONS
# ============================================================

def create_explanations():

    print("=" * 60)
    print("EXPLAINABLE ENGINEERING RECOMMENDATIONS")
    print("=" * 60)

    print("\nLoading recommendations...")

    data = pd.read_csv(
        INPUT_FILE
    )

    print(
        "Recommendation records:",
        len(data)
    )

    explanations = []

    explanation_texts = []

    for _, row in data.iterrows():

        reasons = generate_explanation(
            row
        )

        explanations.append(
            " | ".join(
                reasons
            )
        )

        explanation_texts.append(
            reasons
        )

    data["recommendation_reasons"] = (
        explanations
    )

    data["reason_count"] = (
        data["recommendation_reasons"]
        .str.split("|")
        .str.len()
    )

    # --------------------------------------------------------
    # Create shorter display explanation
    # --------------------------------------------------------

    data["why_recommended"] = (
        data["recommendation_reasons"]
    )

    # --------------------------------------------------------
    # Select useful columns
    # --------------------------------------------------------

    preferred_columns = [
        "id_student",
        "recommendation_rank",
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "difficulty",
        "credits",
        "course_level",
        "hybrid_score",
        "content_score",
        "compatibility_normalized",
        "readiness_fit",
        "difficulty_fit",
        "popularity_score",
        "recommendation_reasons",
        "why_recommended"
    ]

    output_columns = [
        column
        for column in preferred_columns
        if column in data.columns
    ]

    result = data[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nSaved to:")

    print(OUTPUT_FILE)

    # --------------------------------------------------------
    # Display sample
    # --------------------------------------------------------

    if len(result) > 0:

        student_id = result[
            "id_student"
        ].iloc[0]

        sample = result[
            result["id_student"]
            == student_id
        ].head(5)

        print("\n" + "=" * 60)
        print("SAMPLE EXPLAINABLE RECOMMENDATIONS")
        print("=" * 60)

        for _, row in sample.iterrows():

            print(
                f"\n{row['recommendation_rank']}. "
                f"{row['course_name']}"
            )

            print(
                f"   Score: "
                f"{row['hybrid_score']:.4f}"
            )

            print(
                "   Why:"
            )

            reasons = str(
                row["recommendation_reasons"]
            ).split("|")

            for reason in reasons:
                print(
                    f"   ✓ {reason.strip()}"
                )

    print("\n" + "=" * 60)
    print("STEP 4.12 COMPLETED")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_explanations()