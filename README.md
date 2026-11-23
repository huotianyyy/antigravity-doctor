# antigravity-doctor

**English** | [简体中文](README_CN.md)

[![CI](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Zero-dependency local diagnostic CLI, disk-bloat analyzer, safe orphan `.tmp` pruner, and standalone HTML report generator for **Google Antigravity IDE / CLI (`agy`)** users.

## What's New in `v0.2.0`

- **Top-8 Subdirectory Disk Breakdown**: Breaks down `~/.gemini/antigravity` by its 8 largest subdirectories (`scratch/`, `browser_recordings/`, `cache/`, `brain/`, `conversations/`, etc.) with exact byte sizes and percentage shares — rendered both in terminal output and as a visual bar chart in the standalone HTML report.
- **Safe Orphan `.tmp` Pruner (`--prune-tmp` & `--dry-run`)**: Safely previews and cleans accumulated `*.pb.*.tmp` and `*.pbtxt.*.tmp` atomic-write leftovers (often hundreds of files on Windows/macOS), while strictly leaving active `.pb`, `.pbtxt`, `.db`, configs, and credentials untouched.

## What It Diagnoses

| Check | What It Catches |
| :--- | :--- |
| **Disk Breakdown & Brain Cache** | Top-8 heaviest subdirectories under `~/.gemini/antigravity` with share %, heaviest `brain/` sessions, and accumulated orphan `*.pb.*.tmp` / `*.pbtxt.*.tmp` state files |
| **Safe Orphan `.tmp` Cleanup** | Preview (`--prune-tmp --dry-run`) or remove (`--prune-tmp`) orphan protobuf temp files with optional `--min-age` guard and zero risk to active state files |
| **Skills & Rules Security** | Concealed HTML comments, invisible Unicode, indirect prompt injection, or hardcoded tokens inside `SKILL.md` files |
| **Network & API Reachability** | Broken proxy/TUN paths to `github.com`, `api.github.com`, and `generativelanguage.googleapis.com` |
| **Platform Runtime Hygiene** | Cross-platform encoding and hook pitfalls (e.g., Windows UTF-8 `-X utf8` / PowerShell BOM checks) |

## Quickstart

```bash
pip install -e .

# Run full diagnostics with Top-8 disk breakdown in terminal
antigravity-doctor

# Generate a visual standalone HTML diagnostic report (with disk breakdown bar chart)
antigravity-doctor --html doctor_report.html

# Preview orphan *.pb.*.tmp / *.pbtxt.*.tmp cleanup without deleting anything
antigravity-doctor --prune-tmp --dry-run

# Execute safe orphan .tmp cleanup (optional --min-age 60 skips files modified <60s ago)
antigravity-doctor --prune-tmp --min-age 60

# Machine-readable JSON output for CI or scripts
antigravity-doctor --json --skip-network
```

## Safety Guarantee for `--prune-tmp`

`--prune-tmp` strictly targets **direct files** under `~/.gemini/antigravity` matching `*.pb.<id>.tmp` or `*.pbtxt.<id>.tmp` (and ignores symlinks and subdirectories). Active `.pb`, `.pbtxt`, SQLite `.db` files, `mcp_config.json`, `installation_id`, user code in `scratch/`, and any credentials are never modified. Files locked by a running Antigravity instance are safely skipped.

## License

MIT
