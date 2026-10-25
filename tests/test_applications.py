import os
import tempfile
import unittest

from fastapi.testclient import TestClient

import db

SAMPLE_RESULT = {
    "jd_language": "de",
    "match_score": 82,
    "tailored_cv": "ASHER BAIG",
    "validation": {"verdict": "safe", "flags": [], "summary": "ok"},
    "pdf_filename": "schoolboost_20261015_120000.pdf",
}


class ApplicationDbTestCase(unittest.TestCase):
    # Each test gets its own empty SQLite file.
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = os.environ.get("DB_PATH")
        os.environ["DB_PATH"] = os.path.join(self.tmp.name, "test.db")
        db.init_db()

    def tearDown(self):
        if self.old_db_path is None:
            os.environ.pop("DB_PATH", None)
        else:
            os.environ["DB_PATH"] = self.old_db_path
        self.tmp.cleanup()


class TestApplicationDb(ApplicationDbTestCase):
    def test_save_and_get_round_trip(self):
        app_id = db.save_application("schoolboost", "Full-stack JD", SAMPLE_RESULT)
        stored = db.get_application(app_id)
        self.assertEqual(stored["company_name"], "schoolboost")
        self.assertEqual(stored["match_score"], 82)
        self.assertEqual(stored["verdict"], "safe")
        self.assertEqual(stored["status"], "tailored")
        self.assertEqual(stored["result"]["tailored_cv"], "ASHER BAIG")

    def test_list_is_newest_first(self):
        first = db.save_application("A", "jd", SAMPLE_RESULT)
        second = db.save_application("B", "jd", SAMPLE_RESULT)
        ids = [row["id"] for row in db.list_applications()]
        self.assertEqual(ids, [second, first])

    def test_stats(self):
        self.assertEqual(db.get_stats()["total"], 0)
        a = db.save_application("A", "jd", {**SAMPLE_RESULT, "match_score": 80})
        db.save_application("B", "jd", {**SAMPLE_RESULT, "match_score": 60})
        db.update_status(a, "interview")
        stats = db.get_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["avg_score"], 70)
        self.assertEqual(stats["interviews"], 1)

    def test_invalid_status_rejected(self):
        app_id = db.save_application("A", "jd", SAMPLE_RESULT)
        with self.assertRaises(ValueError):
            db.update_status(app_id, "hired-yesterday")

    def test_missing_ids(self):
        self.assertIsNone(db.get_application(999))
        self.assertFalse(db.update_status(999, "applied"))
        self.assertFalse(db.delete_application(999))


class TestApplicationApi(ApplicationDbTestCase):
    def setUp(self):
        super().setUp()
        from main import app
        self.client = TestClient(app)

    def test_dashboard_endpoints(self):
        app_id = db.save_application("schoolboost", "jd", SAMPLE_RESULT)

        listing = self.client.get("/applications").json()
        self.assertEqual(listing["stats"]["total"], 1)
        self.assertEqual(listing["applications"][0]["company_name"], "schoolboost")

        response = self.client.patch(f"/applications/{app_id}", json={"status": "applied"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(f"/applications/{app_id}").json()["status"], "applied")

        bad = self.client.patch(f"/applications/{app_id}", json={"status": "nope"})
        self.assertEqual(bad.status_code, 400)

        self.assertEqual(self.client.delete(f"/applications/{app_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/applications/{app_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
