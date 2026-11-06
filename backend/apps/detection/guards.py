"""Safety checks applied before any scanner touches the network.

CVST runs on a server on behalf of several users, so a scan target must not be
usable to reach the server's own loopback services or cloud metadata endpoints.
Private LAN ranges stay allowed because scanning internal networks is a core use.
"""
import ipaddress
import socket

from django.conf import settings


class TargetNotAllowed(ValueError):
    """Raised when a target resolves somewhere scanners must not go."""


def _blocked_reason(ip: ipaddress._BaseAddress) -> str | None:
    if ip.is_link_local:  # includes 169.254.169.254 cloud metadata
        return "link-local / cloud metadata addresses are never scanned"
    if ip.is_multicast or ip.is_unspecified or ip.is_reserved:
        return "multicast, unspecified and reserved addresses are not scannable"
    if ip.is_loopback and not settings.CVST_ALLOW_LOOPBACK_TARGETS:
        return "loopback targets are disabled (set CVST_ALLOW_LOOPBACK_TARGETS=True to test your own machine)"
    return None


def _check_ip(ip) -> None:
    reason = _blocked_reason(ip)
    if reason:
        raise TargetNotAllowed(f"Target {ip} refused: {reason}.")


def assert_scannable(host: str) -> None:
    """Raise TargetNotAllowed if `host` (IP, CIDR range or hostname) is off limits."""
    if not host:
        raise TargetNotAllowed("Empty target.")

    if "/" in host:
        net = ipaddress.ip_network(host, strict=False)
        _check_ip(net.network_address)
        _check_ip(net.broadcast_address)
        return

    try:
        _check_ip(ipaddress.ip_address(host))
        return
    except TargetNotAllowed:
        raise
    except ValueError:
        pass  # a hostname: resolve it below

    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise TargetNotAllowed(f"Could not resolve {host!r}: {exc}") from exc
    for info in infos:
        _check_ip(ipaddress.ip_address(info[4][0]))
