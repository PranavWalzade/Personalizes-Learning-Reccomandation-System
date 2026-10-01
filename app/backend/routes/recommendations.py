from pathlib import Path

import joblib
from flask import Blueprint, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity

from utils.database import get_db_connection


recommendations_bp = Blueprint(
    "recommendations",
    __name__
)

MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "models"
    / "content_based_tfidf.joblib"
)
_model_bundle = None


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, float(value)))


def normalize_text(value):
    if value is None:
        return ""

    return str(value).lower().strip()


def get_content_model():
    global _model_bundle

    if _model_bundle is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Trained recommendation model was not found: {MODEL_PATH}"
            )

        try:
            model = joblib.load(MODEL_PATH)
        except Exception as error:
            raise RuntimeError(
                f"Could not load the trained recommendation model from {MODEL_PATH}"
            ) from error

        if (
            not hasattr(model, "transform")
            or not hasattr(model, "vocabulary_")
        ):
            raise TypeError(
                "The saved recommendation model is not a fitted text vectorizer."
            )

        _model_bundle = model

    return _model_bundle


def build_course_text(course):
    return " ".join(
        normalize_text(course.get(field))
        for field in (
            "course_name",
            "branch",
            "category",
            "skills",
            "prerequisites",
            "course_level",
        )
    )


def calculate_content_scores(student, skills, courses):
    model = get_content_model()
    skill_names = " ".join(
        str(skill.get("skill_name") or "")
        for skill in skills
    )
    student_text = " ".join(
        str(value or "")
        for value in (
            student.get("interests"),
            student.get("branch"),
            student.get("learning_level"),
            skill_names,
        )
    ).strip()

    if not student_text or not courses:
        return [0.0] * len(courses)

    student_vector = model.transform([student_text])
    course_vectors = model.transform(
        [build_course_text(course) for course in courses]
    )

    return [
        clamp(score)
        for score in cosine_similarity(
            student_vector,
            course_vectors
        )[0]
    ]


def calculate_difficulty_fit(
    readiness_score,
    course_difficulty
):
    try:
        readiness = float(readiness_score)
    except (ValueError, TypeError):
        readiness = 0.5

    try:
        difficulty = float(course_difficulty)
    except (ValueError, TypeError):
        difficulty = 0.5

    readiness = clamp(readiness)
    difficulty = clamp(difficulty)

    distance = abs(readiness - difficulty)

    return clamp(1.0 - distance)


def calculate_semester_fit(
    student_semester,
    course_semester
):
    try:
        student_semester = int(student_semester)
    except (ValueError, TypeError):
        student_semester = 1

    try:
        course_semester = int(course_semester)
    except (ValueError, TypeError):
        course_semester = 1

    difference = abs(
        student_semester - course_semester
    )

    if difference == 0:
        return 1.0

    if difference == 1:
        return 0.8

    if difference == 2:
        return 0.6

    if difference == 3:
        return 0.4

    return 0.2


def calculate_branch_fit(
    student_branch,
    course_branch
):
    student_branch = normalize_text(
        student_branch
    )

    course_branch = normalize_text(
        course_branch
    )

    if not student_branch:
        return 0.5

    if course_branch == student_branch:
        return 1.0

    if course_branch in (
        "",
        "all engineering",
        "common"
    ):
        return 0.8

    return 0.2


def calculate_skill_match(
    interests,
    student_skills,
    course
):
    student_text = " ".join(
        [
            normalize_text(interests),
            normalize_text(student_skills)
        ]
    )

    course_text = " ".join(
        [
            normalize_text(course.get("course_name")),
            normalize_text(course.get("skills")),
            normalize_text(course.get("category")),
            normalize_text(course.get("prerequisites"))
        ]
    )

    if not student_text:
        return 0.5

    student_words = set(
        word
        for word in student_text.split()
        if len(word) > 2
    )

    course_words = set(
        word
        for word in course_text.split()
        if len(word) > 2
    )

    if not student_words or not course_words:
        return 0.5

    common_words = student_words.intersection(
        course_words
    )

    score = len(common_words) / len(
        student_words
    )

    return clamp(score)


def calculate_complexity_fit(
    readiness_score,
    skill_count
):
    try:
        readiness = float(readiness_score)
    except (ValueError, TypeError):
        readiness = 0.5

    try:
        skill_count = int(skill_count)
    except (ValueError, TypeError):
        skill_count = 1

    readiness = clamp(readiness)

    if skill_count <= 3:
        complexity = 0.3
    elif skill_count <= 5:
        complexity = 0.5
    elif skill_count <= 7:
        complexity = 0.7
    else:
        complexity = 0.9

    return clamp(
        1.0 - abs(readiness - complexity)
    )


