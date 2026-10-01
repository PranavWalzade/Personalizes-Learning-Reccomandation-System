import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, RESULTS_DIR


# ============================================================
# SETTINGS
# ============================================================

TOP_N = 10
SIMILAR_USERS = 20


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    interactions = pd.read_csv(
        PROCESSED_DIR / "oulad_ml_interactions.csv"
    )

    print("\nInteraction columns:")
    print(interactions.columns.tolist())

    return interactions


# ============================================================
# PREPARE INDICES
# ============================================================

def prepare_indices(interactions):

    interactions = interactions.copy()

    # Clean IDs
    interactions["id_student"] = pd.to_numeric(
        interactions["id_student"],
        errors="coerce"
    )

    interactions["course_id"] = (
        interactions["course_id"]
        .astype(str)
        .str.strip()
    )

    interactions = interactions.dropna(
        subset=["id_student", "course_id"]
    )

    # --------------------------------------------------------
    # CREATE USER INDEX
    # --------------------------------------------------------

    students = sorted(
        interactions["id_student"].unique()
    )

    student_mapping = pd.DataFrame({
        "user_index": range(len(students)),
        "id_student": students
    })

    # --------------------------------------------------------
    # CREATE COURSE INDEX
    # --------------------------------------------------------

    courses = sorted(
        interactions["course_id"].unique()
    )

    course_mapping = pd.DataFrame({
        "item_index": range(len(courses)),
        "course_id": courses
    })

    # --------------------------------------------------------
    # MERGE INDICES
    # --------------------------------------------------------

    interactions = interactions.merge(
        student_mapping,
        on="id_student",
        how="left"
    )

    interactions = interactions.merge(
        course_mapping,
        on="course_id",
        how="left"
    )

    # --------------------------------------------------------
    # SAVE MAPPINGS
    # --------------------------------------------------------

    student_mapping.to_csv(
        PROCESSED_DIR /
        "cf_student_index_mapping.csv",
        index=False
    )

    course_mapping.to_csv(
        PROCESSED_DIR /
        "cf_course_index_mapping.csv",
        index=False
    )

    print("\nUsers:", len(student_mapping))
    print("Courses:", len(course_mapping))

    return (
        interactions,
        student_mapping,
        course_mapping
    )


# ============================================================
# CREATE USER-COURSE MATRIX
# ============================================================

def create_matrix(
    interactions,
    student_mapping,
    course_mapping
):

    n_users = len(student_mapping)
    n_items = len(course_mapping)

    matrix = np.zeros(
        (n_users, n_items),
        dtype=np.float32
    )

    for _, row in interactions.iterrows():

        user_index = int(
            row["user_index"]
        )

        item_index = int(
            row["item_index"]
        )

        score = float(
            row["interaction_score"]
        )

        matrix[
            user_index,
            item_index
        ] = score

    print("\nUser-course matrix:")
    print("Shape:", matrix.shape)

    return matrix


# ============================================================
# CALCULATE USER SIMILARITY
# ============================================================

def calculate_user_similarity(matrix):

    print("\nCalculating user similarity...")

    similarity = cosine_similarity(
        matrix
    ).astype(np.float32)

    print(
        "Similarity matrix:",
        similarity.shape
    )

    return similarity


# ============================================================
# RECOMMEND COURSES
# ============================================================

def recommend_for_user(
    user_index,
    matrix,
    similarity_matrix,
    student_mapping,
    course_mapping,
    top_n=10
):

    # --------------------------------------------------------
    # GET SIMILAR USERS
    # --------------------------------------------------------

    similarities = similarity_matrix[
        user_index
    ].copy()

    # Remove the current student
    similarities[user_index] = -1

    similar_indices = np.argsort(
        similarities
    )[::-1]

    similar_indices = similar_indices[
        :SIMILAR_USERS
    ]

    # --------------------------------------------------------
    # CALCULATE WEIGHTED COURSE SCORES
    # --------------------------------------------------------

    course_scores = np.zeros(
        matrix.shape[1],
        dtype=np.float32
    )

    similarity_sum = 0.0

    for similar_user in similar_indices:

        similarity = float(
            similarities[similar_user]
        )

        if similarity <= 0:
            continue

        course_scores += (
            similarity
            * matrix[similar_user]
        )

        similarity_sum += similarity

    if similarity_sum > 0:

        course_scores /= similarity_sum

    # --------------------------------------------------------
    # REMOVE COURSES ALREADY SEEN
    # --------------------------------------------------------

    already_seen = (
        matrix[user_index] > 0
    )

    course_scores[already_seen] = -1

    # --------------------------------------------------------
    # GET TOP COURSES
    # --------------------------------------------------------

    top_indices = np.argsort(
        course_scores
    )[::-1]

    recommendations = []

    student_id = student_mapping.iloc[
        user_index
    ]["id_student"]

    for item_index in top_indices:

        if course_scores[item_index] < 0:
            continue

        course_id = course_mapping.iloc[
            item_index
        ]["course_id"]

        recommendations.append({

            "id_student": int(student_id),

            "user_index": user_index,

            "course_id": course_id,

            "item_index": int(item_index),

            "collaborative_score": round(
                float(
                    course_scores[item_index]
                ),
                4
            ),

            "recommendation_rank":
                len(recommendations) + 1
        })

        if len(recommendations) >= top_n:
            break

    return pd.DataFrame(
        recommendations
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 4 - STEP 4.3")
    print("USER-BASED COLLABORATIVE FILTERING")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    interactions = load_data()

    print(
        "\nInteractions:",
        interactions.shape
    )

    # --------------------------------------------------------
    # PREPARE INDICES
    # --------------------------------------------------------

    (
        interactions,
        student_mapping,
        course_mapping
    ) = prepare_indices(
        interactions
    )

    # --------------------------------------------------------
    # CREATE MATRIX
    # --------------------------------------------------------

    matrix = create_matrix(
        interactions,
        student_mapping,
        course_mapping
    )

    # --------------------------------------------------------
    # USER SIMILARITY
    # --------------------------------------------------------

    similarity_matrix = (
        calculate_user_similarity(
            matrix
        )
    )

    # --------------------------------------------------------
    # SAMPLE USER
    # --------------------------------------------------------

    user_index = 0

    student_id = student_mapping.iloc[
        user_index
    ]["id_student"]

    print(
        "\nSample student ID:",
        student_id
    )

    # --------------------------------------------------------
    # RECOMMEND
    # --------------------------------------------------------

    result = recommend_for_user(
        user_index,
        matrix,
        similarity_matrix,
        student_mapping,
        course_mapping,
        TOP_N
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
        "user_based_cf_sample_recommendations.csv"
    )

    result.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP COLLABORATIVE RECOMMENDATIONS")
    print("=" * 70)

    if result.empty:

        print(
            "No new recommendations found."
        )

    else:

        print(
            result.to_string(
                index=False
            )
        )

    print("\nSaved:")
    print(output_path)

    print(
        "\nUSER-BASED COLLABORATIVE "
        "FILTERING COMPLETE."
    )


if __name__ == "__main__":
    main()