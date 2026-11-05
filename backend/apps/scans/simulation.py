"""Demo-mode finding pools.

Used when real scanning is off (CVST_USE_NMAP=False). Findings are picked
deterministically per scan so a re-run of the same scan looks the same, and
every description is prefixed with [SIMULATED] so they are never mistaken for
real results.
"""
import random

NETWORK = [
    ("SSH password authentication enabled", "medium", 5.3, 22, "ssh",
     "The SSH daemon accepts password logins, allowing credential guessing against exposed hosts."),
    ("Telnet service exposed", "high", 7.5, 23, "telnet",
     "An unencrypted Telnet service responds on the network boundary. Credentials traverse in clear text."),
    ("SMB reachable from untrusted network", "high", 7.6, 445, "smb",
     "SMB file sharing is reachable outside the trusted segment. Restrict access to administration ranges."),
    ("RDP exposed to the internet", "critical", 9.8, 3389, "rdp",
     "Remote Desktop is directly reachable. Place it behind a VPN or bastion host."),
    ("SNMP default community string accepted", "high", 7.1, 161, "snmp",
     'The device answers SNMP queries with the default "public" community string, leaking configuration data.'),
    ("Outdated service banner discloses version", "low", 3.7, 80, "http",
     "Version banners reveal the exact software build, easing targeted exploitation."),
    ("NFS export without authentication", "high", 7.5, 2049, "nfs",
     "An NFS share is exported to any host. Mounting it requires no authentication."),
    ("Database service listening on all interfaces", "medium", 6.5, 3306, "mysql",
     "The database accepts connections from any interface rather than loopback only."),
    ("Host responds to ICMP timestamp requests", "info", 0.0, None, "icmp",
     "Timestamp replies let an observer estimate host uptime and clock skew."),
    ("FTP anonymous login permitted", "medium", 5.8, 21, "ftp",
     "Anonymous FTP sessions are accepted, exposing browsable directory listings."),
]

WEB = [
    ("Reflected cross-site scripting in search parameter", "high", 7.4, 443, "https",
     "The q parameter is echoed into the response without encoding, allowing script injection."),
    ("Missing Content-Security-Policy header", "medium", 5.3, 443, "https",
     "No CSP is returned, so the browser applies no restrictions on script origins."),
    ("TLS 1.0 still accepted", "medium", 6.1, 443, "tls",
     "The endpoint negotiates TLS 1.0, which is deprecated and offers weak cipher suites."),
    ("Directory listing enabled on /backup", "high", 7.5, 443, "https",
     "The web server returns an index of /backup, exposing archived resources."),
    ("Session cookie missing Secure attribute", "medium", 4.3, 443, "https",
     "The session cookie can be transmitted over plain HTTP, risking interception."),
    ("Authentication endpoint lacks rate limiting", "high", 7.2, 443, "https",
     "Repeated login attempts are not throttled, enabling credential stuffing."),
    ("Outdated JavaScript library detected", "low", 3.5, 443, "javascript",
     "A client-side library version with known issues is bundled in the page."),
    ("Open redirect in return parameter", "medium", 5.4, 443, "https",
     "The return parameter accepts external hosts, enabling convincing phishing redirects."),
    ("Default administrative credentials accepted", "critical", 9.8, 443, "https",
     "The administrative panel accepts the vendor default password."),
    ("Server banner exposes technology versions", "low", 3.1, 443, "https",
     "Response headers disclose framework and server versions."),
]

POOLS = {"network": NETWORK, "web": WEB, "full": NETWORK + WEB}


def simulated_findings(scan) -> list[dict]:
    """Return 3-7 simulated finding dicts for this scan, stable per scan/target."""
    pool = list(POOLS.get(scan.scan_type, NETWORK))
    rng = random.Random(f"{scan.id}:{scan.target.value}")
    count = min(len(pool), 3 + rng.randrange(5))
    picked = rng.sample(pool, count)
    return [
        {
            "title": title,
            "severity": severity,
            "cvss_score": cvss,
            "port": port,
            "service": service,
            "description": f"[SIMULATED] {text}",
        }
        for title, severity, cvss, port, service, text in picked
    ]
