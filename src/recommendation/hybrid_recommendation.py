import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    PROCESSED_DIR,
    RESULTS_DIR,
)


# ============================================================
# SETTINGS
# ============================================================

TOP_N = 10

# Weights of different recommendation methods
CONTENT_WEIGHT = 0.30
CF_WEIGHT = 0.20
MF_WEIGHT = 0.20
NCF_WEIGHT = 0.20
POPULARITY_WEIGHT = 0.10


# ============================================================
# LOAD ENGINEERING COURSES
# ============================================================

def load_engineering_courses():

    path = (
        PROCESSED_DIR /
        "engineering_candidate_features.csv"
    )

    df = pd.read_csv(path)

    print(
        "\nEngineering candidate data:",
        df.shape
    )

    return df


# ============================================================
# LOAD CONTENT RECOMMENDATIONS
# ============================================================

def load_content_recommendations():

    path = (
        RESULTS_DIR /
        "content_based_sample_recommendations.csv"
    )

    if not path.exists():

        print(
            "\nContent-based result not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(path)

    return df


# ============================================================
# LOAD COLLABORATIVE FILTERING
# ============================================================

def load_cf_recommendations():

    path = (
        RESULTS_DIR /
        "user_based_cf_sample_recommendations.csv"
    )

    if not path.exists():

        print(
            "\nUser-based CF result not found."
        )

        return pd.DataFrame()

    return pd.read_csv(path)


# ============================================================
# LOAD MATRIX FACTORIZATION
# ============================================================

def load_mf_recommendations():

    path = (
        RESULTS_DIR /
        "matrix_factorization_sample_recommendations.csv"
    )

    if not path.exists():

        print(
            "\nMatrix Factorization result not found."
        )

        return pd.DataFrame()

    return pd.read_csv(path)


# ============================================================
# LOAD NCF
# ============================================================

def load_ncf_recommendations():

    path = (
        RESULTS_DIR /
        "neural_cf_sample_recommendations.csv"
    )

    if not path.exists():

        print(
            "\nNCF result not found."
        )

        return pd.DataFrame()

    return pd.read_csv(path)


# ============================================================
# NORMALIZE SCORE
# ============================================================

def normalize_score(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            np.ones(len(series)),
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


# ============================================================
# BUILD HYBRID DATA
# ============================================================

def build_hybrid_scores(
    candidate_courses,
    content,
    cf,
    mf,
    ncf
):

    # --------------------------------------------------------
    # USE ALL ENGINEERING COURSES AS BASE
    # --------------------------------------------------------

    courses = candidate_courses.copy()

    # Make sure course_id is text
    courses["course_id"] = (
        courses["course_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # CONTENT SCORE
    # --------------------------------------------------------

    if not content.empty:

        content_small = content[
            [
                "course_id",
                "recommendation_score"
            ]
        ].copy()

        content_small = (
            content_small
            .rename(
                columns={
                    "recommendation_score":
                        "content_score"
                }
            )
        )

        courses = courses.merge(
            content_small,
            on="course_id",
            how="left"
        )

    else:

        courses["content_score"] = 0

    # --------------------------------------------------------
    # CF SCORE
    # --------------------------------------------------------

    if not cf.empty:

        cf_small = cf[
            [
                "course_id",
                "collaborative_score"
            ]
        ].copy()

        cf_small = (
            cf_small
            .rename(
                columns={
                    "collaborative_score":
                        "cf_score"
                }
            )
        )

        courses = courses.merge(
            cf_small,
            on="course_id",
            how="left"
        )

    else:

        courses["cf_score"] = 0

    # --------------------------------------------------------
    # MATRIX FACTORIZATION
    # --------------------------------------------------------

    if not mf.empty:

        mf_small = mf[
            [
                "course_id",
                "predicted_score"
            ]
        ].copy()

        mf_small = (
            mf_small
            .rename(
                columns={
                    "predicted_score":
                        "mf_score"
                }
            )
        )

        courses = courses.merge(
            mf_small,
            on="course_id",
            how="left"
        )

    else:

        courses["mf_score"] = 0

    # --------------------------------------------------------
    # NCF
    # --------------------------------------------------------

    if not ncf.empty:

        ncf_small = ncf[
            [
                "course_id",
                "ncf_score"
            ]
        ].copy()

        courses = courses.merge(
            ncf_small,
            on="course_id",
            how="left"
        )

    else:

        courses["ncf_score"] = 0

    # --------------------------------------------------------
    # FILL MISSING
    # --------------------------------------------------------

    score_columns = [
        "content_score",
        "cf_score",
        "mf_score",
        "ncf_score"
    ]

    for column in score_columns:

        courses[column] = (
            pd.to_numeric(
                courses[column],
                errors="coerce"
            )
            .fillna(0)
        )

    # --------------------------------------------------------
    # NORMALIZE EACH SCORE
    # --------------------------------------------------------

    courses["content_normalized"] = (
        normalize_score(
            courses["content_score"]
        )
    )

    courses["cf_normalized"] = (
        normalize_score(
            courses["cf_score"]
        )
    )

    courses["mf_normalized"] = (
        normalize_score(
            courses["mf_score"]
        )
    )

    courses["ncf_normalized"] = (
        normalize_score(
            courses["ncf_score"]
        )
    )

    # --------------------------------------------------------
    # POPULARITY
    # --------------------------------------------------------

    if "compatibility_score" in courses.columns:

        courses["popularity_normalized"] = (
            normalize_score(
                courses["compatibility_score"]
            )
        )

    else:

        courses["popularity_normalized"] = 0

    # --------------------------------------------------------
    # HYBRID SCORE
    # --------------------------------------------------------

    courses["hybrid_score"] = (

        CONTENT_WEIGHT
        * courses["content_normalized"]

        + CF_WEIGHT
        * courses["cf_normalized"]

        + MF_WEIGHT
        * courses["mf_normalized"]

        + NCF_WEIGHT
        * courses["ncf_normalized"]

        + POPULARITY_WEIGHT
        * courses["popularity_normalized"]
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    courses = courses.sort_values(
        "hybrid_score",
        ascending=False
    ).reset_index(
        drop=True
    )

    courses["recommendation_rank"] = (
        range(
            1,
            len(courses) + 1
        )
    )

    return courses


# ============================================================
# CREATE EXPLANATION
# ============================================================

def create_reason(row):

    reasons = []

    if row["content_normalized"] >= 0.70:

        reasons.append(
            "strong content match"
        )

    if row["cf_normalized"] >= 0.70:

        reasons.append(
            "similar students showed interest"
        )

    if row["mf_normalized"] >= 0.70:

        reasons.append(
            "strong latent preference score"
        )

    if row["ncf_normalized"] >= 0.70:

        reasons.append(
            "neural preference model predicts a good match"
        )

    if row["popularity_normalized"] >= 0.70:

        reasons.append(
            "good student-profile compatibility"
        )

    if not reasons:

        reasons.append(
            "overall hybrid profile match"
        )

    return "; ".join(reasons)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 4 - STEP 4.6")
    print("HYBRID RECOMMENDATION ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    candidates = (
        load_engineering_courses()
    )

    content = (
        load_content_recommendations()
    )

    cf = (
        load_cf_recommendations()
    )

    mf = (
        load_mf_recommendations()
    )

    ncf = (
        load_ncf_recommendations()
    )

    # --------------------------------------------------------
    # BUILD HYBRID
    # --------------------------------------------------------

    result = build_hybrid_scores(
        candidates,
        content,
        cf,
        mf,
        ncf
    )

    # --------------------------------------------------------
    # STUDENT ID
    # --------------------------------------------------------

    if "id_student" in result.columns:

        student_id = result.iloc[
            0
        ]["id_student"]

    else:

        student_id = 0

    result["id_student"] = student_id

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    result["why_recommended"] = (
        result.apply(
            create_reason,
            axis=1
        )
    )

    # --------------------------------------------------------
    # TOP N
    # --------------------------------------------------------

    final_result = result.head(
        TOP_N
    ).copy()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        RESULTS_DIR /
        "hybrid_sample_recommendations.csv"
    )

    final_result.to_csv(
        output_path,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL HYBRID RECOMMENDATIONS")
    print("=" * 70)

    display_columns = [
        "recommendation_rank",
        "course_id",
        "course_name",
        "branch",
        "category",
        "course_level",
        "difficulty",
        "hybrid_score",
        "why_recommended"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in final_result.columns
    ]

    print(
        final_result[
            available_columns
        ].to_string(
            index=False
        )
    )

    print("\nSaved:")
    print(output_path)

    print(
        "\nHYBRID RECOMMENDATION "
        "ENGINE COMPLETE."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()