def generate_explanation(
    branch_fit,
    skill_match,
    readiness_fit,
    difficulty_fit,
    course
):
    reasons = []

    if branch_fit >= 0.8:
        reasons.append(
            "matches your engineering branch"
        )

    if skill_match >= 0.5:
        reasons.append(
            "matches your interests and skills"
        )

    if readiness_fit >= 0.7:
        reasons.append(
            "fits your current learning readiness"
        )

    if difficulty_fit >= 0.75:
        reasons.append(
            "the difficulty is suitable for your level"
        )

    if course.get("is_core"):
        reasons.append(
            "it is an important core engineering subject"
        )

    if not reasons:
        reasons.append(
            "it provides a useful learning opportunity "
            "based on your current profile"
        )

    return "Recommended because it " + ", ".join(
        reasons
    ) + "."


# =========================================================
# GET RECOMMENDATIONS
# =========================================================

@recommendations_bp.route(
    "/student/<int:student_id>/recommendations",
    methods=["GET"]
)
def get_recommendations(student_id):

    connection = None
    cursor = None

    try:

        limit = request.args.get(
            "limit",
            default=10,
            type=int
        )

        branch_filter = request.args.get(
            "branch",
            default=""
        ).strip()

        limit = max(
            1,
            min(limit, 50)
        )

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # STUDENT PROFILE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                student_name,
                branch,
                semester,
                interests,
                preferred_difficulty,
                learning_level,
                academic_strength,
                engagement_strength,
                readiness_score
            FROM students
            WHERE id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        # -------------------------------------------------
        # STUDENT SKILLS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                skill_name,
                skill_level
            FROM student_skills
            WHERE student_id = %s
            """,
            (student_id,)
        )

        skills = cursor.fetchall()

        # -------------------------------------------------
        # COMPLETED COURSES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                course_id
            FROM student_courses
            WHERE student_id = %s
              AND status = 'completed'
            """,
            (student_id,)
        )

        completed_rows = cursor.fetchall()

        completed_courses = set(
            str(row["course_id"])
            for row in completed_rows
        )

        # -------------------------------------------------
        # ENGINEERING COURSES
        # -------------------------------------------------

        query = """
            SELECT
                id,
                course_id,
                course_name,
                branch,
                semester,
                category,
                skills,
                prerequisites,
                difficulty,
                credits,
                course_level,
                is_core
            FROM courses
            WHERE 1 = 1
        """

        params = []

        if branch_filter:

            query += """
                AND (
                    branch = %s
                    OR branch = 'All Engineering'
                    OR branch = ''
                )
            """

            params.append(
                branch_filter
            )

        cursor.execute(
            query,
            tuple(params)
        )

        courses = cursor.fetchall()
        content_scores = calculate_content_scores(
            student,
            skills,
            courses
        )

        # -------------------------------------------------
        # CALCULATE HYBRID SCORE
        # -------------------------------------------------

        recommendations = []

        for course, content_score in zip(
            courses,
            content_scores
        ):

            course_code = str(
                course["course_id"]
            )

            # Don't recommend completed courses
            if course_code in completed_courses:
                continue

            # -------------------------------
            # 1. CONTENT / SKILL SCORE
            # -------------------------------

            skill_match = content_score

            # -------------------------------
            # 2. COMPATIBILITY
            # -------------------------------

            branch_fit = calculate_branch_fit(
                student.get("branch"),
                course.get("branch")
            )

            semester_fit = calculate_semester_fit(
                student.get("semester"),
                course.get("semester")
            )

            academic_strength = (
                student.get(
                    "academic_strength"
                )
            )

            try:
                academic_strength = float(
                    academic_strength
                )
            except (
                ValueError,
                TypeError
            ):
                academic_strength = 0.5

            academic_strength = clamp(
                academic_strength
            )

            compatibility = (
                0.60 * branch_fit
                +
                0.20 * semester_fit
                +
                0.20 * academic_strength
            )

            # -------------------------------
            # 3. READINESS
            # -------------------------------

            readiness = student.get(
                "readiness_score"
            )

            try:
                readiness = float(
                    readiness
                )
            except (
                ValueError,
                TypeError
            ):
                readiness = 0.5

            if readiness > 1:
                readiness = readiness / 100

            readiness = clamp(
                readiness
            )

            readiness_fit = (
                0.60 * readiness
                +
                0.40 * semester_fit
            )

            # -------------------------------
            # 4. DIFFICULTY
            # -------------------------------

            difficulty = (
                course.get("difficulty")
            )

            try:
                raw_difficulty = float(
                    difficulty
                )

                difficulty = (
                    raw_difficulty - 1
                ) / 4

            except (
                ValueError,
                TypeError
            ):
                difficulty = 0.5

            difficulty_fit = calculate_difficulty_fit(
                readiness,
                difficulty
            )

            # -------------------------------
            # 5. POPULARITY
            # -------------------------------

            # Current web-app catalog does not
            # necessarily contain historical
            # popularity for every course.
            #
            # Therefore use a neutral score
            # rather than inventing popularity.

            popularity = 0.5

            # -------------------------------
            # FINAL HYBRID SCORE
            # -------------------------------

            hybrid_score = (

                0.25 * skill_match

                +

                0.30 * compatibility

                +

                0.20 * readiness_fit

                +

                0.15 * difficulty_fit

                +

                0.10 * popularity
            )

            hybrid_score = clamp(
                hybrid_score
            )

            explanation = generate_explanation(
                branch_fit,
                skill_match,
                readiness_fit,
                difficulty_fit,
                course
            )

            recommendations.append({

                "course": course,

                "hybrid_score":
                    round(
                        hybrid_score,
                        6
                    ),

                "skill_match":
                    round(
                        skill_match,
                        4
                    ),

                "compatibility":
                    round(
                        compatibility,
                        4
                    ),

                "readiness_fit":
                    round(
                        readiness_fit,
                        4
                    ),

                "difficulty_fit":
                    round(
                        difficulty_fit,
                        4
                    ),

                "explanation":
                    explanation
            })

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        recommendations.sort(
            key=lambda item:
                item["hybrid_score"],
            reverse=True
        )

        recommendations = recommendations[
            :limit
        ]

        # -------------------------------------------------
        # SAVE RECOMMENDATIONS
        # -------------------------------------------------

        cursor.execute(
            """
            DELETE FROM recommendations
            WHERE student_id = %s
            """,
            (student_id,)
        )

        for index, item in enumerate(
            recommendations,
            start=1
        ):

            course_db_id = item[
                "course"
            ]["id"]

            cursor.execute(
                """
                INSERT INTO recommendations
                (
                    student_id,
                    course_id,
                    recommendation_rank,
                    hybrid_score,
                    explanation
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    student_id,
                    course_db_id,
                    index,
                    item["hybrid_score"],
                    item["explanation"]
                )
            )

        connection.commit()

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        response_data = []

        for index, item in enumerate(
            recommendations,
            start=1
        ):

            course = item["course"]

            response_data.append({

                "rank": index,

                "course_id":
                    course["course_id"],

                "course_name":
                    course["course_name"],

                "branch":
                    course["branch"],

                "semester":
                    course["semester"],

                "category":
                    course["category"],

                "difficulty":
                    course["difficulty"],

                "credits":
                    course["credits"],

                "course_level":
                    course["course_level"],

                "is_core":
                    course["is_core"],

                "hybrid_score":
                    item["hybrid_score"],

                "skill_match":
                    item["skill_match"],

                "compatibility":
                    item["compatibility"],

                "readiness_fit":
                    item["readiness_fit"],

                "difficulty_fit":
                    item["difficulty_fit"],

                "explanation":
                    item["explanation"]
            })

        return jsonify({

            "success": True,

            "student_id":
                student_id,

            "model":
                "TF-IDF content-based recommender",

            "count":
                len(response_data),

            "recommendations":
                response_data

        }), 200

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({

            "success": False,

            "message":
                "Failed to generate recommendations",

            "error":
                str(e)

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# SINGLE RECOMMENDATION
# =========================================================

@recommendations_bp.route(
    "/student/<int:student_id>/recommendations/<course_id>",
    methods=["GET"]
)
def get_single_recommendation(
    student_id,
    course_id
):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                r.id,
                r.student_id,
                r.recommendation_rank,
                r.hybrid_score,
                r.explanation,

                c.id AS course_database_id,
                c.course_id,
                c.course_name,
                c.branch,
                c.semester,
                c.category,
                c.skills,
                c.prerequisites,
                c.difficulty,
                c.credits,
                c.course_level,
                c.is_core

            FROM recommendations r

            INNER JOIN courses c
                ON r.course_id = c.id

            WHERE r.student_id = %s
              AND c.course_id = %s

            LIMIT 1
            """,
            (
                student_id,
                course_id
            )
        )

        recommendation = cursor.fetchone()

        if not recommendation:

            return jsonify({

                "success": False,

                "message":
                    "Recommendation not found"

            }), 404

        return jsonify({

            "success": True,

            "recommendation":
                recommendation

        }), 200

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                "Failed to fetch recommendation",

            "error":
                str(e)

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()