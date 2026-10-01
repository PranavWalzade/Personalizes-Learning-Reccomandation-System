import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import RESULTS_DIR


# ============================================================
# FILES
# ============================================================

INPUT_FILE = (
    RESULTS_DIR /
    "deployment_recommendations.csv"
)

OUTPUT_FILE = (
    RESULTS_DIR /
    "deployment_validation.csv"
)


# ============================================================
# MAIN
# ============================================================

def validate_deployment_recommendations():

    print("=" * 70)
    print("STEP 4.16 - DEPLOYMENT RECOMMENDATION VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load file
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"File not found:\n{INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    print("\nLoaded recommendations:")
    print(f"Records: {len(data):,}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "id_student",
        "recommendation_rank",
        "course_id",
        "course_name",
        "branch",
        "semester",
        "category",
        "difficulty",
        "credits",
        "course_level",
        "hybrid_score",
        "recommendation_reasons",
        "why_recommended"
    ]

    print("\nChecking required columns...")

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        print("FAILED")
        print(
            f"Missing columns: {missing_columns}"
        )

        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print("PASSED")

    # --------------------------------------------------------
    # Validation results
    # --------------------------------------------------------

    validation_results = []

    def add_result(check, status, details):

        validation_results.append({
            "check": check,
            "status": status,
            "details": details
        })

    # --------------------------------------------------------
    # 1. Empty values
    # --------------------------------------------------------

    missing_values = int(
        data[required_columns]
        .isna()
        .sum()
        .sum()
    )

    if missing_values == 0:

        add_result(
            "Missing values",
            "PASS",
            "No missing values found"
        )

    else:

        add_result(
            "Missing values",
            "FAIL",
            f"{missing_values} missing cells found"
        )

    # --------------------------------------------------------
    # 2. Duplicate rows
    # --------------------------------------------------------

    duplicate_rows = int(
        data.duplicated().sum()
    )

    if duplicate_rows == 0:

        add_result(
            "Duplicate rows",
            "PASS",
            "No duplicate rows found"
        )

    else:

        add_result(
            "Duplicate rows",
            "FAIL",
            f"{duplicate_rows} duplicate rows found"
        )

    # --------------------------------------------------------
    # 3. Student coverage
    # --------------------------------------------------------

    student_counts = (
        data
        .groupby("id_student")
        .size()
    )

    students_with_10 = int(
        (student_counts == 10).sum()
    )

    students_less_than_10 = int(
        (student_counts < 10).sum()
    )

    students_more_than_10 = int(
        (student_counts > 10).sum()
    )

    total_students = int(
        data["id_student"].nunique()
    )

    if students_less_than_10 == 0:

        add_result(
            "Student recommendation coverage",
            "PASS",
            f"All {total_students:,} students have 10 recommendations"
        )

    else:

        add_result(
            "Student recommendation coverage",
            "FAIL",
            f"{students_less_than_10:,} students have fewer than 10 recommendations"
        )

    # --------------------------------------------------------
    # 4. Recommendation rank
    # --------------------------------------------------------

    invalid_rank_groups = 0

    for student_id, group in data.groupby(
        "id_student"
    ):

        ranks = sorted(
            group["recommendation_rank"]
            .astype(int)
            .tolist()
        )

        expected = list(
            range(
                1,
                len(ranks) + 1
            )
        )

        if ranks != expected:

            invalid_rank_groups += 1

    if invalid_rank_groups == 0:

        add_result(
            "Recommendation ranking",
            "PASS",
            "All student recommendation ranks are sequential"
        )

    else:

        add_result(
            "Recommendation ranking",
            "FAIL",
            f"{invalid_rank_groups} students have invalid ranks"
        )

    # --------------------------------------------------------
    # 5. Duplicate course per student
    # --------------------------------------------------------

    duplicate_student_courses = int(
        data.duplicated(
            subset=[
                "id_student",
                "course_id"
            ]
        ).sum()
    )

    if duplicate_student_courses == 0:

        add_result(
            "Duplicate course per student",
            "PASS",
            "No student receives the same course twice"
        )

    else:

        add_result(
            "Duplicate course per student",
            "FAIL",
            f"{duplicate_student_courses} duplicate student-course records"
        )

    # --------------------------------------------------------
    # 6. Score range
    # --------------------------------------------------------

    invalid_scores = int(
        (
            (data["hybrid_score"] < 0) |
            (data["hybrid_score"] > 1)
        ).sum()
    )

    if invalid_scores == 0:

        add_result(
            "Hybrid score range",
            "PASS",
            "All scores are between 0 and 1"
        )

    else:

        add_result(
            "Hybrid score range",
            "FAIL",
            f"{invalid_scores} invalid scores found"
        )

    # --------------------------------------------------------
    # 7. Score ordering
    # --------------------------------------------------------

    incorrectly_sorted = 0

    for student_id, group in data.groupby(
        "id_student"
    ):

        scores = group[
            "hybrid_score"
        ].tolist()

        if scores != sorted(
            scores,
            reverse=True
        ):

            incorrectly_sorted += 1

    if incorrectly_sorted == 0:

        add_result(
            "Score ordering",
            "PASS",
            "Recommendations are sorted by descending score"
        )

    else:

        add_result(
            "Score ordering",
            "FAIL",
            f"{incorrectly_sorted} students have incorrect score ordering"
        )

    # --------------------------------------------------------
    # 8. Recommendation explanations
    # --------------------------------------------------------

    empty_reasons = int(
        data[
            "why_recommended"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    if empty_reasons == 0:

        add_result(
            "Recommendation explanations",
            "PASS",
            "Every recommendation has an explanation"
        )

    else:

        add_result(
            "Recommendation explanations",
            "FAIL",
            f"{empty_reasons} recommendations have no explanation"
        )

    # --------------------------------------------------------
    # 9. Course coverage
    # --------------------------------------------------------

    unique_courses = int(
        data[
            "course_id"
        ].nunique()
    )

    add_result(
        "Course coverage",
        "INFO",
        f"{unique_courses} engineering courses appear in top-10 recommendations"
    )

    # --------------------------------------------------------
    # 10. Branch coverage
    # --------------------------------------------------------

    unique_branches = int(
        data[
            "branch"
        ].nunique()
    )

    add_result(
        "Branch coverage",
        "INFO",
        f"{unique_branches} engineering branches appear"
    )

    # --------------------------------------------------------
    # 11. Score statistics
    # --------------------------------------------------------

    min_score = float(
        data["hybrid_score"].min()
    )

    max_score = float(
        data["hybrid_score"].max()
    )

    average_score = float(
        data["hybrid_score"].mean()
    )

    add_result(
        "Score statistics",
        "INFO",
        (
            f"Min={min_score:.4f}, "
            f"Max={max_score:.4f}, "
            f"Average={average_score:.4f}"
        )
    )

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    validation_df = pd.DataFrame(
        validation_results
    )

    validation_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "VALIDATION RESULTS"
    )

    print(
        "=" * 70
    )

    for _, row in validation_df.iterrows():

        symbol = (
            "✓"
            if row["status"] == "PASS"
            else "!"
            if row["status"] == "INFO"
            else "✗"
        )

        print(
            f"{symbol} "
            f"{row['check']}: "
            f"{row['status']}"
        )

        print(
            f"   {row['details']}"
        )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    failed_checks = int(
        (
            validation_df[
                "status"
            ] == "FAIL"
        ).sum()
    )

    print(
        "\n" + "=" * 70
    )

    if failed_checks == 0:

        print(
            "FINAL STATUS: PASSED"
        )

        print(
            "\nDeployment recommendation file is ready."
        )

    else:

        print(
            "FINAL STATUS: FAILED"
        )

        print(
            f"\nFailed checks: {failed_checks}"
        )

    print(
        "\nValidation report saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "STEP 4.16 COMPLETED"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    validate_deployment_recommendations()