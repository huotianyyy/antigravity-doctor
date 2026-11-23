"""antigravity-doctor: Diagnostics & security auditor for Google Antigravity IDE/CLI."""

from .checks import (
    CheckResult,
    DirUsage,
    PruneResult,
    analyze_disk_breakdown,
    check_environment_runtime,
    check_network_endpoints,
    check_skills_security,
    check_storage_bloat,
    find_orphan_tmp_files,
    is_orphan_tmp_file,
    prune_orphan_tmps,
)
from .reporter import render_html_report

__all__ = [
    "CheckResult",
    "DirUsage",
    "PruneResult",
    "analyze_disk_breakdown",
    "check_environment_runtime",
    "check_network_endpoints",
    "check_skills_security",
    "check_storage_bloat",
    "find_orphan_tmp_files",
    "is_orphan_tmp_file",
    "prune_orphan_tmps",
    "render_html_report",
]

__version__ = "0.2.0"
