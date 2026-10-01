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

TOP_N = 10

RANDOM_STATE = 42


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
    # USER MAPPING
    # --------------------------------------------------------

    students = sorted(
        interactions["id_student"].unique()
    )

    student_mapping = pd.DataFrame({
        "user_index": range(len(students)),
        "id_student": students
    })

    # --------------------------------------------------------
    # COURSE MAPPING
    # --------------------------------------------------------

    courses = sorted(
        interactions["course_id"].unique()
    )

    course_mapping = pd.DataFrame({
        "item_index": range(len(courses)),
        "course_id": courses
    })

    # --------------------------------------------------------
    # MERGE
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
        "ncf_student_index_mapping.csv",
        index=False
    )

    course_mapping.to_csv(
        PROCESSED_DIR /
        "ncf_course_index_mapping.csv",
        index=False
    )

    print("\nStudents:", len(student_mapping))
    print("Courses:", len(course_mapping))

    return (
        interactions,
        student_mapping,
        course_mapping
    )


# ============================================================
# ACTIVATION FUNCTIONS
# ============================================================

def relu(x):

    return np.maximum(
        0,
        x
    )


def relu_derivative(x):

    return (
        x > 0
    ).astype(np.float32)


def sigmoid(x):

    x = np.clip(
        x,
        -20,
        20
    )

    return 1.0 / (
        1.0 + np.exp(-x)
    )


# ============================================================
# NCF MODEL
# ============================================================

