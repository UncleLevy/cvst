from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.scans.models import Scan
from apps.targets.models import Target
from apps.vulnerabilities.models import Vulnerability
from apps.vulnerabilities.scoring import risk_score

User = get_user_model()


class ReportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="S3cure-pass-123", role="analyst")
        self.other = User.objects.create_user("bob", password="S3cure-pass-123", role="analyst")
        target = Target.objects.create(name="Lab", target_type="ip", value="10.0.0.5", created_by=self.user)
        self.scan = Scan.objects.create(name="Lab sweep", target=target, created_by=self.user, status="completed")
        for title, sev, cvss, cve in [
            ("Telnet exposed <b>x</b> & more", "high", None, ""),
            ("Apache RCE", "critical", 9.8, "CVE-2021-41773"),
            ("Missing CSP", "medium", None, ""),
        ]:
            Vulnerability.objects.create(
                scan=self.scan, title=title, severity=sev, cvss_score=cvss, cve_id=cve, service="telnet" if "Telnet" in title else "http",
                risk_score=risk_score(sev, cvss, cve, "telnet" if "Telnet" in title else "http"),
                description="Desc <script>", evidence="Evidence & <tags>", recommendation="Fix it",
                references=["https://example.com/a"], source="web",
            )
        self.client.force_authenticate(self.user)

    def test_report_json_is_prioritised(self):
        res = self.client.get(f"/api/reports/scans/{self.scan.id}/")
        self.assertEqual(res.status_code, 200)
        data = res.data
        self.assertEqual([f["title"] for f in data["findings"]][0], "Apache RCE")
        self.assertEqual([f["rank"] for f in data["findings"]], [1, 2, 3])
        self.assertEqual(data["by_priority"]["P1"], 1)
        self.assertEqual(data["overall_risk"], "Critical")
        self.assertFalse(data["simulated"])

    def test_pdf_is_generated_and_markup_is_escaped(self):
        res = self.client.get(f"/api/reports/scans/{self.scan.id}/pdf/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))
        self.assertGreater(len(res.content), 2000)
        self.assertIn("attachment", res["Content-Disposition"])

    def test_empty_report_renders(self):
        self.scan.vulnerabilities.all().delete()
        res = self.client.get(f"/api/reports/scans/{self.scan.id}/pdf/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_access_rules(self):
        running = Scan.objects.create(name="r", target=self.scan.target, created_by=self.user, status="scanning")
        self.assertEqual(self.client.get(f"/api/reports/scans/{running.id}/").status_code, 409)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/reports/scans/{self.scan.id}/pdf/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/reports/scans/{self.scan.id}/").status_code, 401)
