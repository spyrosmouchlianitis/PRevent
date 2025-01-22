import socket
import ipaddress
import os
import subprocess
from contextlib import redirect_stderr
from src.secret_manager import get_secret


def is_secret_set(secret) -> bool:
    try:
        with open(os.devnull, 'w') as hide, redirect_stderr(hide):
            get_secret(secret)
        return True
    except (ValueError, Exception):
        pass
    return False


def get_public_domain() -> str:
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback:
            return ''

        domain = socket.getfqdn()
        if domain in ("localhost", hostname) or "." not in domain:
            return ''

        resolved_ip = socket.gethostbyname(domain)
        if ipaddress.ip_address(resolved_ip).is_private or ipaddress.ip_address(resolved_ip).is_loopback:
            return ''

        return domain
    except (socket.gaierror, ValueError):
        return ''


def get_public_ip() -> str:
    try:
        return subprocess.check_output(
            ["curl", "-s", "https://ifconfig.me"]
        ).decode().strip() or ''
    except (subprocess.CalledProcessError, OSError):
        return ''


def get_host() -> str:
    domain = get_public_domain()
    if domain:
        return domain
    public_ip = get_public_ip()
    if public_ip:
        return public_ip
    return ''
        