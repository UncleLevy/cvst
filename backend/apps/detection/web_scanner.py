"""Non-intrusive web application checks.

Only passive/low-impact requests are made (a handful of GETs plus one OPTIONS):
transport security, TLS certificate health, security headers, cookie flags,
version disclosure, risky HTTP methods and a few well-known exposed files.
There is no fuzzing, brute forcing or payload injection. Only run this against
systems you own or are explicitly authorised to test.
"""
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests

from .guards import assert_scannable

TIMEOUT = 8
MAX_BODY = 64 * 1024
MAX_REDIRECTS = 3
USER_AGENT = "CVST-Scanner/0.2 (authorised security assessment)"

OWASP_HEADERS = "https://owasp.org/www-project-secure-headers/"
MDN = "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/"


def _finding(title, severity, description, recommendation, *, evidence="", port=None, service="https",
             references=None, cvss=None, cve=""):
    return {
        "title": title,
        "severity": severity,
        "cvss_score": cvss,
        "port": port,
        "service": service,
        "description": description,
        "evidence": evidence,
        "recommendation": recommendation,
        "references": references or [],
        "cve_id": cve,
    }


class Response:
    def __init__(self, url, status, headers, cookies, body):
        self.url, self.status, self.headers, self.cookies, self.body = url, status, headers, cookies, body


def fetch(url: str, method: str = "GET", verify: bool = True, follow: bool = True) -> Response:
    """One guarded request. Every hop is checked so redirects cannot reach forbidden hosts."""
    for _ in range(MAX_REDIRECTS + 1):
        parsed = urlparse(url)
        assert_scannable(parsed.hostname or "")
        resp = requests.request(
            method, url, timeout=TIMEOUT, allow_redirects=False, verify=verify, stream=True,
            headers={"User-Agent": USER_AGENT},
        )
        try:
            body = resp.raw.read(MAX_BODY, decode_content=True) if method == "GET" else b""
            cookies = resp.raw.headers.getlist("Set-Cookie") if hasattr(resp.raw.headers, "getlist") else []
            result = Response(url, resp.status_code, resp.headers, cookies, body)
        finally:
            resp.close()
        location = resp.headers.get("Location")
        if follow and resp.status_code in (301, 302, 303, 307, 308) and location:
            url = urljoin(url, location)
            continue
        return result
    return result


def _origin(url: str) -> tuple[str, str, int]:
    p = urlparse(url)
    scheme = p.scheme
    return scheme, p.hostname or "", p.port or (443 if scheme == "https" else 80)


def candidate_urls(target) -> list[str]:
    """URLs to try for a target, best first."""
    if target.target_type == "url":
        return [target.value]
    if target.target_type == "network":
        raise ValueError("Web scans need a URL, hostname or IP address, not a network range.")
    host = f"[{target.value}]" if ":" in target.value else target.value
    return [f"https://{host}", f"http://{host}"]


def check_tls(host: str, port: int) -> list[dict]:
    """Certificate expiry and negotiated protocol (verification problems are reported elsewhere)."""
    findings = []
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                version = tls.version() or ""
                der = tls.getpeercert(binary_form=True)
    except (OSError, ssl.SSLError):
        return findings

    if version in ("TLSv1", "TLSv1.1", "SSLv3"):
        findings.append(_finding(
            f"Deprecated protocol negotiated ({version})", "medium",
            "The server negotiated a TLS version that is deprecated and considered weak.",
            "Disable TLS 1.0/1.1 and require TLS 1.2 or newer.",
            evidence=f"Negotiated protocol: {version}", port=port, service="tls",
            references=["https://datatracker.ietf.org/doc/html/rfc8996"],
        ))

    try:
        from cryptography import x509  # optional; present when installed alongside pyOpenSSL/requests extras

        cert = x509.load_der_x509_certificate(der)
        not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
        days = (not_after - datetime.now(timezone.utc)).days
        if days < 0:
            findings.append(_finding(
                "TLS certificate has expired", "high",
                "The certificate presented by the server is past its expiry date; browsers will warn or block users.",
                "Renew and deploy a valid certificate.",
                evidence=f"Expired {-days} day(s) ago ({not_after:%Y-%m-%d})", port=port, service="tls",
            ))
        elif days < 30:
            findings.append(_finding(
                "TLS certificate expires soon", "low",
                "The certificate will expire within 30 days.",
                "Renew the certificate and automate renewal (e.g. ACME).",
                evidence=f"Expires in {days} day(s) ({not_after:%Y-%m-%d})", port=port, service="tls",
            ))
    except ImportError:
        pass
    return findings


