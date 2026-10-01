from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DATA DIRECTORIES
# ============================================================

DATA_DIR = BASE_DIR / "data"

OULAD_DIR = DATA_DIR / "oulad"

ENGINEERING_DIR = DATA_DIR / "engineering"


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

MODELS_DIR = BASE_DIR / "models"

RESULTS_DIR = BASE_DIR / "results"

REPORTS_DIR = BASE_DIR / "reports"

PLOTS_DIR = BASE_DIR / "plots"

EXPORTS_DIR = BASE_DIR / "exports"

LOGS_DIR = BASE_DIR / "logs"


# ============================================================
# OULAD FILES
# ============================================================

OULAD_FILES = {
    "assessments": OULAD_DIR / "assessments.csv",
    "courses": OULAD_DIR / "courses.csv",
    "studentAssessment": OULAD_DIR / "studentAssessment.csv",
    "studentInfo": OULAD_DIR / "studentInfo.csv",
    "studentRegistration": OULAD_DIR / "studentRegistration.csv",
    "studentVle": OULAD_DIR / "studentVle.csv",
    "vle": OULAD_DIR / "vle.csv",
}


# ============================================================
# ENGINEERING COURSE CATALOG
# ============================================================

ENGINEERING_COURSES_FILE = (
    ENGINEERING_DIR /
    "engineering_courses_extended.csv"
)


# ============================================================
# PROCESSED DATA
# ============================================================

PROCESSED_DIR = DATA_DIR / "processed"


PROCESSED_FILES = {
    "students": PROCESSED_DIR / "clean_students.csv",
    "courses": PROCESSED_DIR / "clean_courses.csv",
    "assessments": PROCESSED_DIR / "clean_assessments.csv",
    "vle": PROCESSED_DIR / "clean_vle.csv",
    "student_profile": PROCESSED_DIR / "student_profile.csv",
    "course_profile": PROCESSED_DIR / "course_profile.csv",
}