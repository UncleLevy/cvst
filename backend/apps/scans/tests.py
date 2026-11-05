from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from apps.scans.models import Scan
from apps.scans.tasks import run_scan_task
from apps.targets.models import Target

User = get_user_model()


class ApiSmokeTests(APITestCase):
    def setUp(self):
        cache.clear()  # login throttle uses the cache
        self.user = User.objects.create_user("alice", password="S3cure-pass-123", role="analyst")
        self.other = User.objects.create_user("bob", password="S3cure-pass-123", role="analyst")

    def login(self, username="alice"):
        res = self.client.post(
            "/api/auth/login/", {"username": username, "password": "S3cure-pass-123"}, format="json"
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.data["user"]["username"], username)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_requires_authentication(self):
        res = self.client.get("/api/scans/")
        self.assertEqual(res.status_code, 401)

    def test_registration_disabled_by_default(self):
        res = self.client.post(
            "/api/auth/register/",
            {"username": "eve", "password": "S3cure-pass-123", "role": "admin"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_target_validation_rejects_option_injection(self):
        self.login()
        res = self.client.post(
            "/api/targets/",
            {"name": "bad", "target_type": "hostname", "value": "-oX /tmp/x"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("value", res.data)

    def test_target_and_scan_flow(self):
        self.login()
        res = self.client.post(
            "/api/targets/",
            {"name": "Lab server", "target_type": "ip", "value": "192.168.1.10"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        target_id = res.data["id"]

        with patch("apps.scans.views.run_scan_task") as mocked:
            res = self.client.post(
                "/api/scans/", {"name": "First scan", "target": target_id}, format="json"
            )
        self.assertEqual(res.status_code, 201, res.content)
        mocked.delay.assert_called_once_with(res.data["id"])
        self.assertEqual(res.data["status"], "queued")

        scan = Scan.objects.get(id=res.data["id"])
        with patch("apps.scans.tasks.time.sleep"):
            run_scan_task.apply(args=[scan.id])
        scan.refresh_from_db()
        self.assertEqual(scan.status, "completed")
        self.assertEqual(scan.progress, 100)
        found = scan.vulnerabilities.count()
        self.assertTrue(3 <= found <= 7)
        self.assertFalse(scan.vulnerabilities.exclude(description__startswith="[SIMULATED]").exists())

        res = self.client.get("/api/scans/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["results"][0]["vulnerability_count"], found)

        res = self.client.get(f"/api/scans/{scan.id}/summary/")
        self.assertEqual(res.data["total"], found)

        # Dashboard / findings-page endpoints
        res = self.client.get("/api/scans/stats/")
        self.assertEqual(
            res.data, {"total": 1, "completed": 1, "failed": 0, "active": 0}
        )
        res = self.client.get("/api/vulnerabilities/stats/")
        self.assertEqual(res.data["total"], found)
        self.assertEqual(sum(res.data["by_severity"].values()), found)

        res = self.client.get(f"/api/vulnerabilities/?scan={scan.id}&page_size=200")
        self.assertEqual(res.data["count"], found)
        first = res.data["results"][0]
        self.assertEqual(first["scan_name"], "First scan")
        self.assertEqual(first["target_value"], "192.168.1.10")

        sev = first["severity"]
        res = self.client.get(f"/api/vulnerabilities/?severity={sev}")
        self.assertTrue(all(v["severity"] == sev for v in res.data["results"]))
        res = self.client.get("/api/vulnerabilities/?search=zzz-no-match")
        self.assertEqual(res.data["count"], 0)

    def test_auth_config_is_public(self):
        res = self.client.get("/api/auth/config/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"registration_enabled": False})

    def test_page_size_param_is_capped(self):
        self.login()
        for i in range(25):
            Target.objects.create(
                name=f"t{i}", target_type="ip", value=f"10.0.0.{i + 1}", created_by=self.user
            )
        self.assertEqual(len(self.client.get("/api/targets/").data["results"]), 20)
        self.assertEqual(len(self.client.get("/api/targets/?page_size=50").data["results"]), 25)

    def test_users_cannot_see_or_scan_each_others_targets(self):
        target = Target.objects.create(
            name="Bob box", target_type="ip", value="10.0.0.5", created_by=self.other
        )
        self.login("alice")
        self.assertEqual(self.client.get("/api/targets/").data["count"], 0)
        res = self.client.post(
            "/api/scans/", {"name": "sneaky", "target": target.id}, format="json"
        )
        self.assertEqual(res.status_code, 400)
