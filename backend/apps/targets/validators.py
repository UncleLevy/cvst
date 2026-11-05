"""Validation of scan target values.

Target values end up as arguments to external scanners (Nmap), so they are
validated strictly: no whitespace, no leading dashes, and the value must match
the declared target type.
"""
import ipaddress
import re
from urllib.parse import urlparse

HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)

# Largest IPv4 range accepted (/16 = 65,536 addresses).
MIN_IPV4_PREFIX = 16


def validate_target_value(target_type: str, value: str) -> str:
    """Return the cleaned value or raise ValueError with a readable message."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Value is required.")
    if value.startswith("-"):
        raise ValueError("Value must not start with a dash.")
    if any(ch.isspace() for ch in value):
        raise ValueError("Value must not contain whitespace.")

    if target_type == "ip":
        try:
            ipaddress.ip_address(value)
        except ValueError:
            raise ValueError("Enter a valid IPv4 or IPv6 address.") from None
    elif target_type == "network":
        try:
            net = ipaddress.ip_network(value, strict=False)
        except ValueError:
            raise ValueError("Enter a valid network range in CIDR form, e.g. 192.168.1.0/24.") from None
        if net.version == 4 and net.prefixlen < MIN_IPV4_PREFIX:
            raise ValueError(f"Network range too large; use /{MIN_IPV4_PREFIX} or smaller.")
        value = str(net)
    elif target_type == "hostname":
        if not HOSTNAME_RE.match(value):
            raise ValueError("Enter a valid hostname, e.g. server.example.com.")
    elif target_type == "url":
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Enter a full http(s) URL, e.g. https://example.com.")
    else:
        raise ValueError("Unknown target type.")
    return value


def target_host(target) -> str:
    """The host/IP/range to hand to a network scanner for this target."""
    if target.target_type == "url":
        return urlparse(target.value).hostname or ""
    return target.value
