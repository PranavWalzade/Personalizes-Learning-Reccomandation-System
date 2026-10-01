import tempfile
import unittest
from pathlib import Path

import routes.recommendations as recommendations


class RecommendationModelTests(unittest.TestCase):
    def test_saved_tfidf_model_ranks_matching_course_higher(self):
        student = {
            "interests": "Probability Statistics Hypothesis Testing",
            "branch": "AI & Data Science",
            "learning_level": "Intermediate",
        }
        courses = [
            {
                "course_name": "Statistics for Data Science",
                "branch": "AI & Data Science",
                "category": "Statistics",
                "skills": "Probability;Statistics;Hypothesis Testing",
            },
            {
                "course_name": "Structural Design",
                "branch": "Civil Engineering",
                "category": "Construction",
                "skills": "Concrete;Structures;Surveying",
            },
        ]

        original_bundle = recommendations._model_bundle
        try:
            recommendations._model_bundle = None
            scores = recommendations.calculate_content_scores(
                student,
                [],
                courses
            )
        finally:
            recommendations._model_bundle = original_bundle

        self.assertEqual(len(scores), 2)
        self.assertGreater(scores[0], scores[1])
        self.assertGreaterEqual(scores[0], 0)
        self.assertLessEqual(scores[0], 1)

    def test_corrupt_model_fails_explicitly_instead_of_using_a_fallback(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_path = Path(temporary_directory) / "broken_model.joblib"
            model_path.write_bytes(b"not-a-valid-model")

            original_path = recommendations.MODEL_PATH
            original_bundle = recommendations._model_bundle
            try:
                recommendations.MODEL_PATH = model_path
                recommendations._model_bundle = None

                with self.assertRaisesRegex(
                    RuntimeError,
                    "Could not load the trained recommendation model"
                ):
                    recommendations.get_content_model()
            finally:
                recommendations.MODEL_PATH = original_path
                recommendations._model_bundle = original_bundle


if __name__ == "__main__":
    unittest.main()
