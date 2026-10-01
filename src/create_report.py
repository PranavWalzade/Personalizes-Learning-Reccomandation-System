import pandas as pd

from config import (
    OULAD_FILES,
    ENGINEERING_COURSES_FILE,
    REPORTS_DIR,
)


def dataset_summary(name, df):

    return {
        "dataset": name,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(
            df.isnull().sum().sum()
        ),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
    }


def main():

    print("=" * 70)
    print("PHASE 1 - REPORT GENERATION")
    print("=" * 70)

    summaries = []

    for name, path in OULAD_FILES.items():

        df = pd.read_csv(path)

        summaries.append(
            dataset_summary(
                name,
                df
            )
        )

    engineering = pd.read_csv(
        ENGINEERING_COURSES_FILE
    )

    summaries.append(
        dataset_summary(
            "engineering_courses",
            engineering
        )
    )

    report = pd.DataFrame(
        summaries
    )

    output_file = (
        REPORTS_DIR /
        "phase1_dataset_summary.csv"
    )

    report.to_csv(
        output_file,
        index=False
    )

    print("\nDataset summary:\n")

    print(
        report.to_string(
            index=False
        )
    )

    print(
        f"\nSaved:\n{output_file}"
    )

    if "branch" in engineering.columns:

        branch_report = (
            engineering["branch"]
            .value_counts()
            .rename_axis("branch")
            .reset_index(
                name="course_count"
            )
        )

        branch_file = (
            REPORTS_DIR /
            "engineering_branch_summary.csv"
        )

        branch_report.to_csv(
            branch_file,
            index=False
        )

        print(
            f"\nBranch report saved:\n"
            f"{branch_file}"
        )

        print("\nBranch distribution:\n")

        print(
            branch_report.to_string(
                index=False
            )
        )

    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    main()