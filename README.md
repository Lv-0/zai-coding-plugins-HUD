# ZAI Coding Plugins HUD

基于 `leeguooooo/claude-code-usage-bar` 重构，面向 **ZAI / 智谱 (ZHIPU)** 平台使用量的 Claude Code 状态栏监控工具。

实时显示 token 配额、MCP 工具用量、重置倒计时、当前模型与上下文窗口占用——一行状态栏，全局掌控。

---

## 状态栏一览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [███░░░░░░░] 5h 30% │ [█░░░░░░░░░] 7d 2% │ ⏰0h43m │ zai-max@ZHIPU 🔧2/4.0k(1%) │ GLM-5.1(18.2k/128k) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

各段含义：

```
[███░░░░░░░] 5h 30%          短期 token 配额使用率（3 天滚动窗口）+ 进度条
[█░░░░░░░░░] 7d 2%           长期 token 配额使用率（6 天滚动窗口）+ 进度条
⏰0h43m                      距离短期配额重置的倒计时（来自 API 真实数据）
zai-max@ZHIPU                当前套餐 @ 平台
🔧2/4.0k(1%)                 MCP 工具用量：已用 2 / 总额 4000（1%）
GLM-5.1(18.2k/128k)          当前模型 + 上下文窗口占用（来自 stdin）
```

### 颜色规则

```
[█████░░░░░]  绿色 (< 30%)    用量安全
[███████░░░]  黄色 (30-70%)   用量中等
[██████████]  红色 (> 70%)    用量紧张
```

---

## 典型输出示例

### 智谱平台 (ZHIPU)

用量较低时：
```
[█░░░░░░░░░] 5h 5% | [█░░░░░░░░░] 7d 1% | ⏰2h30m | zai-max@ZHIPU 🔧2/4.0k(1%) | GLM-5.1(3.2k/128k)
```

用量中等时：
```
[█████░░░░░] 5h 48% | [███░░░░░░░] 7d 22% | ⏰1h12m | zai-pro@ZHIPU 🔧156/2.0k(8%) | GLM-5.1(89k/128k)
```

用量紧张时：
```
[█████████░] 5h 87% | [██████░░░░] 7d 65% | ⏰0h08m | zai-lite@ZHIPU 🔧98/1.0k(10%) | GLM-5.1(120k/128k)
```

### ZAI 平台

```
[██░░░░░░░░] 5h 18% | [█░░░░░░░░░] 7d 3% | ⏰3h45m | zai-pro@ZAI 🔧45/3.0k(2%) | Claude Sonnet 4(52k/200k)
```

### Anthropic 官方数据 (Pro / Max 用户)

```
[██████░░░░] 5h 63% | [█░░░░░░░░░] 7d 5% | ⏰2h14m | max5 🔥x2[03:00~21:00] | Opus 4.6(13.4k/1.0M)
```

### JSON 输出模式

```bash
$ cs --json-output
```

```json
{
  "success": true,
  "source": "zai-plugin",
  "platform": "ZHIPU",
  "rate_limits": {
    "short_term": { "used_percentage": 9 },
    "long_term":  { "used_percentage": 1 },
    "mcp": {
      "used_percentage": 1,
      "current_usage": 2,
      "total": 4000
    }
  },
  "model_usage": { "...": "按小时聚合的模型调用量" },
  "tool_usage":  { "...": "按小时聚合的工具调用量" },
  "meta": {
    "model": "unknown",
    "display_name": "Unknown",
    "reset_time": "0h43m",
    "bypass": false,
    "plan": "zai-max"
  }
}
```

---

## 数据来源与优先级

```
                    ┌─────────────────────┐
                    │   cs 命令被调用      │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │ 读取 Claude Code     │
                    │ stdin 注入数据        │
                    │ (model, context_win) │
                    └─────────┬───────────┘
                              │
                ┌─────────────▼──────────────┐
                │ ANTHROPIC_BASE_URL 指向     │
                │ z.ai / bigmodel.cn ?       │
                └─────┬──────────────┬────────┘
                   是 │              │ 否
            ┌─────────▼───┐    ┌────▼──────────────┐
            │ 查询平台 API │    │ stdin 含 rate_limit │
            │ (30s 缓存)   │    │ (官方 Anthropic)    │
            └─────┬───────┘    └────┬──────────────┘
                  │                 │
            ┌─────▼──────┐    ┌────▼──────────────┐
            │ short_term  │    │ 5h / 7d 官方配额   │
            │ long_term   │    └────┬──────────────┘
            │ MCP 用量    │         │
            │ nextReset   │         │
            └─────┬──────┘         │
                  └───────┬────────┘
                          │
                ┌─────────▼───────────┐
                │   组装状态栏输出     │
                │   [进度条] + 标签    │
                └─────────────────────┘
```

优先级：**ZAI/ZHIPU 平台 API > Anthropic 官方 stdin > 本地文件分析**

