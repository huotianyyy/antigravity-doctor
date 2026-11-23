"""CLI entry point for antigravity-doctor."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .checks import (
    CheckResult,
    check_environment_runtime,
    check_network_endpoints,
    check_skills_security,
    check_storage_bloat,
)
from .reporter import render_html_report


def run_all_checks(skip_network: bool = False, warn_mb: int = 500) -> list[CheckResult]:
    results = [
        check_environment_runtime(),
        check_storage_bloat(warn_mb=warn_mb),
        check_skills_security(),
    ]
    if not skip_network:
        results.append(check_network_endpoints())
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="antigravity-doctor",
        description="Diagnose Google Antigravity IDE/CLI caches, skills security, and network reachability.",
    )
    parser.add_argument("--skip-network", action="store_true", help="Skip live TCP network checks.")
    parser.add_argument("--warn-mb", type=int, default=500, help="Storage bloat warning threshold in MB.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON diagnostics.")
    parser.add_argument("--html", type=str, help="Write a standalone HTML report to the given path.")
    args = parser.parse_args(argv)

    results = run_all_checks(skip_network=args.skip_network, warn_mb=args.warn_mb)

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
