from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from apps.scans.models import Scan
from apps.scans.tasks import run_scan_task
from apps.targets.models import Target

from . import nvd, scoring
from .models import Vulnerability

User = get_user_model()

NVD_RESPONSE = {
    "vulnerabilities": [{
        "cve": {
            "id": "CVE-2021-41773",
            "descriptions": [{"lang": "es", "value": "x"}, {"lang": "en", "value": "Path traversal in Apache."}],
            "metrics": {"cvssMetricV31": [{
                "type": "Primary",
                "cvssData": {
                    "baseScore": 7.5, "baseSeverity": "HIGH",
                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                },
            }]},
            "references": [{"url": "https://httpd.apache.org/security"}, {"url": "javascript:alert(1)"}],
            "published": "2021-10-05T09:15:00.000",
        }
    }]
}


def fake_response(payload, status=200):
    resp = MagicMock(status_code=status)
    resp.json.return_value = payload
    return resp


class ScoringTests(SimpleTestCase):
    def test_cvss_v3_matches_published_scores(self):
        cases = {
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H": 9.8,
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N": 6.1,
            "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N": 5.5,
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H": 10.0,
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N": 0.0,
        }
        for vector, expected in cases.items():
            self.assertEqual(scoring.cvss_v3_score(vector), expected, vector)
        self.assertIsNone(scoring.cvss_v3_score("not a vector"))
        self.assertIsNone(scoring.cvss_v3_score("CVSS:3.1/AV:X"))

    def test_severity_and_priority_buckets(self):
        self.assertEqual(scoring.severity_from_score(9.8), "critical")
        self.assertEqual(scoring.severity_from_score(7.0), "high")
        self.assertEqual(scoring.severity_from_score(4.0), "medium")
        self.assertEqual(scoring.severity_from_score(0.1), "low")
        self.assertEqual(scoring.severity_from_score(0), "info")
        crit_cve = scoring.risk_score("critical", 9.8, "CVE-2021-41773", "http")
        self.assertEqual((crit_cve, scoring.priority_for(crit_cve)), (100.0, "P1"))
        self.assertEqual(scoring.priority_for(scoring.risk_score("high", None, "", "telnet")), "P2")
        self.assertEqual(scoring.priority_for(scoring.risk_score("medium", None)), "P3")
        self.assertEqual(scoring.priority_for(scoring.risk_score("info", None)), "P4")

    def test_finalise_derives_score_from_vector(self):
        f = scoring.finalise({"severity": "info", "cvss_score": None,
                              "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"})
        self.assertEqual((f["cvss_score"], f["severity"], f["risk_score"]), (9.8, "critical", 98.0))


class NvdClientTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_lookup_parses_and_caches(self):
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response(NVD_RESPONSE)) as get:
            info = nvd.lookup_cve("cve-2021-41773")
            again = nvd.lookup_cve("CVE-2021-41773")
        self.assertEqual(get.call_count, 1)  # second call served from cache
        self.assertEqual(info, again)
        self.assertEqual((info["cvss_score"], info["severity"], info["cvss_version"]), (7.5, "high", "3.1"))
        self.assertEqual(info["description"], "Path traversal in Apache.")
        self.assertEqual(info["references"], ["https://httpd.apache.org/security"])  # javascript: dropped

    def test_errors(self):
        with self.assertRaises(nvd.CveNotFound):
            nvd.lookup_cve("not-a-cve")
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response({"vulnerabilities": []})):
            with self.assertRaises(nvd.CveNotFound):
                nvd.lookup_cve("CVE-2000-0001")
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response({}, status=429)):
            with self.assertRaises(nvd.NvdError):
                nvd.lookup_cve("CVE-2000-0002")

    def test_cpe_conversion(self):
        self.assertEqual(
            nvd.cpe_to_23("cpe:/a:apache:http_server:2.4.49"),
            "cpe:2.3:a:apache:http_server:2.4.49:*:*:*:*:*:*:*",
        )
        self.assertIsNone(nvd.cpe_to_23("cpe:/a:apache:http_server"))  # no version -> too noisy
        self.assertIsNone(nvd.cpe_to_23(""))


class NvdApiAndScanTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("alice", password="S3cure-pass-123", role="analyst")
        self.other = User.objects.create_user("bob", password="S3cure-pass-123", role="analyst")
        self.client.force_authenticate(self.user)
        target = Target.objects.create(name="t", target_type="ip", value="10.0.0.5", created_by=self.user)
        self.scan = Scan.objects.create(name="s", target=target, created_by=self.user, status="completed")

    def test_cve_lookup_endpoint(self):
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response(NVD_RESPONSE)):
            res = self.client.get("/api/vulnerabilities/cve/CVE-2021-41773/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["cvss_score"], 7.5)
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response({}, status=500)):
            self.assertEqual(self.client.get("/api/vulnerabilities/cve/CVE-2021-99999/").status_code, 502)
        self.assertEqual(self.client.get("/api/vulnerabilities/cve/garbage/").status_code, 404)

    def test_enrich_updates_finding_and_respects_ownership(self):
        v = Vulnerability.objects.create(
            scan=self.scan, title="Apache", cve_id="CVE-2021-41773", severity="info", service="http",
        )
        with patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response(NVD_RESPONSE)):
            res = self.client.post(f"/api/vulnerabilities/{v.id}/enrich/")
        self.assertEqual(res.status_code, 200, res.content)
        v.refresh_from_db()
        self.assertEqual((v.cvss_score, v.severity), (7.5, "high"))
        self.assertTrue(v.cvss_vector.startswith("CVSS:3.1/"))
        self.assertEqual(res.data["priority"], "P1")  # 75 + 10 (CVE) = 85
        self.assertIn("https://nvd.nist.gov/vuln/detail/CVE-2021-41773", v.references)

        no_cve = Vulnerability.objects.create(scan=self.scan, title="x", severity="low")
        self.assertEqual(self.client.post(f"/api/vulnerabilities/{no_cve.id}/enrich/").status_code, 400)

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f"/api/vulnerabilities/{v.id}/enrich/").status_code, 404)

    def test_findings_are_ordered_by_risk(self):
        for title, sev in [("low one", "low"), ("crit one", "critical"), ("med one", "medium")]:
            Vulnerability.objects.create(
                scan=self.scan, title=title, severity=sev,
                risk_score=scoring.risk_score(sev, None),
            )
        titles = [v["title"] for v in self.client.get("/api/vulnerabilities/").data["results"]]
        self.assertEqual(titles, ["crit one", "med one", "low one"])

    @override_settings(CVST_REAL_SCANS=True, CVST_NVD_LOOKUP=True)
    def test_scan_matches_cves_by_cpe_and_scores_findings(self):
        finding = {
            "title": "Open port 80/tcp - Apache httpd 2.4.49", "severity": "info", "cvss_score": None,
            "port": 80, "service": "http", "description": "d", "evidence": "10.0.0.5 80/tcp open http",
            "recommendation": "r", "references": [], "cve_id": "",
            "cpe": "cpe:/a:apache:http_server:2.4.49", "banner": "Apache httpd 2.4.49",
        }
        self.scan.scan_type = "network"
        self.scan.save()
        with patch("apps.detection.nmap_scanner.run_nmap_discovery", return_value=[finding]), \
                patch("apps.vulnerabilities.nvd.requests.get", return_value=fake_response(NVD_RESPONSE)):
            run_scan_task.apply(args=[self.scan.id])
        self.scan.refresh_from_db()
        self.assertEqual(self.scan.status, "completed", self.scan.error_message)
        cve = self.scan.vulnerabilities.get(cve_id="CVE-2021-41773")
        self.assertEqual((cve.cvss_score, cve.severity, cve.source), (7.5, "high", "nmap"))
        self.assertIn("backport", cve.description)
        self.assertEqual(cve.risk_score, 85.0)
        self.assertEqual(self.scan.vulnerabilities.count(), 2)

    @override_settings(CVST_REAL_SCANS=True, CVST_NVD_LOOKUP=True)
    def test_scan_survives_nvd_outage(self):
        finding = {
            "title": "Open port", "severity": "info", "cvss_score": None, "port": 80, "service": "http",
            "description": "d", "evidence": "e", "recommendation": "r", "references": [], "cve_id": "",
            "cpe": "cpe:/a:apache:http_server:2.4.49", "banner": "Apache httpd 2.4.49",
        }
        self.scan.scan_type = "network"
        self.scan.save()
        with patch("apps.detection.nmap_scanner.run_nmap_discovery", return_value=[finding]), \
                patch("apps.vulnerabilities.nvd.requests.get", side_effect=nvd.requests.ConnectionError("down")):
            run_scan_task.apply(args=[self.scan.id])
        self.scan.refresh_from_db()
        self.assertEqual(self.scan.status, "completed")
        self.assertEqual(self.scan.vulnerabilities.count(), 1)
