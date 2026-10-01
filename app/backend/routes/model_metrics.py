
from flask import Blueprint, jsonify
from utils.database import get_db_connection


model_metrics_bp = Blueprint(
    "model_metrics",
    __name__
)


# ---------------------------------------------------------
# GET ALL MODEL METRICS
# ---------------------------------------------------------

@model_metrics_bp.route(
    "/model-metrics",
    methods=["GET"]
)
def get_model_metrics():

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                model_name,
                precision_at_5,
                recall_at_5,
                ndcg_at_5,
                students_evaluated,
                created_at
            FROM model_metrics
            ORDER BY ndcg_at_5 DESC
            """
        )

        metrics = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "count": len(metrics),
            "metrics": metrics
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to fetch model metrics",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# GET BEST MODEL
# ---------------------------------------------------------

@model_metrics_bp.route(
    "/model-metrics/best",
    methods=["GET"]
)
def get_best_model():

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                model_name,
                precision_at_5,
                recall_at_5,
                ndcg_at_5,
                students_evaluated,
                created_at
            FROM model_metrics
            ORDER BY ndcg_at_5 DESC
            LIMIT 1
            """
        )

        best_model = cursor.fetchone()

        cursor.close()

        if not best_model:

            return jsonify({
                "success": True,
                "message": "No model metrics available",
                "best_model": None
            }), 200

        return jsonify({
            "success": True,
            "best_model": best_model
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to fetch best model",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()
