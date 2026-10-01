import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ============================================================
# ADD SRC TO PYTHON PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from config import (
    PROCESSED_DIR,
    ENGINEERING_COURSES_FILE,
    REPORTS_DIR,
)

# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    files = {
        "students": PROCESSED_DIR / "clean_students.csv",
        "courses": PROCESSED_DIR / "clean_courses.csv",
        "assessments": PROCESSED_DIR / "clean_assessments.csv",
        "student_profile": PROCESSED_DIR / "student_profile.csv",
        "course_profile": PROCESSED_DIR / "course_profile.csv",
        "student_course_performance":
            PROCESSED_DIR / "student_course_performance.csv",
        "student_skill_profile":
            PROCESSED_DIR / "student_skill_profile.csv",
        "student_course_strength":
            PROCESSED_DIR / "student_course_strength.csv",
        "student_skill_gap":
            PROCESSED_DIR / "student_skill_gap.csv",
        "engineering_courses":
            ENGINEERING_COURSES_FILE,
    }

    data = {}

    for name, path in files.items():

        if not path.exists():
            print(f"[MISSING] {name}: {path}")
            continue

        df = pd.read_csv(path)
        data[name] = df

        print(
            f"[OK] {name:<25} "
            f"Rows: {len(df):>8,} | "
            f"Columns: {len(df.columns):>3}"
        )

    return data


# ============================================================
# BASIC DATA QUALITY CHECKS
# ============================================================

def check_basic_quality(data):

    results = []

    for name, df in data.items():

        # Missing values
        missing_cells = int(df.isna().sum().sum())

        # Duplicate rows
        duplicate_rows = int(df.duplicated().sum())

        # Empty dataset
        empty_dataset = len(df) == 0

        results.append({
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "empty_dataset": empty_dataset,
        })

    return pd.DataFrame(results)


# ============================================================
# RANGE VALIDATION
# ============================================================

def check_ranges(data):

    results = []

    # --------------------------------------------------------
    # Student course performance
    # --------------------------------------------------------

    if "student_course_performance" in data:

        df = data["student_course_performance"]

        if "average_score" in df.columns:

            invalid = (
                (df["average_score"] < 0) |
                (df["average_score"] > 100)
            ).sum()

            results.append({
                "dataset": "student_course_performance",
                "field": "average_score",
                "invalid_values": int(invalid),
                "expected": "0 to 100",
            })

        if "pass_rate" in df.columns:

            invalid = (
                (df["pass_rate"] < 0) |
                (df["pass_rate"] > 1)
            ).sum()

            results.append({
                "dataset": "student_course_performance",
                "field": "pass_rate",
                "invalid_values": int(invalid),
                "expected": "0 to 1",
            })

        if "academic_score" in df.columns:

            invalid = (
                (df["academic_score"] < 0) |
                (df["academic_score"] > 1)
            ).sum()

            results.append({
                "dataset": "student_course_performance",
                "field": "academic_score",
                "invalid_values": int(invalid),
                "expected": "0 to 1",
            })

    # --------------------------------------------------------
    # Student skill gap
    # --------------------------------------------------------

    if "student_skill_gap" in data:

        df = data["student_skill_gap"]

        for column in [
            "readiness_score"
        ]:

            if column in df.columns:

                invalid = (
                    (df[column] < 0) |
                    (df[column] > 1)
                ).sum()

                results.append({
                    "dataset": "student_skill_gap",
                    "field": column,
                    "invalid_values": int(invalid),
                    "expected": "0 to 1",
                })

    # --------------------------------------------------------
    # Engineering courses
    # --------------------------------------------------------

    if "engineering_courses" in data:

        df = data["engineering_courses"]

        if "difficulty" in df.columns:

            invalid = (
                (df["difficulty"] < 1) |
                (df["difficulty"] > 5)
            ).sum()

            results.append({
                "dataset": "engineering_courses",
                "field": "difficulty",
                "invalid_values": int(invalid),
                "expected": "1 to 5",
            })

        if "credits" in df.columns:

            invalid = (
                (df["credits"] <= 0)
            ).sum()

            results.append({
                "dataset": "engineering_courses",
                "field": "credits",
                "invalid_values": int(invalid),
                "expected": "> 0",
            })

    return pd.DataFrame(results)


# ============================================================
# ID CONSISTENCY CHECK
# ============================================================

def check_id_consistency(data):

    results = []

    student_sets = {}

    for name in [
        "students",
        "student_profile",
        "student_course_performance",
        "student_skill_profile",
        "student_course_strength",
        "student_skill_gap",
    ]:

        if name not in data:
            continue

        df = data[name]

        if "id_student" in df.columns:

            ids = set(
                pd.to_numeric(
                    df["id_student"],
                    errors="coerce"
                ).dropna().astype(int)
            )

            student_sets[name] = ids

    if student_sets:

        reference_name = "students"

        if reference_name in student_sets:

            reference = student_sets[reference_name]

            for name, ids in student_sets.items():

                if name == reference_name:
                    continue

                missing_from_dataset = len(reference - ids)
                extra_ids = len(ids - reference)

                results.append({
                    "dataset": name,
                    "missing_student_ids": missing_from_dataset,
                    "extra_student_ids": extra_ids,
                    "status":
                        "OK"
                        if missing_from_dataset == 0
                        and extra_ids == 0
                        else "CHECK",
                })

    return pd.DataFrame(results)


