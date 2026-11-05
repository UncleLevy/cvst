"""Nmap-based network discovery.

Requires the Nmap binary on PATH and the `python-nmap` package. Only run this
against systems you own or are explicitly authorised to test.

`run_nmap_discovery` returns a list of finding dicts (see apps.scans.tasks);
it never writes to the database itself, which keeps it easy to test.
"""
from .guards import assert_scannable

NMAP_ARGS = "-sV -T4 --top-ports 100 --host-timeout 180s"

NMAP_REF = "https://nmap.org/book/man-version-detection.html"

# service name (as reported by Nmap) -> exposure finding.
# These are exposure ratings, not CVSS scores, so cvss_score stays unset.
RISKY_SERVICES = {
    "telnet": (
        "Telnet service exposed", "high",
        "Telnet transmits credentials and session data in clear text.",
        "Disable Telnet and use SSH. If it must stay, restrict it to a management network.",
    ),
    "ftp": (
        "FTP service exposed", "medium",
        "FTP sends credentials in clear text unless wrapped in TLS.",
        "Replace FTP with SFTP/FTPS, disable anonymous access and restrict the source addresses.",
    ),
    "microsoft-ds": (
        "SMB file sharing reachable", "high",
        "SMB is reachable from the scanned network position and is a frequent target of worms and credential attacks.",
        "Block SMB at the network boundary, disable SMBv1 and require signing.",
    ),
    "netbios-ssn": (
        "NetBIOS session service reachable", "medium",
        "NetBIOS exposes host and share information to the network.",
        "Disable NetBIOS over TCP/IP where it is not required and filter ports 137-139.",
    ),
    "ms-wbt-server": (
        "Remote Desktop (RDP) reachable", "high",
        "RDP is directly reachable and is heavily targeted by brute-force and exploit attempts.",
        "Place RDP behind a VPN or gateway, enable Network Level Authentication and enforce MFA.",
    ),
    "vnc": (
        "VNC remote access reachable", "high",
        "VNC often uses weak authentication and no transport encryption.",
        "Tunnel VNC through SSH or a VPN and require strong credentials.",
    ),
    "mysql": (
        "MySQL/MariaDB reachable from the network", "medium",
        "Database servers should not accept connections from general network segments.",
        "Bind the database to loopback or a private interface and allow only application hosts through the firewall.",
    ),
    "postgresql": (
        "PostgreSQL reachable from the network", "medium",
        "Database servers should not accept connections from general network segments.",
        "Restrict listen_addresses and pg_hba.conf to application hosts.",
    ),
    "ms-sql-s": (
        "Microsoft SQL Server reachable from the network", "medium",
        "Database servers should not accept connections from general network segments.",
        "Restrict SQL Server to application hosts with firewall rules.",
    ),
    "mongodb": (
        "MongoDB reachable from the network", "high",
        "Exposed MongoDB instances are routinely found without authentication.",
        "Enable authentication, bind to private interfaces and firewall the port.",
    ),
    "redis": (
        "Redis reachable from the network", "high",
        "Redis has no authentication by default and can lead to remote code execution when exposed.",
        "Bind Redis to loopback, set a password/ACLs and firewall the port.",
    ),
    "memcached": (
        "Memcached reachable from the network", "medium",
        "Open memcached servers leak cached data and can be abused for amplification attacks.",
        "Bind to loopback or a private interface and firewall the port.",
    ),
    "nfs": (
        "NFS service reachable", "medium",
        "NFS exports may be mountable by untrusted hosts.",
        "Restrict exports to specific client addresses and use Kerberos where possible.",
    ),
    "rpcbind": (
        "RPC portmapper reachable", "low",
        "rpcbind reveals which RPC services run on the host.",
        "Filter port 111 from untrusted networks.",
    ),
}

