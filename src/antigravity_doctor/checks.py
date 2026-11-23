"""Core diagnostic checks for Antigravity IDE/CLI workspaces, caches, and skills."""

from __future__ import annotations

import os
import platform
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path

INVISIBLE_UNICODE_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")
HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
SUSPICIOUS_SKILL_RE = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions|"
    r"curl\s+[^\n|]+\|\s*(sh|bash)|"
    r"powershell(\.exe)?\s+-(e|enc|encodedcommand)\b|"
    r"\b(ghp|gho|sk-proj|sk-ant)[-_][A-Za-z0-9]{16,})",
    re.IGNORECASE,
)


@dataclass
class CheckResult:
    name: str
    status: str  # "pass" | "warn" | "fail"
    summary: str
    details: list[str] = field(default_factory=list)
    recommendation: str = ""


def default_antigravity_root() -> Path:
    return Path.home() / ".gemini" / "antigravity"


def dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _, files in os.walk(path):
        for fname in files:
            fpath = Path(root) / fname
            try:
                total += fpath.stat().st_size
            except OSError:
                pass
    return total


def format_bytes(num: int) -> str:
    value = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def check_storage_bloat(ag_root: Path | None = None, warn_mb: int = 500) -> CheckResult:
    """Inspects Antigravity brain artifacts & cache disk usage."""
    root = ag_root or default_antigravity_root()
    if not root.exists():
        return CheckResult(
            name="Storage & Brain Cache",
            status="warn",
            summary=f"Antigravity directory not found at {root}",
            recommendation="Verify Antigravity IDE/CLI has been initialized at least once.",
        )

    brain_dir = root / "brain"
    total_bytes = dir_size_bytes(root)
    brain_bytes = dir_size_bytes(brain_dir)
    details = [
        f"Total Antigravity data dir: {format_bytes(total_bytes)}",
        f"Brain conversation artifacts: {format_bytes(brain_bytes)}",
    ]

    if brain_dir.exists():
        sessions = []
        for entry in brain_dir.iterdir():
            if entry.is_dir():
                sessions.append((dir_size_bytes(entry), entry.name))
        sessions.sort(reverse=True)
        for sz, sid in sessions[:5]:
            details.append(f"Top session {sid[:12]}...: {format_bytes(sz)}")

    warn_bytes = warn_mb * 1024 * 1024
    if total_bytes >= warn_bytes:
        return CheckResult(
            name="Storage & Brain Cache",
            status="warn",
            summary=f"Cache footprint is large ({format_bytes(total_bytes)} >= {warn_mb} MB).",
            details=details,
            recommendation="Archive or prune old conversation logs in brain/ to keep indexing snappy.",
        )

    return CheckResult(
        name="Storage & Brain Cache",
        status="pass",
        summary=f"Healthy footprint ({format_bytes(total_bytes)}).",
        details=details,
    )


def check_skills_security(scan_roots: list[Path] | None = None) -> CheckResult:
    """Audits installed SKILL.md and agent rule files for concealed prompt injection or hardcoded tokens."""
    roots = scan_roots or [
        Path.home() / ".gemini" / "config" / "skills",
        Path.home() / ".gemini" / "antigravity" / "skills",
    ]
    scanned = 0
    flagged: list[str] = []

    for r in roots:
        if not r.exists():
            continue
        for path in r.rglob("*.md"):
            scanned += 1
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            reasons = []
            if INVISIBLE_UNICODE_RE.search(content):
                reasons.append("invisible-unicode")
            if HTML_COMMENT_RE.search(content):
                reasons.append("html-comment")
            if SUSPICIOUS_SKILL_RE.search(content):
                reasons.append("suspicious-directive-or-secret")
            if reasons:
                flagged.append(f"{path.name}: {', '.join(reasons)}")

    if flagged:
        return CheckResult(
            name="Skills & Rules Security Audit",
            status="fail" if any("suspicious-directive" in f for f in flagged) else "warn",
            summary=f"Scanned {scanned} markdown skill files; {len(flagged)} file(s) need review.",
            details=flagged[:15],
            recommendation="Inspect flagged SKILL.md files for indirect prompt injection or leaked tokens.",
        )

    return CheckResult(
        name="Skills & Rules Security Audit",
        status="pass",
        summary=f"Scanned {scanned} skill file(s); no concealed injection markers detected.",
    )


def check_network_endpoints(endpoints: list[tuple[str, int]] | None = None, timeout: float = 2.5) -> CheckResult:
    """Checks TCP reachability to core Antigravity/GitHub endpoints and common local proxy ports."""
    targets = endpoints or [
        ("github.com", 443),
        ("api.github.com", 443),
        ("generativelanguage.googleapis.com", 443),
    ]
    details: list[str] = []
    failed = 0
    for host, port in targets:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                details.append(f"OK   {host}:{port}")
        except OSError as exc:
            failed += 1
            details.append(f"FAIL {host}:{port} ({exc.__class__.__name__})")

    if failed == 0:
        return CheckResult(
            name="Network & API Reachability",
            status="pass",
            summary="All core endpoints reachable via TCP 443.",
            details=details,
        )
    return CheckResult(
        name="Network & API Reachability",
        status="warn" if failed < len(targets) else "fail",
        summary=f"{failed}/{len(targets)} endpoints unreachable.",
        details=details,
        recommendation="Verify system proxy / TUN routing rules for Google & GitHub APIs.",
    )


def check_environment_runtime() -> CheckResult:
    """Checks OS runtime details and platform-specific agent pitfalls."""
    sys_name = platform.system()
    py_ver = platform.python_version()
    details = [f"OS: {sys_name} {platform.release()}", f"Python: {py_ver}"]
    rec = ""
    status = "pass"
    if sys_name == "Windows":
        details.append("Note: Windows UTF-8 mode (-X utf8) recommended for Python hooks to avoid cp936 decode errors.")
        rec = "Ensure lifecycle hooks run Python with `-X utf8` and PowerShell scripts use UTF-8 BOM."
    return CheckResult(
        name="Runtime & Platform Hygiene",
        status=status,
        summary=f"{sys_name} / Python {py_ver}",
        details=details,
        recommendation=rec,
    )
