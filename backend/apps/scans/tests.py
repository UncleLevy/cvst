import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
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

    @override_settings(CVST_REAL_SCANS=False, CVST_SCAN_RUNNER="celery")
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
                "/api/scans/",
                {"name": "First scan", "target": target_id, "authorization_confirmed": True},
                format="json",
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

        for key in ("evidence", "recommendation", "references", "source"):
            self.assertIn(key, first)
        self.assertEqual(first["source"], "simulated")

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
            "/api/scans/",
            {"name": "sneaky", "target": target.id, "authorization_confirmed": True},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_scan_requires_authorization_confirmation(self):
        self.login()
        target = Target.objects.create(
            name="Mine", target_type="ip", value="10.0.0.9", created_by=self.user
        )
        res = self.client.post("/api/scans/", {"name": "x", "target": target.id}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("authorization_confirmed", res.data)

    def test_web_scan_rejects_network_range(self):
        self.login()
        target = Target.objects.create(
            name="Range", target_type="network", value="10.0.0.0/24", created_by=self.user
        )
        res = self.client.post(
            "/api/scans/",
            {"name": "x", "target": target.id, "scan_type": "web", "authorization_confirmed": True},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("scan_type", res.data)

    @override_settings(CVST_REAL_SCANS=True)
    def test_real_scan_stores_scanner_findings_and_failures(self):
        target = Target.objects.create(
            name="Web", target_type="url", value="https://example.test", created_by=self.user
        )
        scan = Scan.objects.create(
            name="real", target=target, scan_type="web", created_by=self.user, authorization_confirmed=True
        )
        finding = {
            "title": "Missing Content-Security-Policy header", "severity": "medium", "cvss_score": None,
            "port": 443, "service": "https", "description": "d", "evidence": "e",
            "recommendation": "r", "references": ["https://example.test/ref"], "cve_id": "",
        }
        with patch("apps.detection.web_scanner.run_web_scan", return_value=[finding]):
            run_scan_task.apply(args=[scan.id])
        scan.refresh_from_db()
        self.assertEqual(scan.status, "completed")
        vuln = scan.vulnerabilities.get()
        self.assertEqual((vuln.source, vuln.evidence, vuln.recommendation), ("web", "e", "r"))
        self.assertEqual(vuln.references, ["https://example.test/ref"])

        with patch("apps.detection.web_scanner.run_web_scan", side_effect=RuntimeError("boom")):
            run_scan_task.apply(args=[scan.id])
        scan.refresh_from_db()
        self.assertEqual(scan.status, "failed")
        self.assertIn("boom", scan.error_message)
        self.assertEqual(scan.vulnerabilities.count(), 0)


class GuardTests(SimpleTestCase):
    def test_blocks_metadata_and_loopback_but_allows_private(self):
        from apps.detection.guards import TargetNotAllowed, assert_scannable

        with self.assertRaises(TargetNotAllowed):
            assert_scannable("169.254.169.254")
        with self.assertRaises(TargetNotAllowed):
            assert_scannable("127.0.0.1")
        with self.assertRaises(TargetNotAllowed):
            assert_scannable("127.0.0.0/24")
        assert_scannable("192.168.1.10")
        assert_scannable("10.0.0.0/24")
        with override_settings(CVST_ALLOW_LOOPBACK_TARGETS=True):
            assert_scannable("127.0.0.1")


class NmapParsingTests(SimpleTestCase):
    def test_findings_from_scan(self):
        from apps.detection.nmap_scanner import findings_from_scan

        ports = {
            21: {"state": "open", "name": "ftp", "product": "vsftpd", "version": "2.3.4"},
            23: {"state": "open", "name": "telnet", "product": "", "version": ""},
            25: {"state": "closed", "name": "smtp"},
        }
        host = MagicMock()
        host.all_protocols.return_value = ["tcp"]
        host.__getitem__.side_effect = lambda proto: ports
        nm = MagicMock()
        nm.all_hosts.return_value = ["10.0.0.5"]
        nm.__getitem__.side_effect = lambda h: host

        findings = findings_from_scan(nm)
        titles = [f["title"] for f in findings]
        self.assertFalse(any("25/" in t for t in titles))  # closed port ignored
        cve = [f for f in findings if f["cve_id"] == "CVE-2011-2523"]
        self.assertEqual(len(cve), 1)
        self.assertEqual((cve[0]["severity"], cve[0]["cvss_score"]), ("critical", 9.8))
        self.assertTrue(any(f["severity"] == "high" and "Telnet" in f["title"] for f in findings))
        self.assertTrue(all(f["recommendation"] and f["evidence"] for f in findings))


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/.env":
            body = b"SECRET_KEY=abc123\nDB_PASSWORD=hunter2\n"
        else:
            body = b"<html>hello</html>"
        self.send_response(200 if self.path in ("/", "/.env") else 404)
        self.send_header("Server", "Apache/2.4.49")
        self.send_header("Set-Cookie", "sid=abc; Path=/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Allow", "GET, POST, TRACE")
        self.send_header("Content-Length", "0")
        self.end_headers()


@override_settings(CVST_ALLOW_LOOPBACK_TARGETS=True)
class WebScannerTests(SimpleTestCase):
    def test_scan_local_server(self):
        from apps.detection.web_scanner import run_web_scan

        server = HTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            target = SimpleNamespace(
                target_type="url", value=f"http://127.0.0.1:{server.server_port}/"
            )
            findings = run_web_scan(target)
        finally:
            server.shutdown()
            server.server_close()

        titles = [f["title"] for f in findings]
        self.assertIn("Site served over unencrypted HTTP", titles)
        self.assertIn("Missing Content-Security-Policy header", titles)
        self.assertIn("Exposed environment file", titles)
        self.assertIn("HTTP TRACE method enabled", titles)
        self.assertTrue(any(t.startswith("Version disclosed in Server") for t in titles))
        self.assertTrue(any(t.startswith("Cookie 'sid' missing") for t in titles))
        env = next(f for f in findings if f["title"] == "Exposed environment file")
        self.assertNotIn("hunter2", env["evidence"])  # secrets are never stored
        self.assertTrue(all(f["recommendation"] and f["evidence"] for f in findings))

    def test_loopback_refused_by_default(self):
        from apps.detection.guards import TargetNotAllowed
        from apps.detection.web_scanner import run_web_scan

        with override_settings(CVST_ALLOW_LOOPBACK_TARGETS=False):
            with self.assertRaises(TargetNotAllowed):
                run_web_scan(SimpleNamespace(target_type="url", value="http://127.0.0.1:9/"))


class ThreadRunnerTests(APITestCase):
    def test_thread_runner_starts_scan_without_celery(self):
        from apps.scans.views import enqueue_scan

        user = User.objects.create_user("carol", password="S3cure-pass-123", role="analyst")
        target = Target.objects.create(name="t", target_type="ip", value="10.0.0.7", created_by=user)
        scan = Scan.objects.create(name="s", target=target, created_by=user)
        with override_settings(CVST_SCAN_RUNNER="thread"), patch("apps.scans.views.threading.Thread") as thread:
            enqueue_scan(scan)
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs["daemon"])
        thread.return_value.start.assert_called_once()
