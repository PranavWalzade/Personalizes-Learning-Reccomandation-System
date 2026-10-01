import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.decomposition import TruncatedSVD


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, RESULTS_DIR


# ============================================================
# SETTINGS
# ============================================================

N_COMPONENTS = 10
TOP_N = 10


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
# PREPARE DATA
# ============================================================

def prepare_data(interactions):

    interactions = interactions.copy()

    interactions["id_student"] = pd.to_numeric(
        interactions["id_student"],
        errors="coerce"
    )

    interactions["course_id"] = (
        interactions["course_id"]
        .astype(str)
        .str.strip()
    )

    interactions["interaction_score"] = pd.to_numeric(
        interactions["interaction_score"],
        errors="coerce"
    )

    interactions = interactions.dropna(
        subset=[
            "id_student",
            "course_id",
            "interaction_score"
        ]
    )

    # --------------------------------------------------------
    # CREATE INDEXES
    # --------------------------------------------------------

    students = sorted(
        interactions["id_student"].unique()
    )

    courses = sorted(
        interactions["course_id"].unique()
    )

    student_mapping = pd.DataFrame({
        "user_index": range(len(students)),
        "id_student": students
    })

    course_mapping = pd.DataFrame({
        "item_index": range(len(courses)),
        "course_id": courses
    })

    # --------------------------------------------------------
    # MERGE INDEXES
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
        "mf_student_index_mapping.csv",
        index=False
    )

    course_mapping.to_csv(
        PROCESSED_DIR /
        "mf_course_index_mapping.csv",
        index=False
    )

    print("\nNumber of students:", len(students))
    print("Number of courses:", len(courses))

    return (
        interactions,
        student_mapping,
        course_mapping
    )


# ============================================================
# CREATE MATRIX
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

    print("\nInteraction matrix:")
    print("Shape:", matrix.shape)

    return matrix


# ============================================================
# MATRIX FACTORIZATION
# ============================================================

def factorize_matrix(matrix):

    # Make sure number of components is valid
    max_components = min(
        matrix.shape[0],
        matrix.shape[1]
    ) - 1

    components = min(
        N_COMPONENTS,
        max_components
    )

    print(
        "\nUsing SVD components:",
        components
    )

    svd = TruncatedSVD(
        n_components=components,
        random_state=42
    )

    user_latent = svd.fit_transform(
        matrix
    )

    item_latent = svd.components_.T

    print(
        "User latent matrix:",
        user_latent.shape
    )

    print(
        "Item latent matrix:",
        item_latent.shape
    )

    print(
        "Explained variance:",
        round(
            float(
                svd.explained_variance_ratio_.sum()
            ),
            4
        )
    )

    return (
        svd,
        user_latent,
        item_latent
    )


# ============================================================
# RECOMMEND COURSES
# ============================================================

def recommend_for_user(
    user_index,
    matrix,
    user_latent,
    item_latent,
    student_mapping,
    course_mapping,
    top_n=10
):

    # --------------------------------------------------------
    # PREDICT SCORES
    # --------------------------------------------------------

    predicted_scores = (
        user_latent[user_index]
        @ item_latent.T
    )

    # --------------------------------------------------------
    # REMOVE ALREADY SEEN COURSES
    # --------------------------------------------------------

    already_seen = (
        matrix[user_index] > 0
    )

    predicted_scores[
        already_seen
    ] = -np.inf

    # --------------------------------------------------------
    # SORT COURSES
    # --------------------------------------------------------

    top_indices = np.argsort(
        predicted_scores
    )[::-1]

    recommendations = []

    student_id = student_mapping.iloc[
        user_index
    ]["id_student"]

    for item_index in top_indices:

        if not np.isfinite(
            predicted_scores[item_index]
        ):
            continue

        course_id = course_mapping.iloc[
            item_index
        ]["course_id"]

        recommendations.append({

            "id_student": int(
                student_id
            ),

            "user_index": user_index,

            "course_id": course_id,

            "item_index": int(
                item_index
            ),

            "predicted_score": round(
                float(
                    predicted_scores[item_index]
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
    print("PHASE 4 - STEP 4.4")
    print("MATRIX FACTORIZATION")
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
    # PREPARE
    # --------------------------------------------------------

    (
        interactions,
        student_mapping,
        course_mapping
    ) = prepare_data(
        interactions
    )

    # --------------------------------------------------------
    # MATRIX
    # --------------------------------------------------------

    matrix = create_matrix(
        interactions,
        student_mapping,
        course_mapping
    )

    # --------------------------------------------------------
    # SVD
    # --------------------------------------------------------

    (
        svd,
        user_latent,
        item_latent
    ) = factorize_matrix(
        matrix
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
        user_latent,
        item_latent,
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
        "matrix_factorization_sample_recommendations.csv"
    )

    result.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP MATRIX FACTORIZATION RECOMMENDATIONS")
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
        "\nMATRIX FACTORIZATION COMPLETE."
    )


if __name__ == "__main__":
    main()