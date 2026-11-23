"""antigravity-doctor: Diagnostics & security auditor for Google Antigravity IDE/CLI."""

from .checks import (
    CheckResult,
    check_environment_runtime,
    check_network_endpoints,
    check_skills_security,
    check_storage_bloat,
)
from .reporter import render_html_report

__all__ = [
    "CheckResult",
    "check_environment_runtime",
    "check_network_endpoints",
    "check_skills_security",
    "check_storage_bloat",
    "render_html_report",
]

__version__ = "0.1.0"
