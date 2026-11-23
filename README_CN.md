# antigravity-doctor（中文说明）

[English](README.md) | **简体中文**

[![CI](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

面向 **Google Antigravity IDE / CLI (`agy`)** 用户的零依赖本地诊断体检工具、磁盘膨胀拆解器、安全孤儿 `.tmp` 清理器与单文件 HTML 可视化报告生成器。

## `v0.2.0` 重磅更新

- **顶级子目录磁盘膨胀拆解（Top-8 Disk Breakdown）**：精准拆解 `~/.gemini/antigravity` 下占用最大的 Top 8 子目录（如 `scratch/`、`browser_recordings/`、`cache/`、`brain/`、`conversations/` 等）的体积与占比百分比，并在单文件 HTML 体检报告中以直观的横向进度条图呈现，一眼看清究竟是谁吃掉了几十 GB 硬盘。
- **安全清理孤儿 `.tmp` 状态垃圾（`--prune-tmp` & `--dry-run`）**：一键预览或安全清理原子写入失败残留的 `*.pb.*.tmp` / `*.pbtxt.*.tmp` 孤儿临时文件（Windows/Mac 重度用户常堆积数百个），严格保护正式状态文件、数据库与登录凭证。

## 解决哪些真实痛点？

| 体检项 | 实际解决的问题 |
| :--- | :--- |
| **磁盘膨胀拆解与 Brain 缓存** | 精准统计 `~/.gemini/antigravity` 总占用、Top 8 子目录占比与 Top 会话体积，并揪出堆积的 `*.pb.*.tmp` / `*.pbtxt.*.tmp` 孤儿状态垃圾 |
| **安全清理孤儿 `.tmp` 文件** | 支持 `--prune-tmp --dry-run` 无损预览和 `--prune-tmp` 一键释放空间，可选 `--min-age` 冷却保护，绝不触碰正式状态文件与凭证 |
| **Skills & 规则安全审计** | 扫描本地所有 `SKILL.md` / Agent 规则文件，拦截隐藏 HTML 注释、零宽 Unicode、间接 Prompt Injection 投毒与明文 Token 泄漏 |
| **网络与 API 连通性探测** | 一键排查 `github.com`、`api.github.com`、`generativelanguage.googleapis.com` 的代理/TUN 连通问题 |
| **跨平台运行环境避坑** | 自动检查 Windows Python UTF-8 (`-X utf8`) 与 PowerShell 编码陷阱 |

## 快速开始

```bash
pip install -e .

# 终端一键全面体检（含 Top 8 子目录磁盘占比拆解）
antigravity-doctor

# 生成高颜值单文件 HTML 可视化体检报告（内置磁盘占用条形图）
antigravity-doctor --html doctor_report.html

# 先无损预览将被清理的孤儿 .tmp 文件数量与可释放空间
antigravity-doctor --prune-tmp --dry-run

# 正式安全清理孤儿 .tmp 文件（可加 --min-age 60 跳过 60 秒内新写入文件）
antigravity-doctor --prune-tmp --min-age 60

# 输出 JSON 供脚本或 CI 调用
antigravity-doctor --json --skip-network
```

## `--prune-tmp` 安全承诺

`--prune-tmp` 仅匹配 `~/.gemini/antigravity` 根目录下的 `*.pb.<id>.tmp` 和 `*.pbtxt.<id>.tmp` 常规文件（跳过符号链接与所有子目录），**绝不触碰**正在使用的 `.pb` / `.pbtxt` 正式状态文件、SQLite `.db`、`mcp_config.json`、`installation_id`、`scratch/` 里的用户代码及任何凭证；若个别文件正被运行中的 Antigravity 占用锁定，会自动跳过并汇报。

## 开源协议

MIT