def check_headers(resp: Response, https: bool, port: int) -> list[dict]:
    h = {k.lower(): v for k, v in resp.headers.items()}
    svc = "https" if https else "http"
    out = []

    def missing(title, sev, why, fix, ref, evidence="Header not present in response."):
        out.append(_finding(title, sev, why, fix, evidence=evidence, port=port, service=svc, references=[ref]))

    if https and "strict-transport-security" not in h:
        missing("Missing Strict-Transport-Security header", "medium",
                "Without HSTS, browsers may be tricked into using HTTP, exposing users to downgrade and sniffing attacks.",
                "Send `Strict-Transport-Security: max-age=31536000; includeSubDomains`.",
                MDN + "Strict-Transport-Security")
    csp = h.get("content-security-policy", "")
    if not csp:
        missing("Missing Content-Security-Policy header", "medium",
                "No CSP is returned, so the browser applies no restrictions on script and resource origins, increasing XSS impact.",
                "Define a Content-Security-Policy that limits script, style and frame sources.",
                MDN + "Content-Security-Policy")
    if "x-frame-options" not in h and "frame-ancestors" not in csp:
        missing("Clickjacking protection missing", "low",
                "The page can be embedded in a frame on another site, enabling clickjacking.",
                "Send `X-Frame-Options: DENY` or a CSP `frame-ancestors` directive.",
                MDN + "X-Frame-Options")
    if h.get("x-content-type-options", "").lower() != "nosniff":
        missing("Missing X-Content-Type-Options header", "low",
                "Browsers may MIME-sniff responses, turning uploaded or reflected content into executable script.",
                "Send `X-Content-Type-Options: nosniff`.",
                MDN + "X-Content-Type-Options")
    if "referrer-policy" not in h:
        missing("Missing Referrer-Policy header", "info",
                "Full URLs, including sensitive paths and parameters, may leak to third parties in the Referer header.",
                "Send `Referrer-Policy: strict-origin-when-cross-origin` or stricter.",
                MDN + "Referrer-Policy")

    for name in ("server", "x-powered-by", "x-aspnet-version"):
        value = h.get(name, "")
        if any(ch.isdigit() for ch in value):
            out.append(_finding(
                f"Version disclosed in {name.title()} header", "low",
                "Response headers reveal software versions, making it easier to look up matching exploits.",
                "Remove or genericise version details in server and framework configuration.",
                evidence=f"{name.title()}: {value}", port=port, service=svc, references=[OWASP_HEADERS],
            ))

    for raw in resp.cookies:
        parts = [p.strip().lower() for p in raw.split(";")]
        cname = raw.split("=", 1)[0].strip()
        issues = []
        if https and "secure" not in parts:
            issues.append("Secure")
        if "httponly" not in parts:
            issues.append("HttpOnly")
        if not any(p.startswith("samesite=") for p in parts):
            issues.append("SameSite")
        if issues:
            out.append(_finding(
                f"Cookie '{cname}' missing {', '.join(issues)}", "medium" if "Secure" in issues else "low",
                "Cookie attributes limit exposure to network sniffing, script access and cross-site requests.",
                f"Set {', '.join(issues)} on the cookie.",
                evidence=f"Set-Cookie: {cname}=<redacted>; " + "; ".join(p for p in parts[1:]),
                port=port, service=svc, references=[MDN + "Set-Cookie"],
            ))
    return out


