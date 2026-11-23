# antigravity-doctor

**English** | [简体中文](README_CN.md)

[![CI](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Zero-dependency local diagnostic CLI & HTML report generator for **Google Antigravity IDE / CLI (`agy`)** users.

## What It Diagnoses

| Check | What It Catches |
| :--- | :--- |
| **Storage & Brain Cache** | Bloated `~/.gemini/antigravity/brain` sessions & logs slowing down indexing |
| **Skills & Rules Security** | Concealed HTML comments, invisible Unicode, indirect prompt injection, or hardcoded tokens inside `SKILL.md` files |
| **Network & API Reachability** | Broken proxy/TUN paths to `github.com`, `api.github.com`, and `generativelanguage.googleapis.com` |
| **Platform Runtime Hygiene** | Cross-platform encoding and hook pitfalls (e.g., Windows UTF-8 `-X utf8` / PowerShell BOM checks) |

## Quickstart

```bash
pip install -e .

# Run full diagnostics in terminal
antigravity-doctor

# Generate a visual standalone HTML diagnostic report
antigravity-doctor --html doctor_report.html

# Machine-readable JSON output for CI or scripts
antigravity-doctor --json --skip-network
```

## License

MIT