# ============================================================
# ENGINEERING COURSE VALIDATION
# ============================================================

def check_engineering_courses(data):

    results = []

    if "engineering_courses" not in data:
        return pd.DataFrame()

    df = data["engineering_courses"]

    # Course count
    results.append({
        "check": "Engineering course count",
        "value": len(df),
        "expected": 155,
        "status": "OK" if len(df) == 155 else "CHECK",
    })

    # Course ID uniqueness
    if "course_id" in df.columns:

        duplicates = df["course_id"].duplicated().sum()

        results.append({
            "check": "Duplicate course IDs",
            "value": int(duplicates),
            "expected": 0,
            "status": "OK" if duplicates == 0 else "CHECK",
        })

    # Missing course names
    if "course_name" in df.columns:

        missing = df["course_name"].isna().sum()

        results.append({
            "check": "Missing course names",
            "value": int(missing),
            "expected": 0,
            "status": "OK" if missing == 0 else "CHECK",
        })

    # Missing skills
    if "skills" in df.columns:

        missing = (
            df["skills"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        results.append({
            "check": "Courses without skills",
            "value": int(missing),
            "expected": 0,
            "status": "OK" if missing == 0 else "CHECK",
        })

    return pd.DataFrame(results)


# ============================================================
# LEAKAGE CHECK
# ============================================================

def create_leakage_report(data):

    leakage = [

        {
            "feature": "final_result",
            "risk": "HIGH",
            "reason":
                "Final result is an outcome variable and must not "
                "be used as an input feature for recommendation.",
            "action":
                "Exclude from model input features."
        },

        {
            "feature": "held-out assessment score",
            "risk": "HIGH",
            "reason":
                "Using the target course performance while generating "
                "recommendations causes target leakage.",
            "action":
                "Only use historical/training interactions."
        },

        {
            "feature": "engagement rank",
            "risk": "MEDIUM",
            "reason":
                "Global ranking can include information from the "
                "evaluation period.",
            "action":
                "Recalculate engagement features using training data only."
        },

        {
            "feature": "student_course_performance",
            "risk": "MEDIUM",
            "reason":
                "Performance must be split correctly before evaluation.",
            "action":
                "Never use test interaction information to build "
                "student features."
        },

        {
            "feature": "engineering course catalog",
            "risk": "LOW",
            "reason":
                "Course metadata does not contain student outcomes.",
            "action":
                "Safe to use as item/content features."
        },

        {
            "feature": "student demographics",
            "risk": "LOW",
            "reason":
                "Can be used as contextual features if justified.",
            "action":
                "Check fairness and avoid unnecessary sensitive attributes."
        },

    ]

    return pd.DataFrame(leakage)


# ============================================================
# DATASET SUMMARY
# ============================================================

def create_summary(data):

    rows = []

    for name, df in data.items():

        rows.append({
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "memory_mb":
                round(
                    df.memory_usage(deep=True).sum()
                    / (1024 ** 2),
                    2
                ),
        })

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("PHASE 2 — DATA QUALITY VALIDATION")
    print("=" * 70)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\n[1] Loading processed datasets...\n")

    data = load_data()

    if not data:
        print("\nERROR: No processed datasets found.")
        return

    # --------------------------------------------------------
    # Basic quality
    # --------------------------------------------------------

    print("\n[2] Running basic quality checks...")

    basic_report = check_basic_quality(data)

    basic_report.to_csv(
        REPORTS_DIR / "phase2_basic_quality_report.csv",
        index=False
    )

    # --------------------------------------------------------
    # Range checks
    # --------------------------------------------------------

    print("[3] Checking numeric ranges...")

    range_report = check_ranges(data)

    range_report.to_csv(
        REPORTS_DIR / "phase2_range_validation_report.csv",
        index=False
    )

    # --------------------------------------------------------
    # ID checks
    # --------------------------------------------------------

    print("[4] Checking student ID consistency...")

    id_report = check_id_consistency(data)

    id_report.to_csv(
        REPORTS_DIR / "phase2_id_consistency_report.csv",
        index=False
    )

    # --------------------------------------------------------
    # Engineering catalog
    # --------------------------------------------------------

    print("[5] Validating engineering course catalog...")

    engineering_report = check_engineering_courses(data)

    engineering_report.to_csv(
        REPORTS_DIR / "phase2_engineering_course_validation.csv",
        index=False
    )

    # --------------------------------------------------------
    # Leakage
    # --------------------------------------------------------

    print("[6] Creating leakage report...")

    leakage_report = create_leakage_report(data)

    leakage_report.to_csv(
        REPORTS_DIR / "phase2_leakage_check_report.csv",
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("[7] Creating dataset summary...")

    summary = create_summary(data)

    summary.to_csv(
        REPORTS_DIR / "phase2_dataset_summary.csv",
        index=False
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print("\nDataset Summary:")
    print(summary.to_string(index=False))

    print("\nRange Validation:")
    print(range_report.to_string(index=False))

    print("\nEngineering Course Validation:")
    print(engineering_report.to_string(index=False))

    print("\nID Consistency:")
    print(id_report.to_string(index=False))

    print("\n" + "=" * 70)
    print("PHASE 2 VALIDATION COMPLETE")
    print("=" * 70)

    print("\nReports created in:")
    print(REPORTS_DIR)


if __name__ == "__main__":
    main()