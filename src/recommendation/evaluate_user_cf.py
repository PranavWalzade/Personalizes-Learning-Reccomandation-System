from pathlib import Path
import sys

import numpy as np
import pandas as pd

from sklearn.neighbors import NearestNeighbors


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
N_NEIGHBORS = 20
TEST_SIZE = 0.20


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

    if not recommended:
        return 0.0

    dcg = 0.0

    for position, course in enumerate(
        recommended
    ):

        if course in relevant:

            dcg += (
                1 /
                np.log2(position + 2)
            )

    ideal_hits = min(
        len(relevant),
        k
    )

    if ideal_hits == 0:
        return 0.0

    idcg = sum(
        1 /
        np.log2(position + 2)
        for position in range(
            ideal_hits
        )
    )

    return dcg / idcg


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    file_path = (
        PROCESSED_DIR /
        "oulad_ml_interactions.csv"
    )

    df = pd.read_csv(
        file_path
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

    # One interaction per student/course
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

def create_split(df):

    train_parts = []
    test_parts = []

    for student_id, group in df.groupby(
        "id_student"
    ):

        group = group.sort_values(
            "interaction_score",
            ascending=False
        )

        if len(group) < 2:

            train_parts.append(
                group
            )

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
# BUILD USER-COURSE MATRIX
# =========================================================

def build_matrix(train):

    students = sorted(
        train["id_student"].unique()
    )

    courses = sorted(
        train["course_id"].unique()
    )

    student_to_index = {
        student: index
        for index, student in enumerate(
            students
        )
    }

    course_to_index = {
        course: index
        for index, course in enumerate(
            courses
        )
    }

    matrix = np.zeros(
        (
            len(students),
            len(courses)
        ),
        dtype=np.float32
    )

    for row in train.itertuples():

        user_index = (
            student_to_index[
                row.id_student
            ]
        )

        item_index = (
            course_to_index[
                row.course_id
            ]
        )

        matrix[
            user_index,
            item_index
        ] = row.interaction_score

    return (
        matrix,
        student_to_index,
        course_to_index,
        courses
    )


# =========================================================
# TRAIN USER CF
# =========================================================

def train_user_cf(matrix):

    print(
        "\nTraining User-Based CF..."
    )

    print(
        f"User matrix shape: "
        f"{matrix.shape}"
    )

    model = NearestNeighbors(
        metric="cosine",
        algorithm="brute",
        n_neighbors=min(
            N_NEIGHBORS + 1,
            matrix.shape[0]
        )
    )

    model.fit(
        matrix
    )

    return model


# =========================================================
# RECOMMEND
# =========================================================

def recommend(
    student_id,
    train,
    matrix,
    model,
    student_to_index,
    course_to_index,
    courses,
    k=5
):

    if student_id not in student_to_index:
        return []

    user_index = (
        student_to_index[
            student_id
        ]
    )

    user_vector = matrix[
        user_index
    ].reshape(1, -1)

    distances, indices = model.kneighbors(
        user_vector
    )

    neighbor_indices = indices[0][1:]

    neighbor_distances = distances[0][1:]

    scores = np.zeros(
        len(courses),
        dtype=np.float32
    )

    total_weight = 0.0

    for neighbor_index, distance in zip(
        neighbor_indices,
        neighbor_distances
    ):

        similarity = 1.0 - distance

        if similarity <= 0:
            continue

        scores += (
            similarity *
            matrix[neighbor_index]
        )

        total_weight += similarity

    if total_weight > 0:

        scores /= total_weight

    # Do not recommend already-seen courses
    seen = set(
        train.loc[
            train["id_student"] == student_id,
            "course_id"
        ]
    )

    ranked_indices = np.argsort(
        scores
    )[::-1]

    recommendations = []

    for index in ranked_indices:

        course_id = courses[index]

        if course_id in seen:
            continue

        recommendations.append(
            course_id
        )

        if len(recommendations) >= k:
            break

    return recommendations


# =========================================================
# EVALUATION
# =========================================================

def evaluate(
    train,
    test,
    matrix,
    model,
    student_to_index,
    course_to_index,
    courses
):

    precision_scores = []
    recall_scores = []
    ndcg_scores = []

    students_evaluated = 0

    print(
        "\nEvaluating User-Based CF..."
    )

    for counter, (
        student_id,
        group
    ) in enumerate(
        test.groupby("id_student"),
        start=1
    ):

        relevant = group[
            "course_id"
        ].tolist()

        recommendations = recommend(
            student_id,
            train,
            matrix,
            model,
            student_to_index,
            course_to_index,
            courses,
            TOP_K
        )

        if not recommendations:
            continue

        precision_scores.append(
            precision_at_k(
                recommendations,
                relevant,
                TOP_K
            )
        )

        recall_scores.append(
            recall_at_k(
                recommendations,
                relevant,
                TOP_K
            )
        )

        ndcg_scores.append(
            ndcg_at_k(
                recommendations,
                relevant,
                TOP_K
            )
        )

        students_evaluated += 1

        if counter % 500 == 0:

            print(
                f"Evaluated "
                f"{counter:,} students..."
            )

    return {
        "model": "User-Based CF",
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
    print(
        "USER-BASED COLLABORATIVE FILTERING"
    )
    print(
        "TRAIN / TEST EVALUATION"
    )
    print("=" * 60)

    df = load_data()

    print(
        f"\nInteractions: "
        f"{len(df):,}"
    )

    print(
        f"Students: "
        f"{df['id_student'].nunique():,}"
    )

    print(
        f"Courses: "
        f"{df['course_id'].nunique():,}"
    )

    train, test = create_split(
        df
    )

    print(
        f"\nTrain interactions: "
        f"{len(train):,}"
    )

    print(
        f"Test interactions: "
        f"{len(test):,}"
    )

    (
        matrix,
        student_to_index,
        course_to_index,
        courses
    ) = build_matrix(
        train
    )

    model = train_user_cf(
        matrix
    )

    result = evaluate(
        train,
        test,
        matrix,
        model,
        student_to_index,
        course_to_index,
        courses
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "USER-BASED CF RESULTS"
    )

    print(
        "=" * 60
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
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
        "user_cf_evaluation.csv"
    )

    pd.DataFrame(
        [result]
    ).to_csv(
        output_file,
        index=False
    )

    print(
        f"\nSaved to:\n{output_file}"
    )


if __name__ == "__main__":
    main()