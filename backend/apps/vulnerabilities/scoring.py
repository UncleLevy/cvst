"""CVSS scoring and risk prioritisation.

* `cvss_v3_score` implements the CVSS v3.0/v3.1 base-score equations from the
  FIRST specification, so a vector string alone is enough to get a score.
* `risk_score` turns a finding into a 0-100 number used to rank remediation.
* `priority_for` buckets that number into P1-P4.

Exposure findings (open Telnet, missing headers, ...) have no CVSS score, so a
nominal base score per severity is used and clearly treated as an estimate.
"""
import math

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

# Nominal CVSS-like base score for findings that have no real CVSS score.
NOMINAL_BASE = {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.5, "info": 0.5}

# Services that give an attacker direct control or data when exposed.
HIGH_VALUE_SERVICES = {
    "telnet", "ms-wbt-server", "rdp", "vnc", "microsoft-ds", "smb",
    "mysql", "postgresql", "ms-sql-s", "mongodb", "redis", "memcached", "nfs",
}

PRIORITIES = {
    "P1": "Fix immediately",
    "P2": "Fix urgently",
    "P3": "Plan a fix",
    "P4": "Monitor / backlog",
}

_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"H": 0.56, "L": 0.22, "N": 0.0}
_PR = {"unchanged": {"N": 0.85, "L": 0.62, "H": 0.27}, "changed": {"N": 0.85, "L": 0.68, "H": 0.5}}


def _roundup(value: float) -> float:
    """CVSS v3.1 Roundup: smallest number with one decimal place >= value."""
    int_input = round(value * 100000)
    if int_input % 10000 == 0:
        return int_input / 100000.0
    return (math.floor(int_input / 10000) + 1) / 10.0


def cvss_v3_score(vector: str) -> float | None:
    """Base score for a CVSS v3.x vector string, or None if it can't be parsed."""
    try:
        parts = vector.strip().split("/")
        if not parts[0].startswith("CVSS:3"):
            return None
        m = dict(p.split(":", 1) for p in parts[1:])
        scope_changed = m["S"] == "C"
        iss = 1 - (1 - _CIA[m["C"]]) * (1 - _CIA[m["I"]]) * (1 - _CIA[m["A"]])
        if scope_changed:
            impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
        else:
            impact = 6.42 * iss
        pr = _PR["changed" if scope_changed else "unchanged"][m["PR"]]
        exploitability = 8.22 * _AV[m["AV"]] * _AC[m["AC"]] * pr * _UI[m["UI"]]
        if impact <= 0:
            return 0.0
        raw = 1.08 * (impact + exploitability) if scope_changed else impact + exploitability
        return _roundup(min(raw, 10))
    except (KeyError, ValueError, AttributeError):
        return None


def severity_from_score(score: float) -> str:
    """Qualitative CVSS rating: 0 none/info, 0.1-3.9 low, 4-6.9 medium, 7-8.9 high, 9+ critical."""
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "info"


def risk_score(severity: str, cvss: float | None, cve_id: str = "", service: str = "") -> float:
    """0-100 ranking score: base score x10, +10 for a known CVE, +5 for high-value services."""
    base = cvss if cvss is not None else NOMINAL_BASE.get(severity, 0.5)
    score = base * 10
    if cve_id:
        score += 10
    if (service or "").lower() in HIGH_VALUE_SERVICES:
        score += 5
    return round(min(score, 100.0), 1)


def priority_for(score: float) -> str:
    if score >= 85:
        return "P1"
    if score >= 65:
        return "P2"
    if score >= 35:
        return "P3"
    return "P4"


def finalise(finding: dict) -> dict:
    """Fill in CVSS score/severity from a vector (if present) and compute risk_score."""
    vector = finding.get("cvss_vector") or ""
    if vector and finding.get("cvss_score") is None:
        score = cvss_v3_score(vector)
        if score is not None:
            finding["cvss_score"] = score
            finding["severity"] = severity_from_score(score)
    finding["risk_score"] = risk_score(
        finding.get("severity", "info"),
        finding.get("cvss_score"),
        finding.get("cve_id", ""),
        finding.get("service", ""),
    )
    return finding
