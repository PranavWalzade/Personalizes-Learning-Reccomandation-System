import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import RESULTS_DIR, REPORTS_DIR, PLOTS_DIR


# ============================================================
# INPUT FILES
# ============================================================

MODEL_FILES = {
    "Popularity Baseline":
        RESULTS_DIR / "recommendation_evaluation.csv",

    "User-Based CF":
        RESULTS_DIR / "user_cf_evaluation.csv",

    "Matrix Factorization":
        RESULTS_DIR / "matrix_factorization_evaluation.csv",

    "Neural Collaborative Filtering":
        RESULTS_DIR / "neural_cf_evaluation.csv",
}


# ============================================================
# OUTPUT FILES
# ============================================================

COMPARISON_FILE = (
    RESULTS_DIR /
    "model_comparison.csv"
)

REPORT_FILE = (
    REPORTS_DIR /
    "final_model_comparison_report.csv"
)

CHART_FILE = (
    PLOTS_DIR /
    "model_comparison_ndcg_at_5.png"
)


# ============================================================
# LOAD RESULTS
# ============================================================

def load_results():

    rows = []

    print("\nLoading model evaluation results...")

    for model_name, file_path in MODEL_FILES.items():

        print(
            f"Loading: {model_name}"
        )

        if not file_path.exists():

            print(
                f"WARNING: File not found: {file_path}"
            )

            continue

        data = pd.read_csv(
            file_path
        )

        if len(data) == 0:
            continue

        row = data.iloc[0].to_dict()

        row["model"] = model_name

        rows.append(row)

    if not rows:

        raise FileNotFoundError(
            "No model evaluation files were found."
        )

    return pd.DataFrame(rows)


# ============================================================
# COMPARE MODELS
# ============================================================

def create_comparison(data):

    required_columns = [
        "model",
        "students_evaluated",
        "precision_at_5",
        "recall_at_5",
        "ndcg_at_5",
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            f"Missing columns: {missing}"
        )

    comparison = data[
        required_columns
    ].copy()

    # --------------------------------------------------------
    # Sort by NDCG@5
    # --------------------------------------------------------

    comparison = comparison.sort_values(
        by="ndcg_at_5",
        ascending=False
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Assign ranking
    # --------------------------------------------------------

    comparison["rank"] = (
        comparison.index + 1
    )

    # --------------------------------------------------------
    # Round metrics
    # --------------------------------------------------------

    comparison["precision_at_5"] = (
        comparison["precision_at_5"]
        .round(6)
    )

    comparison["recall_at_5"] = (
        comparison["recall_at_5"]
        .round(6)
    )

    comparison["ndcg_at_5"] = (
        comparison["ndcg_at_5"]
        .round(6)
    )

    # Put rank first

    comparison = comparison[
        [
            "rank",
            "model",
            "students_evaluated",
            "precision_at_5",
            "recall_at_5",
            "ndcg_at_5",
        ]
    ]

    return comparison


# ============================================================
# SAVE REPORT
# ============================================================

def save_reports(comparison):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PLOTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    comparison.to_csv(
        COMPARISON_FILE,
        index=False
    )

    comparison.to_csv(
        REPORT_FILE,
        index=False
    )

    print(
        f"\nComparison saved to:\n"
        f"{COMPARISON_FILE}"
    )

    print(
        f"\nFinal report saved to:\n"
        f"{REPORT_FILE}"
    )


# ============================================================
# CREATE NDCG CHART
# ============================================================

def create_ndcg_chart(comparison):

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        comparison["model"],
        comparison["ndcg_at_5"]
    )

    plt.title(
        "Recommendation Model Comparison - NDCG@5"
    )

    plt.xlabel(
        "Recommendation Model"
    )

    plt.ylabel(
        "NDCG@5"
    )

    plt.xticks(
        rotation=20,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        CHART_FILE,
        dpi=300
    )

    plt.close()

    print(
        f"\nNDCG chart saved to:\n"
        f"{CHART_FILE}"
    )


# ============================================================
# DISPLAY FINAL RESULTS
# ============================================================

def display_results(comparison):

    print("\n" + "=" * 70)
    print("FINAL RECOMMENDATION MODEL COMPARISON")
    print("=" * 70)

    print(
        comparison.to_string(
            index=False
        )
    )

    best_model = comparison.iloc[0]

    print("\n" + "=" * 70)
    print("BEST MODEL")
    print("=" * 70)

    print(
        f"Model: {best_model['model']}"
    )

    print(
        f"Precision@5: "
        f"{best_model['precision_at_5']:.6f}"
    )

    print(
        f"Recall@5: "
        f"{best_model['recall_at_5']:.6f}"
    )

    print(
        f"NDCG@5: "
        f"{best_model['ndcg_at_5']:.6f}"
    )

    print(
        "\nSelection criterion: NDCG@5"
    )

    print(
        "\nNDCG@5 is used as the primary metric "
        "because it considers both relevance "
        "and ranking position."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("STEP 4.13 - FINAL MODEL COMPARISON")
    print("=" * 70)

    data = load_results()

    comparison = create_comparison(
        data
    )

    save_reports(
        comparison
    )

    create_ndcg_chart(
        comparison
    )

    display_results(
        comparison
    )

    print("\n" + "=" * 70)
    print("STEP 4.13 COMPLETED")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()