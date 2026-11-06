"""NVD (National Vulnerability Database) lookups via the public CVE API 2.0.

* `lookup_cve("CVE-2021-41773")` -> normalised dict (description, CVSS score/vector, references)
* `lookup_cpe(cpe)` -> CVEs whose NVD configuration matches a product+version
* `enrich_finding(finding)` -> fills CVSS/description/references on a finding dict

Everything here is best effort: network problems raise `NvdError`, and callers
decide whether that is fatal. Responses are cached so repeat scans stay cheap.
Set NVD_API_KEY for a higher rate limit (https://nvd.nist.gov/developers/request-an-api-key).
"""
import re

import requests
from django.conf import settings
from django.core.cache import cache

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
CACHE_SECONDS = 24 * 3600
TIMEOUT = 10


class NvdError(Exception):
    """The NVD could not be reached or returned something unusable."""


class CveNotFound(NvdError):
    pass


def _get(params: dict) -> dict:
    headers = {"User-Agent": "CVST/0.3"}
    key = getattr(settings, "NVD_API_KEY", "")
    if key:
        headers["apiKey"] = key
    try:
        resp = requests.get(NVD_URL, params=params, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise NvdError(f"Could not reach the NVD: {exc}") from exc
    if resp.status_code in (403, 429):
        raise NvdError("NVD rate limit reached; try again shortly or set NVD_API_KEY.")
    if resp.status_code != 200:
        raise NvdError(f"NVD returned HTTP {resp.status_code}.")
    try:
        return resp.json()
    except ValueError as exc:
        raise NvdError("NVD returned invalid JSON.") from exc


def _severity(score: float | None, label: str = "") -> str:
    from .scoring import severity_from_score

    if label and label.lower() in {"critical", "high", "medium", "low"}:
        return label.lower()
    return severity_from_score(score) if score is not None else "info"


def parse_cve(item: dict) -> dict:
    """Normalise one `vulnerabilities[]` entry from the NVD response."""
    cve = item["cve"]
    description = next((d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"), "")

    score = vector = version = label = None
    for key, ver in (("cvssMetricV31", "3.1"), ("cvssMetricV30", "3.0"), ("cvssMetricV2", "2.0")):
        metrics = cve.get("metrics", {}).get(key) or []
        if not metrics:
            continue
        metric = next((m for m in metrics if m.get("type") == "Primary"), metrics[0])
        data = metric.get("cvssData", {})
        score, vector, version = data.get("baseScore"), data.get("vectorString"), ver
        label = data.get("baseSeverity") or metric.get("baseSeverity")
        break

    refs = []
    for ref in cve.get("references", []):
        url = ref.get("url", "")
        if url.startswith(("http://", "https://")) and url not in refs:
            refs.append(url)

    return {
        "cve_id": cve["id"],
        "description": description,
        "cvss_score": score,
        "cvss_vector": vector or "",
        "cvss_version": version or "",
        "severity": _severity(score, label or ""),
        "references": refs[:8],
        "published": cve.get("published", ""),
        "last_modified": cve.get("lastModified", ""),
    }


def lookup_cve(cve_id: str) -> dict:
    cve_id = cve_id.strip().upper()
    if not CVE_RE.match(cve_id):
        raise CveNotFound(f"{cve_id!r} is not a valid CVE identifier.")
    cache_key = f"nvd:cve:{cve_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = _get({"cveId": cve_id})
    vulns = data.get("vulnerabilities") or []
    if not vulns:
        raise CveNotFound(f"{cve_id} was not found in the NVD.")
    result = parse_cve(vulns[0])
    cache.set(cache_key, result, CACHE_SECONDS)
    return result


def cpe_to_23(cpe: str) -> str | None:
    """Convert Nmap's `cpe:/a:vendor:product:version` to a CPE 2.3 string; None if no version."""
    if cpe.startswith("cpe:2.3:"):
        parts = cpe.split(":")
        return cpe if len(parts) >= 6 and parts[5] not in ("*", "-", "") else None
    if not cpe.startswith("cpe:/"):
        return None
    parts = cpe[5:].split(":")  # type, vendor, product, version, ...
    if len(parts) < 4 or not all(parts[:4]):
        return None
    return "cpe:2.3:" + ":".join(parts[:4]) + ":*:*:*:*:*:*:*"


def lookup_cpe(cpe: str, limit: int = 3) -> list[dict]:
    """Highest-scoring CVEs NVD associates with this exact product version."""
    cpe23 = cpe_to_23(cpe)
    if not cpe23:
        return []
    cache_key = f"nvd:cpe:{cpe23}"
    cached = cache.get(cache_key)
    if cached is None:
        data = _get({"virtualMatchString": cpe23, "resultsPerPage": 50})
        cached = [parse_cve(v) for v in data.get("vulnerabilities", [])]
        cache.set(cache_key, cached, CACHE_SECONDS)
    scored = [c for c in cached if c["cvss_score"] is not None]
    scored.sort(key=lambda c: c["cvss_score"], reverse=True)
    return scored[:limit]


def apply_cve(finding: dict, info: dict) -> dict:
    """Merge NVD data into a finding dict (works for dicts and is idempotent)."""
    if info["cvss_score"] is not None:
        finding["cvss_score"] = info["cvss_score"]
        finding["cvss_vector"] = info["cvss_vector"]
        finding["severity"] = info["severity"]
    if not finding.get("description"):
        finding["description"] = info["description"]
    refs = list(finding.get("references") or [])
    nvd_url = f"https://nvd.nist.gov/vuln/detail/{info['cve_id']}"
    for url in [nvd_url, *info["references"]]:
        if url not in refs:
            refs.append(url)
    finding["references"] = refs[:10]
    return finding


def enrich_finding(finding: dict) -> dict:
    """Look up finding['cve_id'] and merge the NVD data in. Raises NvdError on failure."""
    return apply_cve(finding, lookup_cve(finding["cve_id"]))
