"""Nmap-based network discovery.

Requires the Nmap binary on PATH and the `python-nmap` package. Only run this
against systems you own or are explicitly authorised to test.
"""
from apps.vulnerabilities.models import Vulnerability


def run_nmap_discovery(scan, target_value: str) -> int:
    """Run service detection against `target_value` and store one finding per open port.

    Returns the number of open ports recorded.
    """
    import nmap  # imported lazily: optional dependency

    # Defence in depth: values are validated when a Target is saved, but never
    # let a value that looks like an option reach the nmap command line.
    if not target_value or target_value.startswith("-") or any(c.isspace() for c in target_value):
        raise ValueError(f"Refusing to scan invalid target value: {target_value!r}")

    nm = nmap.PortScanner()
    nm.scan(hosts=target_value, arguments="-sV -T4 --top-ports 100")

    findings = []
    for host in nm.all_hosts():
        for proto in nm[host].all_protocols():
            for port, info in nm[host][proto].items():
                if info.get("state") != "open":
                    continue
                name = info.get("name") or "unknown"
                product = info.get("product", "")
                version = info.get("version", "")

                title = f"Open port {port}/{proto} - {name}"
                if product:
                    title += f" ({product} {version})".rstrip()

                findings.append(
                    Vulnerability(
                        scan=scan,
                        title=title,
                        description=f"Host {host}: service detected: {name} {product} {version}".strip(),
                        severity="info",
                        port=port,
                        service=name,
                        cvss_score=0.0,
                    )
                )

                # Minimal CVE matching example; replace with an NVD lookup later.
                if "apache" in product.lower() and "2.4.49" in version:
                    findings.append(
                        Vulnerability(
                            scan=scan,
                            cve_id="CVE-2021-41773",
                            title="Apache HTTP Server path traversal / RCE",
                            description="Apache 2.4.49 is affected by CVE-2021-41773.",
                            severity="critical",
                            cvss_score=9.8,
                            port=port,
                            service=name,
                        )
                    )

    Vulnerability.objects.bulk_create(findings)
    return len(findings)