class NeuralCF:

    def __init__(
        self,
        n_users,
        n_items,
        embedding_size=16,
        hidden_size=16,
        random_state=42
    ):

        rng = np.random.default_rng(
            random_state
        )

        self.n_users = n_users
        self.n_items = n_items

        self.embedding_size = embedding_size
        self.hidden_size = hidden_size

        # ----------------------------------------------------
        # USER EMBEDDINGS
        # ----------------------------------------------------

        self.user_embeddings = (
            rng.normal(
                0,
                0.1,
                (
                    n_users,
                    embedding_size
                )
            ).astype(np.float32)
        )

        # ----------------------------------------------------
        # ITEM EMBEDDINGS
        # ----------------------------------------------------

        self.item_embeddings = (
            rng.normal(
                0,
                0.1,
                (
                    n_items,
                    embedding_size
                )
            ).astype(np.float32)
        )

        # ----------------------------------------------------
        # NEURAL NETWORK WEIGHTS
        # ----------------------------------------------------

        input_size = (
            embedding_size * 2
        )

        self.W1 = (
            rng.normal(
                0,
                0.1,
                (
                    input_size,
                    hidden_size
                )
            ).astype(np.float32)
        )

        self.b1 = np.zeros(
            hidden_size,
            dtype=np.float32
        )

        self.W2 = (
            rng.normal(
                0,
                0.1,
                (
                    hidden_size,
                    1
                )
            ).astype(np.float32)
        )

        self.b2 = np.zeros(
            1,
            dtype=np.float32
        )

    # ========================================================
    # FORWARD PASS
    # ========================================================

    def forward(
        self,
        user_index,
        item_index
    ):

        user_vector = (
            self.user_embeddings[
                user_index
            ]
        )

        item_vector = (
            self.item_embeddings[
                item_index
            ]
        )

        # Combine user and item embeddings
        x = np.concatenate([
            user_vector,
            item_vector
        ])

        # Hidden layer
        z1 = (
            x @ self.W1
            + self.b1
        )

        h1 = relu(z1)

        # Output
        z2 = (
            h1 @ self.W2
            + self.b2
        )

        prediction = sigmoid(
            z2[0]
        )

        return (
            prediction,
            x,
            z1,
            h1
        )

    # ========================================================
    # TRAIN ONE SAMPLE
    # ========================================================

    def train_sample(
        self,
        user_index,
        item_index,
        target
    ):

        (
            prediction,
            x,
            z1,
            h1
        ) = self.forward(
            user_index,
            item_index
        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        error = (
            prediction
            - target
        )

        # ----------------------------------------------------
        # OUTPUT LAYER GRADIENT
        # ----------------------------------------------------

        d_z2 = error

        d_W2 = (
            h1[:, None]
            * d_z2
        )

        d_b2 = d_z2

        # ----------------------------------------------------
        # HIDDEN LAYER
        # ----------------------------------------------------

        d_h1 = (
            self.W2[:, 0]
            * d_z2
        )

        d_z1 = (
            d_h1
            * relu_derivative(z1)
        )

        d_W1 = (
            x[:, None]
            * d_z1
        )

        d_b1 = d_z1

        # ----------------------------------------------------
        # INPUT GRADIENT
        # ----------------------------------------------------

        d_x = (
            self.W1
            @ d_z1
        )

        # ----------------------------------------------------
        # EMBEDDING GRADIENTS
        # ----------------------------------------------------

        d_user = d_x[
            :self.embedding_size
        ]

        d_item = d_x[
            self.embedding_size:
        ]

        # ----------------------------------------------------
        # UPDATE WEIGHTS
        # ----------------------------------------------------

        self.W2 -= (
            LEARNING_RATE
            * d_W2
        )

        self.b2 -= (
            LEARNING_RATE
            * d_b2
        )

        self.W1 -= (
            LEARNING_RATE
            * d_W1
        )

        self.b1 -= (
            LEARNING_RATE
            * d_b1
        )

        self.user_embeddings[
            user_index
        ] -= (
            LEARNING_RATE
            * d_user
        )

        self.item_embeddings[
            item_index
        ] -= (
            LEARNING_RATE
            * d_item
        )

        return prediction


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(
    model,
    interactions
):

    print("\nTraining NCF model...")

    rng = np.random.default_rng(
        RANDOM_STATE
    )

    # --------------------------------------------------------
    # NORMALIZE TARGET
    # --------------------------------------------------------

    interactions = interactions.copy()

    interactions["target"] = (
        interactions[
            "interaction_score"
        ]
        .clip(0, 1)
    )

    samples = interactions[
        [
            "user_index",
            "item_index",
            "target"
        ]
    ].values

    # --------------------------------------------------------
    # TRAINING
    # --------------------------------------------------------

    for epoch in range(
        1,
        EPOCHS + 1
    ):

        # Shuffle
        indices = rng.permutation(
            len(samples)
        )

        total_loss = 0.0

        for index in indices:

            user_index = int(
                samples[index][0]
            )

            item_index = int(
                samples[index][1]
            )

            target = float(
                samples[index][2]
            )

            prediction = (
                model.train_sample(
                    user_index,
                    item_index,
                    target
                )
            )

            loss = (
                prediction
                - target
            ) ** 2

            total_loss += loss

        average_loss = (
            total_loss
            / len(samples)
        )

        if (
            epoch == 1
            or epoch % 5 == 0
            or epoch == EPOCHS
        ):

            print(
                f"Epoch {epoch:02d}/{EPOCHS} "
                f"- Loss: "
                f"{average_loss:.6f}"
            )

    print("\nNCF training complete.")

    return model


# ============================================================
# RECOMMEND COURSES
# ============================================================

def recommend_for_user(
    model,
    user_index,
    interactions,
    student_mapping,
    course_mapping,
    top_n=10
):

    # --------------------------------------------------------
    # COURSES ALREADY SEEN
    # --------------------------------------------------------

    seen_courses = set(
        interactions[
            interactions["user_index"]
            == user_index
        ]["item_index"]
        .astype(int)
        .tolist()
    )

    predictions = []

    # --------------------------------------------------------
    # PREDICT EVERY COURSE
    # --------------------------------------------------------

    for item_index in range(
        len(course_mapping)
    ):

        if item_index in seen_courses:
            continue

        prediction, _, _, _ = (
            model.forward(
                user_index,
                item_index
            )
        )

        course_id = (
            course_mapping.iloc[
                item_index
            ]["course_id"]
        )

        student_id = (
            student_mapping.iloc[
                user_index
            ]["id_student"]
        )

        predictions.append({

            "id_student": int(
                student_id
            ),

            "user_index": user_index,

            "course_id": course_id,

            "item_index": item_index,

            "ncf_score": round(
                float(prediction),
                4
            )
        })

    result = pd.DataFrame(
        predictions
    )

    if result.empty:
        return result

    result = result.sort_values(
        "ncf_score",
        ascending=False
    )

    result = result.head(
        top_n
    ).copy()

    result["recommendation_rank"] = (
        range(
            1,
            len(result) + 1
        )
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 4 - STEP 4.5")
    print("NEURAL COLLABORATIVE FILTERING")
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
    # CREATE MODEL
    # --------------------------------------------------------

    model = NeuralCF(
        n_users=len(
            student_mapping
        ),
        n_items=len(
            course_mapping
        ),
        embedding_size=EMBEDDING_SIZE,
        hidden_size=HIDDEN_SIZE,
        random_state=RANDOM_STATE
    )

    print(
        "\nEmbedding size:",
        EMBEDDING_SIZE
    )

    print(
        "Hidden layer size:",
        HIDDEN_SIZE
    )

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model = train_model(
        model,
        interactions
    )

    # --------------------------------------------------------
    # SAMPLE USER
    # --------------------------------------------------------

    user_index = 0

    student_id = (
        student_mapping.iloc[
            user_index
        ]["id_student"]
    )

    print(
        "\nSample student ID:",
        student_id
    )

    # --------------------------------------------------------
    # RECOMMEND
    # --------------------------------------------------------

    result = recommend_for_user(
        model,
        user_index,
        interactions,
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
        "neural_cf_sample_recommendations.csv"
    )

    result.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP NCF RECOMMENDATIONS")
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
        "\nNEURAL COLLABORATIVE "
        "FILTERING COMPLETE."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()