import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATH SETUP
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = SRC_DIR.parent

sys.path.insert(0, str(SRC_DIR))

from config import PROCESSED_DIR, REPORTS_DIR, PLOTS_DIR


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_processed_data():

    print("\nLoading processed datasets...")

    students = pd.read_csv(
        PROCESSED_DIR / "clean_students.csv"
    )

    courses = pd.read_csv(
        PROCESSED_DIR / "clean_courses.csv"
    )

    assessments = pd.read_csv(
        PROCESSED_DIR / "clean_assessments.csv"
    )

    student_profile = pd.read_csv(
        PROCESSED_DIR / "student_profile.csv"
    )

    course_profile = pd.read_csv(
        PROCESSED_DIR / "course_profile.csv"
    )

    print("Processed datasets loaded.")

    return (
        students,
        courses,
        assessments,
        student_profile,
        course_profile,
    )


# ============================================================
# DATASET SUMMARY
# ============================================================

def create_dataset_report(
    students,
    courses,
    assessments,
    student_profile,
    course_profile,
):

    print("\nCreating dataset report...")

    rows = []

    datasets = {
        "students": students,
        "courses": courses,
        "assessments": assessments,
        "student_profile": student_profile,
        "course_profile": course_profile,
    }

    for name, df in datasets.items():

        rows.append({
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        })

    report = pd.DataFrame(rows)

    report.to_csv(
        REPORTS_DIR / "phase2_dataset_report.csv",
        index=False
    )

    print(
        "Saved:",
        REPORTS_DIR / "phase2_dataset_report.csv"
    )


# ============================================================
# STUDENT PERFORMANCE REPORT
# ============================================================

def create_student_performance_report(student_profile):

    print("\nCreating student performance report...")

    df = student_profile.copy()

    performance = pd.DataFrame({
        "metric": [
            "Average Score",
            "Pass Rate",
            "Average Assessments Completed",
            "Average Maximum Score",
            "Average Learning Score",
        ],
        "value": [
            df["average_score"].mean(),
            df["pass_rate"].mean() * 100,
            df["assessments_completed"].mean(),
            df["maximum_score"].mean(),
            df["overall_learning_score"].mean() * 100,
        ]
    })

    performance.to_csv(
        REPORTS_DIR / "student_performance_report.csv",
        index=False
    )

    print(
        "Saved:",
        REPORTS_DIR / "student_performance_report.csv"
    )


# ============================================================
# COURSE ACTIVITY REPORT
# ============================================================

def create_course_activity_report(course_profile):

    print("\nCreating course activity report...")

    df = course_profile.copy()

    report = (
        df.groupby("course_id")
        .agg(
            total_clicks=("total_clicks", "sum"),
            interaction_records=("interaction_records", "sum"),
            unique_resources=("unique_resources", "sum"),
            active_days=("active_days", "max"),
        )
        .reset_index()
    )

    report = report.sort_values(
        "total_clicks",
        ascending=False
    )

    report.to_csv(
        REPORTS_DIR / "course_activity_report.csv",
        index=False
    )

    print(
        "Saved:",
        REPORTS_DIR / "course_activity_report.csv"
    )


# ============================================================
# FINAL RESULT DISTRIBUTION
# ============================================================

def plot_final_result_distribution(students):

    print("\nCreating final result distribution...")

    counts = (
        students["final_result"]
        .value_counts()
    )

    plt.figure(figsize=(8, 5))

    counts.plot(kind="bar")

    plt.title("Student Final Result Distribution")
    plt.xlabel("Final Result")
    plt.ylabel("Number of Students")

    plt.xticks(rotation=0)
    plt.tight_layout()

    plt.savefig(
        PLOTS_DIR / "final_result_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

def plot_score_distribution(student_profile):

    print("Creating score distribution...")

    scores = student_profile["average_score"]

    plt.figure(figsize=(8, 5))

    scores.plot(
        kind="hist",
        bins=30
    )

    plt.title("Student Average Score Distribution")
    plt.xlabel("Average Score")
    plt.ylabel("Number of Students")

    plt.tight_layout()

    plt.savefig(
        PLOTS_DIR / "score_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# ACTIVITY DISTRIBUTION
# ============================================================

def plot_activity_distribution(student_profile):

    print("Creating activity distribution...")

    clicks = student_profile["total_clicks"]

    plt.figure(figsize=(8, 5))

    clicks.plot(
        kind="hist",
        bins=30
    )

    plt.title("Student Learning Activity Distribution")
    plt.xlabel("Total VLE Clicks")
    plt.ylabel("Number of Students")

    plt.tight_layout()

    plt.savefig(
        PLOTS_DIR / "activity_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================
# COURSE POPULARITY
# ============================================================

def plot_course_popularity(course_profile):

    print("Creating course popularity chart...")

    df = (
        course_profile
        .sort_values(
            "total_clicks",
            ascending=False
        )
        .head(10)
    )

    labels = (
        df["course_id"]
        .astype(str)
    )

    values = df["total_clicks"]

    plt.figure(figsize=(10, 6))

    plt.bar(labels, values)

    plt.title("Top 10 OULAD Courses by Learning Activity")
    plt.xlabel("Course")
    plt.ylabel("Total Clicks")

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        PLOTS_DIR / "course_popularity.png",
        dpi=150
    )

    plt.close()


# ============================================================
# LEARNING SCORE ANALYSIS
# ============================================================

def create_learning_score_report(student_profile):

    print("\nCreating learning score report...")

    df = student_profile.copy()

    result = pd.DataFrame({
        "metric": [
            "Minimum Learning Score",
            "Maximum Learning Score",
            "Mean Learning Score",
            "Median Learning Score",
            "Minimum Academic Score",
            "Maximum Academic Score",
            "Mean Academic Score",
            "Minimum Engagement Score",
            "Maximum Engagement Score",
            "Mean Engagement Score",
        ],
        "value": [
            df["overall_learning_score"].min(),
            df["overall_learning_score"].max(),
            df["overall_learning_score"].mean(),
            df["overall_learning_score"].median(),
            df["academic_score"].min(),
            df["academic_score"].max(),
            df["academic_score"].mean(),
            df["engagement_score"].min(),
            df["engagement_score"].max(),
            df["engagement_score"].mean(),
        ]
    })

    result.to_csv(
        REPORTS_DIR / "learning_score_report.csv",
        index=False
    )

    print(
        "Saved:",
        REPORTS_DIR / "learning_score_report.csv"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 2 - EXPLORATORY DATA ANALYSIS")
    print("=" * 70)

    (
        students,
        courses,
        assessments,
        student_profile,
        course_profile,
    ) = load_processed_data()

    create_dataset_report(
        students,
        courses,
        assessments,
        student_profile,
        course_profile,
    )

    create_student_performance_report(
        student_profile
    )

    create_course_activity_report(
        course_profile
    )

    create_learning_score_report(
        student_profile
    )

    plot_final_result_distribution(
        students
    )

    plot_score_distribution(
        student_profile
    )

    plot_activity_distribution(
        student_profile
    )

    plot_course_popularity(
        course_profile
    )

    print("\n" + "=" * 70)
    print("PHASE 2 EDA COMPLETE")
    print("=" * 70)

    print("\nReports created in:")
    print(REPORTS_DIR)

    print("\nPlots created in:")
    print(PLOTS_DIR)


if __name__ == "__main__":
    main()