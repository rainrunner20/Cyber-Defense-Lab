"""Offline Flask tests using a temporary SQLite database, not real telemetry."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from extensions import db
from models import User


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        database = Path(self.temp.name) / "lab.sqlite3"
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(database),
            "JWT_SECRET_KEY": "test-only-not-for-live-use-" + ("x" * 40),
        })
        self.client = self.app.test_client()

    def register(self, username="example_user", team="blue", password="strong-test-password-123"):
        return self.client.post("/register", json={
            "username": username, "password": password, "team": team
        })

    def login(self, username="example_user", password="strong-test-password-123"):
        return self.client.post("/login", json={"username": username, "password": password})

    def token(self, username="example_user"):
        return self.login(username).json["access_token"]

    def test_offline_health(self):
        self.assertEqual(self.client.get("/health").json["environment"], "educational-demo")

    def test_register_hashes_password_and_rejects_duplicate(self):
        self.assertEqual(self.register().status_code, 201)
        with self.app.app_context():
            user = db.session.query(User).filter_by(username="example_user").first()
            self.assertNotEqual(user.password_hash, "strong-test-password-123")
            self.assertTrue(user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"))
        self.assertEqual(self.register().status_code, 409)

    def test_rejects_invalid_signups_and_logins(self):
        for name, password, team in [("!!", "a-long-enough-password", "blue"),
                                     ("name123", "short", "blue"),
                                     ("name123", "a-long-enough-password", "admin")]:
            self.assertEqual(self.register(name, team, password).status_code, 400)
        self.register()
        self.assertEqual(self.login(password="incorrect").status_code, 401)
        self.assertEqual(self.login().status_code, 200)

    def test_events_require_authentication_and_remain_synthetic(self):
        self.assertEqual(self.client.get("/api/events").status_code, 401)
        self.register()
        auth = {"Authorization": "Bearer " + self.token()}
        self.assertEqual(self.client.post("/api/events", json={"kind": "real_exploit"}, headers=auth).status_code, 400)
        event = self.client.post("/api/events", json={"kind": "suspicious_volume"}, headers=auth)
        self.assertEqual(event.status_code, 201)
        self.assertEqual(event.json["source"], "synthetic")
        self.assertEqual(event.json["severity"], "high")
        listed = self.client.get("/api/events", headers=auth).json["events"]
        self.assertEqual(len(listed), 1)

    def test_events_are_private_between_training_accounts(self):
        self.register()
        token_a = self.token()
        self.register(username="other_user", team="red")
        token_b = self.token("other_user")
        self.client.post("/api/events", json={"kind": "failed_login"},
                         headers={"Authorization": "Bearer " + token_a})
        result = self.client.get("/api/events", headers={"Authorization": "Bearer " + token_b})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["events"], [])

    def test_team_is_a_training_preference_not_admin(self):
        self.register(team="red")
        auth = {"Authorization": "Bearer " + self.token()}
        self.assertEqual(self.client.get("/api/me", headers=auth).json["team"], "red")
        allowed = self.client.get("/health", headers={"Origin": "http://localhost:5173"})
        denied = self.client.get("/health", headers={"Origin": "https://untrusted.example"})
        self.assertEqual(allowed.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        self.assertIsNone(denied.headers.get("Access-Control-Allow-Origin"))


if __name__ == "__main__":
    unittest.main()
