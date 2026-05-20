---
name: fusion360-mcp
description: Fusion 360 MCP 安装配置引导 - 84 工具 CC 亲测
---

# Fusion 360 MCP 安装引导

工具用法由 MCP server 自动提供，本 skill 仅为安装引导。

## 1. Add-in 安装（家里执行一次）

    git clone https://github.com/faust-machines/fusion360-mcp-server.git
    cd fusion360-mcp-server
    Copy-Item -Recurse addon "C:\Users\heiweilu.li\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\Fusion360MCP"

Fusion 360: Shift+S -> Add-Ins -> Fusion360MCP -> Run
成功: TEXT COMMANDS 显示 [MCP] Server listening on localhost:9876

## 2. MCP Server（settings.json 已配好）

command: uvx, args: [fusion360-mcp-server, --mode, socket]
要求 uv: pip install uv

## 3. 验证

ping tool 返回 pong:true = 就绪

## 排查

| 症状 | 解决方案 |
|------|---------|
| 工具不出现 | 启动 Fusion360MCP Add-in |
| connection refused | 检查 Add-in 是否运行 |
| uvx not found | pip install uv |
| 超时 30s | 拆分操作 |

## 注意

单位: 厘米, 每次只能一个操作
Mock: uvx fusion360-mcp-server --mode mock
GitHub: https://github.com/faust-machines/fusion360-mcp-server