# (product substring, version substring, CVE, title, severity, cvss, description, recommendation)
KNOWN_VULNERABLE = [
    (
        "apache httpd", "2.4.49", "CVE-2021-41773",
        "Apache HTTP Server 2.4.49 path traversal / RCE", "critical", 9.8,
        "Apache HTTP Server 2.4.49 is affected by a path traversal flaw that can expose files and, with CGI enabled, allow remote code execution.",
        "Upgrade Apache HTTP Server to 2.4.51 or later.",
    ),
    (
        "apache httpd", "2.4.50", "CVE-2021-42013",
        "Apache HTTP Server 2.4.50 path traversal / RCE", "critical", 9.8,
        "The fix for CVE-2021-41773 in 2.4.50 was incomplete and still allows path traversal and remote code execution.",
        "Upgrade Apache HTTP Server to 2.4.51 or later.",
    ),
    (
        "vsftpd", "2.3.4", "CVE-2011-2523",
        "vsftpd 2.3.4 backdoor", "critical", 9.8,
        "vsftpd 2.3.4 distributed from a compromised source archive contains a backdoor that opens a root shell.",
        "Replace vsftpd with a trusted, current release from your OS vendor.",
    ),
    (
        "proftpd", "1.3.5", "CVE-2015-3306",
        "ProFTPD 1.3.5 mod_copy arbitrary file copy", "critical", 9.8,
        "The mod_copy module in ProFTPD 1.3.5 lets unauthenticated clients copy files, which can lead to remote code execution.",
        "Upgrade ProFTPD or disable mod_copy.",
    ),
]


def _nvd(cve: str) -> list[str]:
    return [f"https://nvd.nist.gov/vuln/detail/{cve}"]


def findings_from_scan(nm) -> list[dict]:
    """Turn a python-nmap PortScanner result into finding dicts."""
    findings: list[dict] = []
    for host in nm.all_hosts():
        for proto in nm[host].all_protocols():
            for port, info in sorted(nm[host][proto].items()):
                if info.get("state") != "open":
                    continue
                name = info.get("name") or "unknown"
                product = info.get("product", "") or ""
                version = info.get("version", "") or ""
                banner = " ".join(p for p in (product, version, info.get("extrainfo", "")) if p).strip()
                evidence = f"{host} {port}/{proto} open {name}" + (f" — {banner}" if banner else "")

                title = f"Open port {port}/{proto} ({name})"
                if product:
                    title = f"Open port {port}/{proto} — {product} {version}".rstrip()
                findings.append({
                    "title": title,
                    "severity": "info",
                    "cvss_score": None,
                    "port": port,
                    "service": name,
                    "description": f"Host {host} accepts connections on {port}/{proto}. Detected service: {name} {banner}".strip(),
                    "evidence": evidence,
                    "recommendation": "Confirm this service is intended to be reachable and close the port if it is not.",
                    "references": [NMAP_REF],
                    "cve_id": "",
                })

                risky = RISKY_SERVICES.get(name)
                if risky:
                    r_title, r_sev, r_desc, r_fix = risky
                    findings.append({
                        "title": f"{r_title} on port {port}",
                        "severity": r_sev,
                        "cvss_score": None,
                        "port": port,
                        "service": name,
                        "description": r_desc,
                        "evidence": evidence,
                        "recommendation": r_fix,
                        "references": [],
                        "cve_id": "",
                    })

                haystack = f"{product} {name}".lower()
                for prod, ver, cve, k_title, k_sev, k_cvss, k_desc, k_fix in KNOWN_VULNERABLE:
                    if prod in haystack and version.startswith(ver):
                        findings.append({
                            "title": k_title,
                            "severity": k_sev,
                            "cvss_score": k_cvss,
                            "port": port,
                            "service": name,
                            "description": k_desc,
                            "evidence": evidence,
                            "recommendation": k_fix,
                            "references": _nvd(cve),
                            "cve_id": cve,
                        })
    return findings


def run_nmap_discovery(target_value: str) -> list[dict]:
    """Run service detection against `target_value`; return finding dicts."""
    import nmap  # imported lazily: optional dependency

    # Defence in depth: values are validated when a Target is saved, but never
    # let a value that looks like an option reach the nmap command line.
    if not target_value or target_value.startswith("-") or any(c.isspace() for c in target_value):
        raise ValueError(f"Refusing to scan invalid target value: {target_value!r}")
    assert_scannable(target_value)

    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=target_value, arguments=NMAP_ARGS)
    except nmap.PortScannerError as exc:
        raise RuntimeError(
            "Nmap is not installed or could not run. Install it (e.g. `sudo apt install nmap`) "
            f"and make sure it is on PATH. Details: {exc}"
        ) from exc

    return findings_from_scan(nm)
