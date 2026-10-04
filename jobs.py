"""Example jobs. Add a function + entry in REGISTRY to add a job."""
from __future__ import annotations

import datetime
import platform


def ping() -> str:
    return "pong"


def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sysinfo() -> str:
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


REGISTRY = {
    "ping": ("Health check", ping),
    "now": ("Current server time", now),
    "sysinfo": ("OS info", sysinfo),
}
