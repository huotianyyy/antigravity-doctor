# antigravity-doctor（中文说明）

[English](README.md) | **简体中文**

[![CI](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/huotianyyy/antigravity-doctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

面向 **Google Antigravity IDE / CLI (`agy`)** 用户的零依赖本地诊断体检工具与单文件 HTML 报告生成器。

## 解决哪些真实痛点？

| 体检项 | 实际解决的问题 |
| :--- | :--- |
| **磁盘与 Brain 缓存膨胀** | 扫描 `~/.gemini/antigravity` 总占用、Top 体积会话，并揪出 Windows/Mac 下堆积的数百个孤儿 `*.tmp` 状态垃圾文件 |
| **Skills & 规则安全审计** | 扫描本地所有 `SKILL.md` / Agent 规则文件，拦截隐藏 HTML 注释、零宽 Unicode、间接 Prompt Injection 投毒与明文 Token 泄漏 |
| **网络与 API 连通性探测** | 一键排查 `github.com`、`api.github.com`、`generativelanguage.googleapis.com` 的代理/TUN 连通问题 |
| **跨平台运行环境避坑** | 自动检查 Windows Python UTF-8 (`-X utf8`) 与 PowerShell 编码陷阱 |

## 快速开始

```bash
pip install -e .

# 终端一键全面体检
antigravity-doctor

# 生成高颜值单文件 HTML 可视化体检报告
antigravity-doctor --html doctor_report.html

# 输出 JSON 供脚本或 CI 调用
antigravity-doctor --json --skip-network
```

## 开源协议

MIT
