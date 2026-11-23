"""Core diagnostic checks and safe maintenance helpers for Antigravity IDE/CLI."""

from __future__ import annotations

import os
import platform
import re
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

INVISIBLE_UNICODE_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")
HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
SUSPICIOUS_SKILL_RE = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions|"
    r"curl\s+[^\n|]+\|\s*(sh|bash)|"
    r"powershell(\.exe)?\s+-(e|enc|encodedcommand)\b|"
    r"\b(ghp|gho|sk-proj|sk-ant)[-_][A-Za-z0-9]{16,})",
    re.IGNORECASE,
)
# Only matches orphan atomic-write temp files left behind by protobuf state saves,
# e.g. `antigravity_state.pbtxt.<uuid>.tmp` or `agyhub_summaries_proto.pb.<uuid>.tmp`.
ORPHAN_TMP_RE = re.compile(r"^.+\.(?:pb|pbtxt)\.[^./\\]+\.tmp$", re.IGNORECASE)


@dataclass
class DirUsage:
    name: str
    size_bytes: int
    share_pct: float


@dataclass
class PruneResult:
    root: str
    dry_run: bool
    matched_count: int
    removed_count: int
    skipped_count: int
    reclaimed_bytes: int
    matched_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    name: str
    status: str  # "pass" | "warn" | "fail"
    summary: str
    details: list[str] = field(default_factory=list)
    recommendation: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


def default_antigravity_root() -> Path:
    return Path.home() / ".gemini" / "antigravity"


def dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _, files in os.walk(path, followlinks=False):
        for fname in files:
            fpath = Path(root) / fname
            try:
                if not fpath.is_symlink():
                    total += fpath.stat().st_size
            except OSError:
                pass
    return total


def format_bytes(num: int) -> str:
    value = float(max(0, num))
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def is_orphan_tmp_file(path: Path) -> bool:
    """Returns True only for orphan `*.pb.*.tmp` / `*.pbtxt.*.tmp` state temp files."""
    try:
        if path.is_symlink() or not path.is_file():
            return False
    except OSError:
        return False
    return bool(ORPHAN_TMP_RE.match(path.name))


def find_orphan_tmp_files(
    ag_root: Path | None = None,
    min_age_seconds: int = 0,
) -> list[Path]:
    """Finds orphan state `.tmp` files directly under the Antigravity root directory."""
    root = ag_root or default_antigravity_root()
    if not root.exists() or not root.is_dir():
        return []

    now = time.time()
    matched: list[Path] = []
    try:
        entries = list(root.iterdir())
    except OSError:
        return []

    for entry in entries:
        if not is_orphan_tmp_file(entry):
            continue
        if min_age_seconds > 0:
            try:
                age = now - entry.stat().st_mtime
            except OSError:
                continue
            if age < min_age_seconds:
                continue
        matched.append(entry)

    matched.sort(key=lambda p: p.name)
    return matched


def prune_orphan_tmps(
    ag_root: Path | None = None,
    dry_run: bool = True,
    min_age_seconds: int = 0,
) -> PruneResult:
    """Safely previews or deletes orphan `*.pb.*.tmp` / `*.pbtxt.*.tmp` files.

    Never touches formal `.pb`, `.pbtxt`, `.db`, configuration, or credential files.
    """
    root = ag_root or default_antigravity_root()
    matched = find_orphan_tmp_files(root, min_age_seconds=min_age_seconds)
    matched_names = [p.name for p in matched]

    if dry_run:
        reclaimable = 0
        for path in matched:
            try:
                reclaimable += path.stat().st_size
            except OSError:
                pass
        return PruneResult(
            root=str(root),
            dry_run=True,
            matched_count=len(matched),
            removed_count=0,
            skipped_count=0,
            reclaimed_bytes=reclaimable,
            matched_files=matched_names,
        )

    removed = 0
    reclaimed = 0
    skipped_names: list[str] = []
    for path in matched:
        try:
            size = path.stat().st_size
            path.unlink()
            removed += 1
            reclaimed += size
        except OSError:
            skipped_names.append(path.name)

    return PruneResult(
        root=str(root),
        dry_run=False,
        matched_count=len(matched),
        removed_count=removed,
        skipped_count=len(skipped_names),
        reclaimed_bytes=reclaimed,
        matched_files=matched_names,
        skipped_files=skipped_names,
    )


