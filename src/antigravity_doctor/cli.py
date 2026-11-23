"""CLI entry point for antigravity-doctor."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .checks import (
    CheckResult,
    check_environment_runtime,
    check_network_endpoints,
    check_skills_security,
    check_storage_bloat,
    format_bytes,
    prune_orphan_tmps,
)
from .reporter import render_html_report


def run_all_checks(
    skip_network: bool = False,
    warn_mb: int = 500,
    ag_root: Path | None = None,
) -> list[CheckResult]:
    results = [
        check_environment_runtime(),
        check_storage_bloat(ag_root=ag_root, warn_mb=warn_mb),
        check_skills_security(),
    ]
    if not skip_network:
        results.append(check_network_endpoints())
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="antigravity-doctor",
        description="Diagnose Google Antigravity IDE/CLI caches, disk breakdown, orphan .tmp buildup, and skills security.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--root", type=str, default=None, help="Override ~/.gemini/antigravity directory path.")
    parser.add_argument("--skip-network", action="store_true", help="Skip live TCP network checks.")
    parser.add_argument("--warn-mb", type=int, default=500, help="Storage bloat warning threshold in MB.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    parser.add_argument("--html", type=str, help="Write a standalone HTML report to the given path.")
    parser.add_argument(
        "--prune-tmp",
        action="store_true",
        help="Safely prune orphan *.pb.*.tmp / *.pbtxt.*.tmp state files (never touches active state or credentials).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files to prune without deleting anything (used with --prune-tmp).",
    )
    parser.add_argument(
        "--min-age",
        type=int,
        default=0,
        help="Minimum file age in seconds before pruning an orphan .tmp file (default: 0).",
    )
    args = parser.parse_args(argv)
    ag_root = Path(args.root).expanduser() if args.root else None

    if args.prune_tmp:
        prune_res = prune_orphan_tmps(
            ag_root=ag_root,
            dry_run=args.dry_run,
            min_age_seconds=max(0, args.min_age),
        )
        if args.json:
            print(json.dumps(asdict(prune_res), indent=2))
        else:
            mode = "DRY-RUN" if prune_res.dry_run else "PRUNED"
            print(f"[{mode}] Antigravity orphan .tmp cleanup ({prune_res.root})")
            if prune_res.dry_run:
                print(
                    f"  Matched {prune_res.matched_count} orphan file(s); "
                    f"reclaimable space: {format_bytes(prune_res.reclaimed_bytes)}"
                )
            else:
                print(
                    f"  Removed {prune_res.removed_count}/{prune_res.matched_count} orphan file(s); "
                    f"freed space: {format_bytes(prune_res.reclaimed_bytes)}"
                )
                if prune_res.skipped_count:
                    print(f"  Skipped {prune_res.skipped_count} locked/busy file(s)")
            for sample in prune_res.matched_files[:10]:
                print(f"  - {sample}")
            if prune_res.matched_count > 10:
                print(f"  ... and {prune_res.matched_count - 10} more")
        return 0

    results = run_all_checks(skip_network=args.skip_network, warn_mb=args.warn_mb, ag_root=ag_root)

    if args.html:
        out_path = Path(args.html)
        out_path.write_text(render_html_report(results), encoding="utf-8")
        print(f"HTML report written to: {out_path}")

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        for r in results:
            tag = {"pass": "[PASS]", "warn": "[WARN]", "fail": "[FAIL]"}.get(r.status, "[INFO]")
            print(f"{tag} {r.name}: {r.summary}")
            for d in r.details:
                print(f"       - {d}")
            if r.recommendation:
                print(f"       -> Tip: {r.recommendation}")

    return 1 if any(r.status == "fail" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