当 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` 可用，且指向以下地址时，自动启用平台查询：

| 平台 | 地址 |
|------|------|
| ZAI | `https://api.z.ai` |
| 智谱 | `https://open.bigmodel.cn` |
| 智谱 (开发) | `https://dev.bigmodel.cn` |

平台 API 返回 3 类配额数据：

| 类型 | 说明 | 状态栏映射 |
|------|------|-----------|
| `TOKENS_LIMIT` (短期) | 3 天滚动窗口 token 限额 | `5h` 进度条 |
| `TOKENS_LIMIT` (长期) | 6 天滚动窗口 token 限额 | `7d` 进度条 |
| `TIME_LIMIT` | MCP 工具月度限额 | `🔧` 标签 |

---

## 安装

### 本地编译安装

```bash
git clone <repo-url>
cd claude-code-usage-bar-2.2.4
python3 -m build
uv tool install dist/claude_statusbar-2.3.0-py3-none-any.whl
```

或开发模式：

```bash
python3 -m pip install -e .
```

### 通过 pip / uv / pipx

```bash
pip install claude-statusbar
uv tool install claude-statusbar
pipx install claude-statusbar
```

安装后可用 3 个等价命令：`claude-statusbar`、`cstatus`、`cs`

---

## 配置 Claude Code

编辑 `~/.claude/settings.json`：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-token-here",
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic"
  },
  "statusLine": {
    "type": "command",
    "command": "cs"
  }
}
```

重启 Claude Code 即可在状态栏看到使用量数据。

---

## 命令用法

```bash
cs                          # 显示状态栏（最短命令）
cs --json-output            # 输出 JSON（便于脚本集成）
cs --plan zai-max           # 手动设置套餐
cs --reset-hour 14          # 指定重置小时
cs --no-color               # 关闭颜色
cs --no-auto-update         # 关闭自动更新检查
cs --version                # 查看版本
cs --help                   # 查看帮助
```

### 设置套餐

设置一次后自动保存：

```bash
cs --plan zai-lite    # Lite 套餐
cs --plan zai-pro     # Pro 套餐
cs --plan zai-max     # Max 套餐
```

也支持 Anthropic 原生套餐：`pro`、`max5`、`max20`

### 环境变量

| 变量 | 作用 |
|------|------|
| `ANTHROPIC_BASE_URL` | 平台 API 基地址（自动检测 ZAI / ZHIPU） |
| `ANTHROPIC_AUTH_TOKEN` | 平台认证令牌 |
| `CLAUDE_PLAN` | 默认套餐类型 |
| `CLAUDE_RESET_HOUR` | 默认重置小时 (0-23) |
| `CLAUDE_STATUSBAR_JSON=1` | 默认输出 JSON |
| `CLAUDE_STATUSBAR_NO_UPDATE=1` | 禁用自动更新 |
| `NO_COLOR=1` | 禁用彩色输出 |

---

## 刷新频率

```
Claude Code 每轮对话 ──触发──▶ cs 命令
                                  │
                    ┌─────────────▼─────────────┐
                    │  last_zai_query.json       │
                    │  缓存 < 30s ?              │
                    └─────┬──────────────┬────────┘
                       是 │              │ 否
                   读缓存  │         调用平台 API
                   (<1ms)  │         (~1.2s)
                          └──────┬──────┘
                                 │
                          写入缓存文件
                          (30s TTL)
```

| 场景 | 频率 |
|------|------|
| Claude Code 调用 statusLine | 每轮对话触发 |
| 平台 API 实际请求 | **每 30 秒最多 1 次** |
| 自动更新检查 | 每天 1 次 |

平台监控类 API 不消耗 token，不会增加您的用量。

---

## 其他集成场景

### tmux 状态栏

```bash
set -g status-right '#(cs --no-color)'
set -g status-interval 30
```

### zsh / bash prompt

```bash
# zsh
RPROMPT='$(cs --no-color)'

# bash
PROMPT_COMMAND='cs --no-color'
```

### i3 / sway

```
bar {
    status_command cs --no-color
}
```

---

## 项目结构

```
src/claude_statusbar/
├── __init__.py       # 包入口，版本号
├── cli.py            # CLI 入口 (cs / cstatus / claude-statusbar)
├── core.py           # 核心逻辑：数据获取、配额解析、输出组装
├── progress.py       # 进度条渲染 + ANSI 着色（纯函数）
├── cache.py          # 缓存层：原子写入、30s 过期、stale-read
├── cache_refresh.py  # 后台缓存刷新子进程
├── updater.py        # 自动更新器（每日检查 PyPI）
└── zai_query.py      # ZAI / 智谱平台 API 查询
```

---

## 已知情况

- 仓库中的旧安装脚本和宣传图片不再代表当前版本能力
- 项目名和可执行命令仍沿用原始包名 `claude-statusbar`
- 保留了兼容原 Anthropic 官方数据的回退逻辑

## License

MIT