def analyze_disk_breakdown(
    ag_root: Path | None = None,
    top_n: int = 8,
) -> tuple[int, list[DirUsage]]:
    """Computes total footprint and Top-N largest direct subdirectories with percentage share."""
    root = ag_root or default_antigravity_root()
    if not root.exists() or not root.is_dir():
        return 0, []

    dir_sizes: list[tuple[int, str]] = []
    root_files_bytes = 0
    try:
        entries = list(root.iterdir())
    except OSError:
        return 0, []

    for entry in entries:
        try:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                dir_sizes.append((dir_size_bytes(entry), entry.name))
            elif entry.is_file():
                root_files_bytes += entry.stat().st_size
        except OSError:
            continue

    total_bytes = root_files_bytes + sum(sz for sz, _ in dir_sizes)
    dir_sizes.sort(key=lambda item: (-item[0], item[1]))

    breakdown: list[DirUsage] = []
    for sz, name in dir_sizes[: max(1, top_n)]:
        pct = round((sz / total_bytes) * 100.0, 1) if total_bytes > 0 else 0.0
        breakdown.append(DirUsage(name=name, size_bytes=sz, share_pct=pct))

    return total_bytes, breakdown


def check_storage_bloat(
    ag_root: Path | None = None,
    warn_mb: int = 500,
    top_n: int = 8,
) -> CheckResult:
    """Inspects Antigravity top-level disk breakdown, brain artifacts, and orphan `.tmp` buildup."""
    root = ag_root or default_antigravity_root()
    if not root.exists():
        return CheckResult(
            name="Storage & Brain Cache",
            status="warn",
            summary=f"Antigravity directory not found at {root}",
            recommendation="Verify Antigravity IDE/CLI has been initialized at least once.",
        )

    total_bytes, breakdown = analyze_disk_breakdown(root, top_n=top_n)
    brain_dir = root / "brain"
    brain_bytes = next((d.size_bytes for d in breakdown if d.name == "brain"), dir_size_bytes(brain_dir))

    orphan_tmps = find_orphan_tmp_files(root)
    orphan_tmp_bytes = 0
    for p in orphan_tmps:
        try:
            orphan_tmp_bytes += p.stat().st_size
        except OSError:
            pass

    details = [
        f"Total Antigravity data dir: {format_bytes(total_bytes)}",
        f"Brain conversation artifacts: {format_bytes(brain_bytes)}",
        f"Orphan state .tmp files: {len(orphan_tmps)} ({format_bytes(orphan_tmp_bytes)})",
    ]

    if breakdown:
        for item in breakdown:
            details.append(f"Disk breakdown: {item.name}/ — {format_bytes(item.size_bytes)} ({item.share_pct:.1f}%)")

    if brain_dir.exists():
        sessions: list[tuple[int, str]] = []
        for entry in brain_dir.iterdir():
            if entry.is_dir() and not entry.is_symlink():
                sessions.append((dir_size_bytes(entry), entry.name))
        sessions.sort(reverse=True)
        for sz, sid in sessions[:5]:
            details.append(f"Top session {sid[:12]}...: {format_bytes(sz)}")

    metrics: dict[str, Any] = {
        "total_bytes": total_bytes,
        "brain_bytes": brain_bytes,
        "orphan_tmp_count": len(orphan_tmps),
        "orphan_tmp_bytes": orphan_tmp_bytes,
        "disk_breakdown": [
            {
                "name": item.name,
                "size_bytes": item.size_bytes,
                "formatted": format_bytes(item.size_bytes),
                "share_pct": item.share_pct,
            }
            for item in breakdown
        ],
    }

    warn_bytes = warn_mb * 1024 * 1024
    if total_bytes >= warn_bytes or len(orphan_tmps) >= 20:
        reasons = []
        if total_bytes >= warn_bytes:
            reasons.append(f"cache footprint {format_bytes(total_bytes)} >= {warn_mb} MB")
        if len(orphan_tmps) >= 20:
            reasons.append(f"{len(orphan_tmps)} orphan .tmp state files accumulated")
        rec_parts = []
        if orphan_tmps:
            rec_parts.append("Run `antigravity-doctor --prune-tmp --dry-run` to preview safe orphan .tmp cleanup")
        if total_bytes >= warn_bytes:
            rec_parts.append("archive old brain/ sessions or prune heavy scratch/browser_recordings folders")
        return CheckResult(
            name="Storage & Brain Cache",
            status="warn",
            summary=f"Cleanup recommended: {'; '.join(reasons)}.",
            details=details,
            recommendation="; ".join(rec_parts) + ".",
            metrics=metrics,
        )

    return CheckResult(
        name="Storage & Brain Cache",
        status="pass",
        summary=f"Healthy footprint ({format_bytes(total_bytes)}).",
        details=details,
        metrics=metrics,
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
