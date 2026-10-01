import sys
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    PROCESSED_DIR,
    ENGINEERING_COURSES_FILE,
)


# ============================================================
# LOAD ENGINEERING COURSES
# ============================================================

def load_courses():

    print("\nLoading engineering course dataset...")

    if not ENGINEERING_COURSES_FILE.exists():

        raise FileNotFoundError(
            f"Engineering course file not found:\n"
            f"{ENGINEERING_COURSES_FILE}"
        )

    courses = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    print(
        f"Courses loaded: {len(courses):,}"
    )

    return courses


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

def check_columns(courses):

    print("\nChecking course columns...")

    required_columns = [
        "course_id",
        "course_name",
        "branch",
        "category",
        "skills",
        "prerequisites",
        "difficulty",
        "credits",
        "semester",
    ]

    missing = [
        column
        for column in required_columns
        if column not in courses.columns
    ]

    if missing:

        print("\nMissing columns:")

        for column in missing:
            print(f"  - {column}")

        raise ValueError(
            "Engineering course dataset is missing "
            "required columns."
        )

    print("All required columns found.")


# ============================================================
# CLEAN COURSE DATA
# ============================================================

def clean_courses(courses):

    print("\nCleaning course data...")

    df = courses.copy()

    # --------------------------------------------------------
    # Remove duplicate courses
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["course_id"]
    )

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    text_columns = [
        "course_name",
        "branch",
        "category",
        "skills",
        "prerequisites",
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "difficulty",
        "credits",
        "semester",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Defaults
    df["difficulty"] = (
        df["difficulty"]
        .fillna(3)
        .clip(1, 5)
    )

    df["credits"] = (
        df["credits"]
        .fillna(df["credits"].median())
    )

    df["semester"] = (
        df["semester"]
        .fillna(1)
        .clip(1, 8)
    )

    return df


# ============================================================
# CREATE COURSE TEXT
# ============================================================

def create_course_text(courses):

    print("\nCreating combined course text...")

    df = courses.copy()

    # --------------------------------------------------------
    # Repeat important fields
    #
    # Repetition gives TF-IDF more importance to these
    # concepts.
    # --------------------------------------------------------

    df["course_text"] = (
        "course "
        + df["course_name"] + " "
        + "course "
        + df["course_name"] + " "

        + "branch "
        + df["branch"] + " "

        + "category "
        + df["category"] + " "

        + "skills "
        + df["skills"] + " "
        + df["skills"] + " "

        + "prerequisite "
        + df["prerequisites"]
    )

    df["course_text"] = (
        df["course_text"]
        .str.replace(
            r"[^a-zA-Z0-9+#.\- ]",
            " ",
            regex=True
        )
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    return df


# ============================================================
# TF-IDF FEATURES
# ============================================================

def create_tfidf_features(courses):

    print("\nCreating TF-IDF course features...")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_features=3000,
    )

    tfidf_matrix = vectorizer.fit_transform(
        courses["course_text"]
    )

    print(
        "TF-IDF matrix shape:",
        tfidf_matrix.shape
    )

    # --------------------------------------------------------
    # Save TF-IDF matrix
    # --------------------------------------------------------

    tfidf_file = (
        PROCESSED_DIR /
        "course_tfidf.npz"
    )

    from scipy.sparse import save_npz

    save_npz(
        tfidf_file,
        tfidf_matrix
    )

    print(
        "Saved TF-IDF matrix:",
        tfidf_file
    )

    # --------------------------------------------------------
    # Save vocabulary
    # --------------------------------------------------------

    vocabulary_file = (
        PROCESSED_DIR /
        "course_tfidf_vocabulary.csv"
    )

    vocabulary = pd.DataFrame({
        "term": vectorizer.get_feature_names_out()
    })

    vocabulary.to_csv(
        vocabulary_file,
        index=False
    )

    print(
        "Saved vocabulary:",
        vocabulary_file
    )

    return tfidf_matrix, vectorizer


# ============================================================
# NUMERIC FEATURES
# ============================================================

def create_numeric_features(courses):

    print("\nCreating numeric course features...")

    df = courses.copy()

    scaler = MinMaxScaler()

    numeric_columns = [
        "difficulty",
        "credits",
        "semester",
    ]

    numeric_matrix = scaler.fit_transform(
        df[numeric_columns]
    )

    numeric_features = pd.DataFrame(
        numeric_matrix,
        columns=[
            "difficulty_norm",
            "credits_norm",
            "semester_norm",
        ]
    )

    numeric_features.index = df.index

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    numeric_file = (
        PROCESSED_DIR /
        "course_numeric_features.csv"
    )

    numeric_features.to_csv(
        numeric_file,
        index=False
    )

    print(
        "Saved:",
        numeric_file
    )

    return numeric_features


# ============================================================
# CATEGORICAL FEATURES
# ============================================================

def create_categorical_features(courses):

    print("\nCreating categorical features...")

    df = courses.copy()

    # One-hot encode
    categorical = pd.get_dummies(
        df[
            [
                "branch",
                "category",
            ]
        ],
        prefix=[
            "branch",
            "category",
        ],
        dtype=int
    )

    categorical_file = (
        PROCESSED_DIR /
        "course_categorical_features.csv"
    )

    categorical.to_csv(
        categorical_file,
        index=False
    )

    print(
        "Saved:",
        categorical_file
    )

    return categorical


# ============================================================
# COURSE SKILL FEATURES
# ============================================================

def create_skill_features(courses):

    print("\nCreating skill features...")

    df = courses.copy()

    # --------------------------------------------------------
    # Collect all skills
    # --------------------------------------------------------

    skill_set = set()

    for value in df["skills"]:

        skills = [
            skill.strip().lower()
            for skill in str(value).split(";")
            if skill.strip()
        ]

        skill_set.update(skills)

    skills = sorted(skill_set)

    print(
        "Unique engineering skills:",
        len(skills)
    )

    # --------------------------------------------------------
    # Create binary skill matrix
    # --------------------------------------------------------

    skill_matrix = np.zeros(
        (
            len(df),
            len(skills)
        ),
        dtype=np.int8
    )

    skill_index = {
        skill: index
        for index, skill in enumerate(skills)
    }

    for row_index, value in enumerate(
        df["skills"]
    ):

        current_skills = [
            skill.strip().lower()
            for skill in str(value).split(";")
            if skill.strip()
        ]

        for skill in current_skills:

            if skill in skill_index:

                skill_matrix[
                    row_index,
                    skill_index[skill]
                ] = 1

    skill_columns = [
        f"skill_{skill.replace(' ', '_')}"
        for skill in skills
    ]

    skill_features = pd.DataFrame(
        skill_matrix,
        columns=skill_columns
    )

    skill_file = (
        PROCESSED_DIR /
        "course_skill_features.csv"
    )

    skill_features.to_csv(
        skill_file,
        index=False
    )

    print(
        "Saved:",
        skill_file
    )

    # Save skill dictionary
    skill_dictionary = pd.DataFrame({
        "skill": skills,
        "feature": skill_columns,
    })

    skill_dictionary.to_csv(
        PROCESSED_DIR /
        "skill_dictionary.csv",
        index=False
    )

    return skill_features


# ============================================================
# FINAL COURSE FEATURE TABLE
# ============================================================

def create_course_feature_table(
    courses,
    numeric_features,
    categorical_features,
    skill_features,
):

    print("\nCreating final course feature table...")

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = courses[
        [
            "course_id",
            "course_name",
            "branch",
            "category",
            "skills",
            "prerequisites",
            "difficulty",
            "credits",
            "semester",
            "course_text",
        ]
    ].reset_index(drop=True)

    # --------------------------------------------------------
    # Combine features
    # --------------------------------------------------------

    features = pd.concat(
        [
            numeric_features.reset_index(drop=True),
            categorical_features.reset_index(drop=True),
            skill_features.reset_index(drop=True),
        ],
        axis=1
    )

    # --------------------------------------------------------
    # Final dataset
    # --------------------------------------------------------

    final_df = pd.concat(
        [
            metadata,
            features,
        ],
        axis=1
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = (
        PROCESSED_DIR /
        "course_features.csv"
    )

    final_df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nFinal course feature dataset:"
    )

    print(
        "Rows:",
        len(final_df)
    )

    print(
        "Columns:",
        len(final_df.columns)
    )

    print(
        "Saved:",
        output_file
    )

    return final_df


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.2 "
        "ENGINEERING COURSE FEATURES"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    courses = load_courses()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    check_columns(courses)

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    courses = clean_courses(
        courses
    )

    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    courses = create_course_text(
        courses
    )

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    tfidf_matrix, vectorizer = (
        create_tfidf_features(
            courses
        )
    )

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    numeric_features = (
        create_numeric_features(
            courses
        )
    )

    # --------------------------------------------------------
    # Categorical
    # --------------------------------------------------------

    categorical_features = (
        create_categorical_features(
            courses
        )
    )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    skill_features = (
        create_skill_features(
            courses
        )
    )

    # --------------------------------------------------------
    # Final feature table
    # --------------------------------------------------------

    final_df = create_course_feature_table(
        courses,
        numeric_features,
        categorical_features,
        skill_features,
    )

    print("\n" + "=" * 70)
    print(
        "PHASE 3 — STEP 3.2 COMPLETE"
    )
    print("=" * 70)

    print(
        "\nCourse feature matrix ready for ML."
    )


if __name__ == "__main__":
    main()