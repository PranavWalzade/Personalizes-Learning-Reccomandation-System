import sys
from pathlib import Path

import numpy as np
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

EMBEDDING_SIZE = 16
HIDDEN_SIZE = 16

EPOCHS = 30
LEARNING_RATE = 0.01

TOP_N = 5


# ============================================================
# ACTIVATION FUNCTIONS
# ============================================================

def sigmoid(x):
    x = np.clip(x, -50, 50)
    return 1 / (1 + np.exp(-x))


def relu(x):
    return np.maximum(0, x)


# ============================================================
# METRICS
# ============================================================

def precision_at_k(recommended, actual, k=5):

    recommended = recommended[:k]

    if len(recommended) == 0:
        return 0.0

    hits = len(
        set(recommended) & set(actual)
    )

    return hits / k


def recall_at_k(recommended, actual, k=5):

    recommended = recommended[:k]

    if len(actual) == 0:
        return 0.0

    hits = len(
        set(recommended) & set(actual)
    )

    return hits / len(actual)


def ndcg_at_k(recommended, actual, k=5):

    recommended = recommended[:k]

    if len(actual) == 0:
        return 0.0

    dcg = 0.0

    for rank, course in enumerate(recommended):

        if course in actual:

            dcg += 1 / np.log2(rank + 2)

    ideal_hits = min(
        len(actual),
        k
    )

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
print("NEURAL COLLABORATIVE FILTERING")
print("TRAIN / TEST EVALUATION")
print("=" * 60)

input_file = (
    PROCESSED_DIR /
    "oulad_ml_interactions.csv"
)

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

df["id_student"] = df[
    "id_student"
].astype(int)

print()
print(f"Interactions: {len(df):,}")
print(
    f"Students: "
    f"{df['id_student'].nunique():,}"
)
print(
    f"Courses: "
    f"{df['course_id'].nunique():,}"
)


# ============================================================
# REMOVE DUPLICATES
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

for student_id, group in df.groupby(
    "id_student"
):

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

    test_df = pd.DataFrame(
        test_rows
    )

else:

    test_df = pd.DataFrame(
        columns=df.columns
    )


print()
print(
    f"Training interactions: "
    f"{len(train_df):,}"
)

print(
    f"Testing interactions: "
    f"{len(test_df):,}"
)

print(
    f"Test students: "
    f"{test_df['id_student'].nunique():,}"
)


# ============================================================
# INDEX MAPPINGS
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
# CREATE TRAINING INTERACTIONS
# ============================================================

train_interactions = []

for row in train_df.itertuples(
    index=False
):

    user_index = student_to_index[
        row.id_student
    ]

    item_index = course_to_index[
        row.course_id
    ]

    train_interactions.append(
        (
            user_index,
            item_index,
            float(row.interaction_score)
        )
    )


# ============================================================
# INITIALIZE NCF PARAMETERS
# ============================================================

print()
print("Initializing NCF model...")

rng = np.random.default_rng(42)

num_users = len(students)
num_items = len(courses)

user_embeddings = (
    rng.normal(
        0,
        0.1,
        (num_users, EMBEDDING_SIZE)
    )
)

item_embeddings = (
    rng.normal(
        0,
        0.1,
        (num_items, EMBEDDING_SIZE)
    )
)

input_size = (
    EMBEDDING_SIZE * 2
)

hidden_weights = (
    rng.normal(
        0,
        0.1,
        (input_size, HIDDEN_SIZE)
    )
)

hidden_bias = np.zeros(
    HIDDEN_SIZE
)

output_weights = (
    rng.normal(
        0,
        0.1,
        HIDDEN_SIZE
    )
)

output_bias = 0.0


# ============================================================
# TRAIN NCF
# ============================================================

print()
print("Training Neural Collaborative Filtering...")

