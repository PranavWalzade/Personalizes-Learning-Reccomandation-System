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
TOP_N = 5


# ============================================================
# METRIC FUNCTIONS
# ============================================================

def precision_at_k(recommended, actual, k=5):
    recommended = recommended[:k]

    if len(recommended) == 0:
        return 0.0

    hits = len(set(recommended) & set(actual))

    return hits / k


def recall_at_k(recommended, actual, k=5):
    recommended = recommended[:k]

    if len(actual) == 0:
        return 0.0

    hits = len(set(recommended) & set(actual))

    return hits / len(actual)


def ndcg_at_k(recommended, actual, k=5):
    recommended = recommended[:k]

    if len(actual) == 0:
        return 0.0

    dcg = 0.0

    for rank, course in enumerate(recommended):
        if course in actual:
            dcg += 1 / np.log2(rank + 2)

    ideal_hits = min(len(actual), k)

    idcg = sum(
        1 / np.log2(rank + 2)
        for rank in range(ideal_hits)
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("MATRIX FACTORIZATION")
print("TRAIN / TEST EVALUATION")
print("=" * 60)

input_file = PROCESSED_DIR / "oulad_ml_interactions.csv"

print()
print("Loading:")
print(input_file)

df = pd.read_csv(input_file)

df["id_student"] = pd.to_numeric(
    df["id_student"],
    errors="coerce"
)

df["course_id"] = df["course_id"].astype(str)

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

df["id_student"] = df["id_student"].astype(int)

print()
print(f"Interactions: {len(df):,}")
print(f"Students: {df['id_student'].nunique():,}")
print(f"Courses: {df['course_id'].nunique():,}")


# ============================================================
# REMOVE DUPLICATE STUDENT-COURSE RECORDS
# ============================================================

df = (
    df.groupby(
        ["id_student", "course_id"],
        as_index=False
    )["interaction_score"]
    .mean()
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print()
print("Creating per-student train/test split...")

train_rows = []
test_rows = []

for student_id, group in df.groupby("id_student"):

    group = group.sort_values(
        "interaction_score",
        ascending=False
    )

    if len(group) >= 2:

        test_rows.append(
            group.iloc[0]
        )

        train_rows.append(
            group.iloc[1:]
        )

    else:

        train_rows.append(group)


train_df = pd.concat(
    train_rows,
    ignore_index=True
)

if test_rows:
    test_df = pd.DataFrame(test_rows)
else:
    test_df = pd.DataFrame(
        columns=df.columns
    )


print()
print(f"Training interactions: {len(train_df):,}")
print(f"Testing interactions: {len(test_df):,}")
print(
    f"Test students: "
    f"{test_df['id_student'].nunique():,}"
)


# ============================================================
# CREATE INDEX MAPPINGS
# ============================================================

students = sorted(
    train_df["id_student"].unique()
)

courses = sorted(
    train_df["course_id"].unique()
)

student_to_index = {
    student: index
    for index, student in enumerate(students)
}

course_to_index = {
    course: index
    for index, course in enumerate(courses)
}

index_to_course = {
    index: course
    for course, index in course_to_index.items()
}


# ============================================================
# CREATE USER-COURSE MATRIX
# ============================================================

print()
print("Creating user-course matrix...")

matrix = np.zeros(
    (len(students), len(courses)),
    dtype=np.float32
)

for row in train_df.itertuples(index=False):

    user_index = student_to_index[row.id_student]
    item_index = course_to_index[row.course_id]

    matrix[user_index, item_index] = (
        row.interaction_score
    )


print(
    f"Matrix shape: {matrix.shape}"
)


# ============================================================
# TRAIN MATRIX FACTORIZATION
# ============================================================

print()
print("Training Matrix Factorization...")

components = min(
    N_COMPONENTS,
    min(matrix.shape) - 1
)

svd = TruncatedSVD(
    n_components=components,
    random_state=42
)

user_latent = svd.fit_transform(matrix)

item_latent = svd.components_.T


print(
    f"Latent dimensions: {components}"
)

print(
    "Explained variance ratio:",
    round(
        svd.explained_variance_ratio_.sum(),
        4
    )
)


# ============================================================
# EVALUATION
# ============================================================

print()
print("Evaluating Matrix Factorization...")

test_by_student = (
    test_df
    .groupby("id_student")["course_id"]
    .apply(list)
    .to_dict()
)

train_by_student = (
    train_df
    .groupby("id_student")["course_id"]
    .apply(set)
    .to_dict()
)


precision_scores = []
recall_scores = []
ndcg_scores = []

evaluated = 0

for student_id, actual_courses in test_by_student.items():

    if student_id not in student_to_index:
        continue

    user_index = student_to_index[student_id]

    # --------------------------------------------------------
    # Calculate predicted scores
    # --------------------------------------------------------

    scores = (
        user_latent[user_index]
        @ item_latent.T
    )

    # --------------------------------------------------------
    # Remove courses already seen during training
    # --------------------------------------------------------

    seen_courses = train_by_student.get(
        student_id,
        set()
    )

    for course in seen_courses:

        if course in course_to_index:

            item_index = course_to_index[course]

            scores[item_index] = -np.inf

    # --------------------------------------------------------
    # Get top recommendations
    # --------------------------------------------------------

    top_indices = np.argsort(
        scores
    )[::-1][:TOP_N]

    recommendations = [
        index_to_course[index]
        for index in top_indices
    ]

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    precision_scores.append(
        precision_at_k(
            recommendations,
            actual_courses,
            TOP_N
        )
    )

    recall_scores.append(
        recall_at_k(
            recommendations,
            actual_courses,
            TOP_N
        )
    )

    ndcg_scores.append(
        ndcg_at_k(
            recommendations,
            actual_courses,
            TOP_N
        )
    )

    evaluated += 1

    if evaluated % 500 == 0:

        print(
            f"Evaluated {evaluated:,} students..."
        )


# ============================================================
# FINAL RESULTS
# ============================================================

precision = np.mean(
    precision_scores
) if precision_scores else 0

recall = np.mean(
    recall_scores
) if recall_scores else 0

ndcg = np.mean(
    ndcg_scores
) if ndcg_scores else 0


print()
print("=" * 60)
print("MATRIX FACTORIZATION RESULTS")
print("=" * 60)

print(f"model: Matrix Factorization")
print(f"students_evaluated: {evaluated}")
print(f"precision_at_5: {precision}")
print(f"recall_at_5: {recall}")
print(f"ndcg_at_5: {ndcg}")


# ============================================================
# SAVE RESULTS
# ============================================================

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

result_file = (
    RESULTS_DIR /
    "matrix_factorization_evaluation.csv"
)

results = pd.DataFrame(
    [{
        "model": "Matrix Factorization",
        "students_evaluated": evaluated,
        "precision_at_5": precision,
        "recall_at_5": recall,
        "ndcg_at_5": ndcg
    }]
)

results.to_csv(
    result_file,
    index=False
)

print()
print("Saved to:")
print(result_file)

print()
print("Step 4.9 completed.")