# path -> (title, severity, signature check, description, recommendation)
SENSITIVE_PATHS = [
    ("/.git/HEAD", "Exposed Git repository", "high",
     lambda body: body.lstrip().startswith(b"ref:"),
     "The .git directory is served publicly, allowing the full source history to be downloaded.",
     "Block access to dotfiles and directories at the web server and remove .git from the document root."),
    ("/.env", "Exposed environment file", "critical",
     lambda body: b"=" in body[:2000] and b"<html" not in body[:500].lower(),
     "A .env file is served publicly and typically contains secrets and credentials.",
     "Remove the file from the document root, block dotfiles, and rotate every secret it contained."),
    ("/phpinfo.php", "phpinfo() page exposed", "medium",
     lambda body: b"phpinfo()" in body or b"PHP Version" in body,
     "phpinfo output reveals configuration, paths and loaded modules.",
     "Delete the phpinfo page from production."),
    ("/server-status", "Apache server-status exposed", "medium",
     lambda body: b"Apache Server Status" in body,
     "The Apache status page reveals request details and internal activity.",
     "Restrict /server-status to localhost or an admin network."),
]


def check_sensitive_files(base: str, port: int, https: bool) -> list[dict]:
    out = []
    for path, title, sev, signature, desc, fix in SENSITIVE_PATHS:
        try:
            resp = fetch(urljoin(base, path), follow=False, verify=False)
        except (requests.RequestException, ValueError):
            continue
        if resp.status == 200 and signature(resp.body):
            out.append(_finding(
                title, sev, desc, fix,
                evidence=f"GET {path} → HTTP 200 ({len(resp.body)} bytes read; content not stored)",
                port=port, service="https" if https else "http", references=[OWASP_HEADERS],
            ))
    return out


def check_methods(base: str, port: int, https: bool) -> list[dict]:
    try:
        resp = fetch(base, method="OPTIONS", follow=False, verify=False)
    except (requests.RequestException, ValueError):
        return []
    allow = resp.headers.get("Allow", "")
    if "TRACE" in allow.upper():
        return [_finding(
            "HTTP TRACE method enabled", "low",
            "TRACE echoes requests back to the client and can aid cross-site tracing attacks.",
            "Disable the TRACE method on the web server.",
            evidence=f"Allow: {allow}", port=port, service="https" if https else "http",
        )]
    return []


def run_web_scan(target) -> list[dict]:
    """Run the web checks against a target; return finding dicts."""
    last_error = None
    for url in candidate_urls(target):
        findings: list[dict] = []
        scheme, host, port = _origin(url)
        https = scheme == "https"
        try:
            try:
                resp = fetch(url)
            except requests.exceptions.SSLError as exc:
                findings.append(_finding(
                    "TLS certificate not trusted", "high",
                    "The certificate could not be verified (self-signed, expired, wrong hostname or incomplete chain). "
                    "Users see browser warnings and cannot be sure who they are talking to.",
                    "Install a certificate from a trusted CA that matches the hostname, with the full chain.",
                    evidence=str(exc)[:300], port=port, service="tls",
                ))
                resp = fetch(url, verify=False)
        except ValueError:
            raise
        except requests.RequestException as exc:
            last_error = exc
            continue

        base = resp.url
        # Report on the URL the server finally answered from.
        final_scheme, _, final_port = _origin(base)
        https = final_scheme == "https"
        port = final_port

        if not https:
            findings.append(_finding(
                "Site served over unencrypted HTTP", "medium",
                "Traffic, including credentials and session cookies, can be read or modified in transit.",
                "Serve the site over HTTPS and redirect all HTTP traffic.",
                evidence=f"Final URL: {base}", port=port, service="http",
                references=["https://developer.mozilla.org/en-US/docs/Web/Security/Transport_Layer_Security"],
            ))
        else:
            findings += check_tls(host, port)
            # Does plain HTTP upgrade to HTTPS?
            try:
                plain = fetch(f"http://{host}:80/", follow=False, verify=False)
                loc = plain.headers.get("Location", "")
                if not (plain.status in (301, 302, 307, 308) and loc.startswith("https://")):
                    findings.append(_finding(
                        "HTTP does not redirect to HTTPS", "low",
                        "The site answers on plain HTTP without redirecting, so users may stay on an unencrypted connection.",
                        "Redirect all HTTP requests to HTTPS (and add HSTS).",
                        evidence=f"GET http://{host}/ → HTTP {plain.status}", port=80, service="http",
                    ))
            except (requests.RequestException, ValueError):
                pass  # port 80 closed is fine

        findings += check_headers(resp, https, port)
        findings += check_methods(base, port, https)
        findings += check_sensitive_files(base, port, https)
        return findings

    raise RuntimeError(f"Could not connect to the target over HTTPS or HTTP: {last_error}")