for epoch in range(EPOCHS):

    total_loss = 0.0

    rng.shuffle(train_interactions)

    for user_index, item_index, score in train_interactions:

        # ----------------------------------------------------
        # Normalize interaction score
        # ----------------------------------------------------

        target = np.clip(
            score,
            0.0,
            1.0
        )

        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        user_vector = (
            user_embeddings[user_index]
        )

        item_vector = (
            item_embeddings[item_index]
        )

        x = np.concatenate(
            [
                user_vector,
                item_vector
            ]
        )

        hidden_input = (
            x @ hidden_weights
            + hidden_bias
        )

        hidden = relu(
            hidden_input
        )

        output_input = (
            hidden @ output_weights
            + output_bias
        )

        prediction = sigmoid(
            output_input
        )

        # ----------------------------------------------------
        # Binary cross entropy
        # ----------------------------------------------------

        eps = 1e-8

        loss = -(
            target * np.log(
                prediction + eps
            )
            +
            (1 - target)
            * np.log(
                1 - prediction + eps
            )
        )

        total_loss += loss

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        d_output = (
            prediction - target
        )

        d_output_weights = (
            hidden * d_output
        )

        d_output_bias = d_output

        d_hidden = (
            output_weights * d_output
        )

        d_hidden_input = (
            d_hidden
            * (hidden_input > 0)
        )

        d_hidden_weights = np.outer(
            x,
            d_hidden_input
        )

        d_hidden_bias = (
            d_hidden_input
        )

        d_x = (
            hidden_weights
            @ d_hidden_input
        )

        d_user = d_x[
            :EMBEDDING_SIZE
        ]

        d_item = d_x[
            EMBEDDING_SIZE:
        ]

        # ----------------------------------------------------
        # Update parameters
        # ----------------------------------------------------

        user_embeddings[user_index] -= (
            LEARNING_RATE * d_user
        )

        item_embeddings[item_index] -= (
            LEARNING_RATE * d_item
        )

        hidden_weights -= (
            LEARNING_RATE
            * d_hidden_weights
        )

        hidden_bias -= (
            LEARNING_RATE
            * d_hidden_bias
        )

        output_weights -= (
            LEARNING_RATE
            * d_output_weights
        )

        output_bias -= (
            LEARNING_RATE
            * d_output_bias
        )

    average_loss = (
        total_loss
        / len(train_interactions)
    )

    if (
        epoch == 0
        or (epoch + 1) % 5 == 0
        or epoch == EPOCHS - 1
    ):

        print(
            f"Epoch {epoch + 1:02d}/{EPOCHS} "
            f"- Loss: {average_loss:.6f}"
        )


# ============================================================
# PREPARE TEST DATA
# ============================================================

test_by_student = (
    test_df
    .groupby("id_student")[
        "course_id"
    ]
    .apply(list)
    .to_dict()
)

train_by_student = (
    train_df
    .groupby("id_student")[
        "course_id"
    ]
    .apply(set)
    .to_dict()
)


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_score(
    user_index,
    item_index
):

    user_vector = (
        user_embeddings[user_index]
    )

    item_vector = (
        item_embeddings[item_index]
    )

    x = np.concatenate(
        [
            user_vector,
            item_vector
        ]
    )

    hidden_input = (
        x @ hidden_weights
        + hidden_bias
    )

    hidden = relu(
        hidden_input
    )

    output = (
        hidden @ output_weights
        + output_bias
    )

    return sigmoid(output)


# ============================================================
# EVALUATION
# ============================================================

print()
print("Evaluating Neural Collaborative Filtering...")

precision_scores = []
recall_scores = []
ndcg_scores = []

evaluated = 0

for student_id, actual_courses in test_by_student.items():

    if student_id not in student_to_index:
        continue

    user_index = student_to_index[
        student_id
    ]

    scores = np.zeros(
        num_items
    )

    # --------------------------------------------------------
    # Predict score for every course
    # --------------------------------------------------------

    for item_index in range(num_items):

        scores[item_index] = (
            predict_score(
                user_index,
                item_index
            )
        )

    # --------------------------------------------------------
    # Remove courses already seen
    # --------------------------------------------------------

    seen_courses = train_by_student.get(
        student_id,
        set()
    )

    for course in seen_courses:

        if course in course_to_index:

            item_index = course_to_index[
                course
            ]

            scores[item_index] = -np.inf

    # --------------------------------------------------------
    # Top recommendations
    # --------------------------------------------------------

    top_indices = np.argsort(
        scores
    )[::-1][:TOP_N]

    recommendations = [
        index_to_course[index]
        for index in top_indices
    ]

    # --------------------------------------------------------
    # Metrics
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
            f"Evaluated "
            f"{evaluated:,} students..."
        )


# ============================================================
# FINAL RESULTS
# ============================================================

precision = (
    np.mean(precision_scores)
    if precision_scores
    else 0.0
)

recall = (
    np.mean(recall_scores)
    if recall_scores
    else 0.0
)

ndcg = (
    np.mean(ndcg_scores)
    if ndcg_scores
    else 0.0
)


print()
print("=" * 60)
print("NEURAL COLLABORATIVE FILTERING RESULTS")
print("=" * 60)

print(
    "model: Neural Collaborative Filtering"
)

print(
    f"students_evaluated: {evaluated}"
)

print(
    f"precision_at_5: {precision}"
)

print(
    f"recall_at_5: {recall}"
)

print(
    f"ndcg_at_5: {ndcg}"
)


# ============================================================
# SAVE RESULTS
# ============================================================

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

result_file = (
    RESULTS_DIR /
    "neural_cf_evaluation.csv"
)

results = pd.DataFrame(
    [
        {
            "model":
                "Neural Collaborative Filtering",
            "students_evaluated":
                evaluated,
            "precision_at_5":
                precision,
            "recall_at_5":
                recall,
            "ndcg_at_5":
                ndcg
        }
    ]
)

results.to_csv(
    result_file,
    index=False
)

print()
print("Saved to:")
print(result_file)

print()
print("Step 4.10 completed.")