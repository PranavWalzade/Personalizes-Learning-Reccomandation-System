import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import json


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    RESULTS_DIR,
    REPORTS_DIR,
    MODELS_DIR,
    PROCESSED_DIR,
)


# ============================================================
# FILES
# ============================================================

COMPARISON_FILE = (
    RESULTS_DIR /
    "model_comparison.csv"
)

STUDENT_FEATURE_FILE = (
    PROCESSED_DIR /
    "student_features.csv"
)

ENGINEERING_COURSE_FILE = (
    PROCESSED_DIR /
    "course_features.csv"
)

OULAD_INTERACTION_FILE = (
    PROCESSED_DIR /
    "oulad_ml_interactions.csv"
)

MANIFEST_FILE = (
    MODELS_DIR /
    "model_manifest.json"
)


# ============================================================
# CREATE MANIFEST
# ============================================================

def create_manifest():

    print("=" * 70)
    print("STEP 4.14 - CREATE MODEL MANIFEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Check comparison file
    # --------------------------------------------------------

    if not COMPARISON_FILE.exists():

        raise FileNotFoundError(
            f"Missing model comparison file:\n"
            f"{COMPARISON_FILE}"
        )

    comparison = pd.read_csv(
        COMPARISON_FILE
    )

    if comparison.empty:

        raise ValueError(
            "Model comparison file is empty."
        )

    # --------------------------------------------------------
    # Best model
    # --------------------------------------------------------

    best_model = comparison.iloc[0]

    # --------------------------------------------------------
    # Dataset statistics
    # --------------------------------------------------------

    student_count = None
    engineering_course_count = None
    interaction_count = None

    if STUDENT_FEATURE_FILE.exists():

        students = pd.read_csv(
            STUDENT_FEATURE_FILE,
            usecols=["id_student"]
        )

        student_count = (
            students["id_student"]
            .nunique()
        )

    if ENGINEERING_COURSE_FILE.exists():

        courses = pd.read_csv(
            ENGINEERING_COURSE_FILE,
            usecols=["course_id"]
        )

        engineering_course_count = (
            courses["course_id"]
            .nunique()
        )

    if OULAD_INTERACTION_FILE.exists():

        interactions = pd.read_csv(
            OULAD_INTERACTION_FILE,
            usecols=["id_student", "course_id"]
        )

        interaction_count = len(
            interactions
        )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {

        "project": {
            "name":
                "Personalized Learning Recommendation System",

            "version":
                "1.0",

            "created_at":
                datetime.now().isoformat()
        },

        "recommendation": {

            "primary_metric":
                "NDCG@5",

            "best_model":
                str(best_model["model"]),

            "selection_method":
                "Highest NDCG@5"
        },

        "best_model_metrics": {

            "precision_at_5":
                float(best_model["precision_at_5"]),

            "recall_at_5":
                float(best_model["recall_at_5"]),

            "ndcg_at_5":
                float(best_model["ndcg_at_5"]),

            "students_evaluated":
                int(best_model["students_evaluated"])
        },

        "benchmark": {

            "dataset":
                "OULAD",

            "engineering_catalog":
                "Engineering Courses Extended",

            "student_count":
                student_count,

            "engineering_course_count":
                engineering_course_count,

            "interaction_count":
                interaction_count
        },

        "models_evaluated": {

            "Popularity Baseline": {
                "precision_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Popularity Baseline",
                            "precision_at_5"
                        ].iloc[0]
                    ),

                "recall_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Popularity Baseline",
                            "recall_at_5"
                        ].iloc[0]
                    ),

                "ndcg_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Popularity Baseline",
                            "ndcg_at_5"
                        ].iloc[0]
                    )
            },

            "User-Based CF": {
                "precision_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "User-Based CF",
                            "precision_at_5"
                        ].iloc[0]
                    ),

                "recall_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "User-Based CF",
                            "recall_at_5"
                        ].iloc[0]
                    ),

                "ndcg_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "User-Based CF",
                            "ndcg_at_5"
                        ].iloc[0]
                    )
            },

            "Matrix Factorization": {
                "precision_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Matrix Factorization",
                            "precision_at_5"
                        ].iloc[0]
                    ),

                "recall_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Matrix Factorization",
                            "recall_at_5"
                        ].iloc[0]
                    ),

                "ndcg_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Matrix Factorization",
                            "ndcg_at_5"
                        ].iloc[0]
                    )
            },

            "Neural Collaborative Filtering": {
                "precision_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Neural Collaborative Filtering",
                            "precision_at_5"
                        ].iloc[0]
                    ),

                "recall_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Neural Collaborative Filtering",
                            "recall_at_5"
                        ].iloc[0]
                    ),

                "ndcg_at_5":
                    float(
                        comparison.loc[
                            comparison["model"]
                            == "Neural Collaborative Filtering",
                            "ndcg_at_5"
                        ].iloc[0]
                    )
            }
        },

        "architecture": {

            "offline_benchmark":
                "OULAD student-course interactions",

            "engineering_recommendation":
                "Hybrid engineering course ranking",

            "content_component":
                "TF-IDF course content",

            "compatibility_component":
                "Student readiness and academic profile",

            "primary_deployment_catalog":
                "155 engineering courses"
        },

        "important_notes": [

            "OULAD course IDs are not mapped directly to engineering course IDs.",

            "Engineering recommendations use student profile compatibility and course metadata.",

            "OULAD evaluation is used as an offline recommendation benchmark.",

            "Final web recommendations should collect branch, interests, skills and preferences.",

            "Final engineering recommendation quality should be evaluated after collecting real engineering-student interactions."
        ]
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\nModel package information:")
    print(
        f"Best Model: "
        f"{manifest['recommendation']['best_model']}"
    )

    print(
        f"NDCG@5: "
        f"{manifest['best_model_metrics']['ndcg_at_5']:.6f}"
    )

    print(
        f"Precision@5: "
        f"{manifest['best_model_metrics']['precision_at_5']:.6f}"
    )

    print(
        f"Recall@5: "
        f"{manifest['best_model_metrics']['recall_at_5']:.6f}"
    )

    print(
        f"OULAD Students: "
        f"{student_count}"
    )

    print(
        f"Engineering Courses: "
        f"{engineering_course_count}"
    )

    print(
        f"\nManifest saved to:\n"
        f"{MANIFEST_FILE}"
    )

    print("\n" + "=" * 70)
    print("STEP 4.14 COMPLETED")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_manifest()