from pathlib import Path
import sys

import numpy as np
import pandas as pd


# =========================================================
# PATH SETUP
# =========================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, RESULTS_DIR


# =========================================================
# SETTINGS
# =========================================================

TOP_K = 5
TEST_SIZE = 0.20
RANDOM_STATE = 42


# =========================================================
# METRICS
# =========================================================

def precision_at_k(recommended, relevant, k=5):

    recommended = recommended[:k]

    if len(recommended) == 0:
        return 0.0

    hits = len(
        set(recommended) & set(relevant)
    )

    return hits / k


def recall_at_k(recommended, relevant, k=5):

    if len(relevant) == 0:
        return 0.0

    recommended = recommended[:k]

    hits = len(
        set(recommended) & set(relevant)
    )

    return hits / len(relevant)


def ndcg_at_k(recommended, relevant, k=5):

    recommended = recommended[:k]
    relevant = set(relevant)

    if len(recommended) == 0:
        return 0.0

    dcg = 0.0

    for position, course in enumerate(recommended):

        if course in relevant:

            dcg += 1 / np.log2(position + 2)

    ideal_hits = min(
        len(relevant),
        k
    )

    if ideal_hits == 0:
        return 0.0

    idcg = sum(
        1 / np.log2(position + 2)
        for position in range(ideal_hits)
    )

    return dcg / idcg


# =========================================================
# LOAD DATA
# =========================================================

def load_interactions():

    file_path = (
        PROCESSED_DIR /
        "oulad_ml_interactions.csv"
    )

    print(
        f"\nLoading:\n{file_path}"
    )

    df = pd.read_csv(file_path)

    required_columns = [
        "id_student",
        "course_id",
        "interaction_score"
    ]

    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"Missing column: {column}"
            )

    df["id_student"] = pd.to_numeric(
        df["id_student"],
        errors="coerce"
    )

    df["interaction_score"] = pd.to_numeric(
        df["interaction_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "id_student",
            "course_id",
            "interaction_score"
        ]
    )

    df = df[
        df["interaction_score"] > 0
    ]

    # Remove accidental duplicate
    # student-course interactions
    df = (
        df.groupby(
            [
                "id_student",
                "course_id"
            ],
            as_index=False
        )["interaction_score"]
        .mean()
    )

    return df


# =========================================================
# TRAIN / TEST SPLIT
# =========================================================

def create_train_test_split(df):

    train_parts = []
    test_parts = []

    print("\nCreating per-student train/test split...")

    for student_id, group in df.groupby(
        "id_student"
    ):

        group = group.sort_values(
            "interaction_score",
            ascending=False
        )

        # A student with only one course
        # stays completely in training.
        if len(group) < 2:

            train_parts.append(group)

            continue

        test_count = max(
            1,
            int(
                len(group) * TEST_SIZE
            )
        )

        test_count = min(
            test_count,
            len(group) - 1
        )

        # IMPORTANT:
        # We hold out the strongest interactions
        # as relevant test items.
        test_group = group.head(
            test_count
        )

        train_group = group.iloc[
            test_count:
        ]

        train_parts.append(
            train_group
        )

        test_parts.append(
            test_group
        )

    train = pd.concat(
        train_parts,
        ignore_index=True
    )

    test = pd.concat(
        test_parts,
        ignore_index=True
    )

    return train, test


# =========================================================
# POPULARITY RECOMMENDER
# =========================================================

def popularity_recommendations(
    train,
    student_id,
    k=5
):

    popularity = (
        train.groupby("course_id")
        .agg(
            popularity_score=(
                "interaction_score",
                "mean"
            ),
            student_count=(
                "id_student",
                "nunique"
            )
        )
        .reset_index()
    )

    popularity["score"] = (
        0.60 *
        popularity["student_count"]
        / popularity["student_count"].max()
        +
        0.40 *
        popularity["popularity_score"]
        / popularity["popularity_score"].max()
    )

    popularity = popularity.sort_values(
        "score",
        ascending=False
    )

    seen_courses = set(
        train.loc[
            train["id_student"] == student_id,
            "course_id"
        ]
    )

    recommendations = []

    for course_id in popularity[
        "course_id"
    ]:

        if course_id not in seen_courses:

            recommendations.append(
                course_id
            )

        if len(recommendations) >= k:
            break

    return recommendations


# =========================================================
# EVALUATE POPULARITY
# =========================================================

def evaluate_popularity(
    train,
    test
):

    precision_scores = []
    recall_scores = []
    ndcg_scores = []

    students_evaluated = 0

    print(
        "\nEvaluating Popularity Baseline..."
    )

    for student_id, group in test.groupby(
        "id_student"
    ):

        relevant_courses = group[
            "course_id"
        ].tolist()

        recommendations = popularity_recommendations(
            train,
            student_id,
            TOP_K
        )

        if not recommendations:
            continue

        precision_scores.append(
            precision_at_k(
                recommendations,
                relevant_courses,
                TOP_K
            )
        )

        recall_scores.append(
            recall_at_k(
                recommendations,
                relevant_courses,
                TOP_K
            )
        )

        ndcg_scores.append(
            ndcg_at_k(
                recommendations,
                relevant_courses,
                TOP_K
            )
        )

        students_evaluated += 1

    return {
        "model": "Popularity Baseline",
        "students_evaluated": students_evaluated,
        "precision_at_5": np.mean(
            precision_scores
        ),
        "recall_at_5": np.mean(
            recall_scores
        ),
        "ndcg_at_5": np.mean(
            ndcg_scores
        )
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("RECOMMENDATION EVALUATION")
    print("=" * 60)

    df = load_interactions()

    print(
        f"\nTotal interactions: "
        f"{len(df):,}"
    )

    print(
        f"Students: "
        f"{df['id_student'].nunique():,}"
    )

    print(
        f"OULAD courses: "
        f"{df['course_id'].nunique():,}"
    )

    train, test = create_train_test_split(
        df
    )

    print(
        f"\nTraining interactions: "
        f"{len(train):,}"
    )

    print(
        f"Testing interactions: "
        f"{len(test):,}"
    )

    print(
        f"Test students: "
        f"{test['id_student'].nunique():,}"
    )

    # -----------------------------------------------------
    # POPULARITY
    # -----------------------------------------------------

    result = evaluate_popularity(
        train,
        test
    )

    results = [
        result
    ]

    # -----------------------------------------------------
    # DISPLAY
    # -----------------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "EVALUATION RESULTS"
    )

    print(
        "=" * 60
    )

    print(
        results_df.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        RESULTS_DIR /
        "recommendation_evaluation.csv"
    )

    results_df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nResults saved to:"
    )

    print(
        output_file
    )

    print(
        "\nStep 4.7 completed."
    )


if __name__ == "__main__":
    main()