import sys

from config import (
    BASE_DIR,
    DATA_DIR,
    OULAD_DIR,
    ENGINEERING_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    REPORTS_DIR,
    PLOTS_DIR,
    EXPORTS_DIR,
    LOGS_DIR,
    OULAD_FILES,
    ENGINEERING_COURSES_FILE,
)


def check_folder(name, path):

    if path.exists():
        print(f"[OK]      {name:<20} {path}")
        return True

    print(f"[MISSING] {name:<20} {path}")
    return False


def check_file(name, path):

    if path.exists():

        size_mb = path.stat().st_size / (
            1024 * 1024
        )

        print(
            f"[OK]      {name:<25} "
            f"{size_mb:.2f} MB"
        )

        return True

    print(
        f"[MISSING] {name:<25} "
        f"{path}"
    )

    return False


def main():

    print("=" * 70)

    print(
        "PERSONALIZED LEARNING "
        "RECOMMENDATION SYSTEM"
    )

    print(
        "PHASE 1 - PYTHON 3.14 "
        "SETUP CHECK"
    )

    print("=" * 70)

    print("\nPython version:")
    print(sys.version)

    print("\nPython executable:")
    print(sys.executable)

    print("\nProject directory:")
    print(BASE_DIR)

    print("\n" + "-" * 70)
    print("CHECKING FOLDERS")
    print("-" * 70)

    folders = {
        "Data": DATA_DIR,
        "OULAD": OULAD_DIR,
        "Engineering": ENGINEERING_DIR,
        "Models": MODELS_DIR,
        "Results": RESULTS_DIR,
        "Reports": REPORTS_DIR,
        "Plots": PLOTS_DIR,
        "Exports": EXPORTS_DIR,
        "Logs": LOGS_DIR,
    }

    folders_ok = True

    for name, path in folders.items():

        if not check_folder(name, path):
            folders_ok = False

    print("\n" + "-" * 70)
    print("CHECKING OULAD DATASET")
    print("-" * 70)

    oulad_ok = True

    for name, path in OULAD_FILES.items():

        if not check_file(
            f"{name}.csv",
            path
        ):
            oulad_ok = False

    print("\n" + "-" * 70)
    print("CHECKING ENGINEERING DATASET")
    print("-" * 70)

    engineering_ok = check_file(
        ENGINEERING_COURSES_FILE.name,
        ENGINEERING_COURSES_FILE
    )

    print("\n" + "=" * 70)

    if (
        folders_ok
        and oulad_ok
        and engineering_ok
    ):

        print(
            "STATUS: PHASE 1 SETUP READY"
        )

    else:

        print(
            "STATUS: SETUP INCOMPLETE"
        )

        print(
            "Fix the missing files/folders "
            "shown above."
        )

    print("=" * 70)


if __name__ == "__main__":
    main()