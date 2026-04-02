# ZAI Coding Plugins HUD

Forked and refactored from `leeguooooo/claude-code-usage-bar`, a Claude Code status bar monitor built for **ZAI / ZHIPU** platform usage tracking.

Displays real-time token quotas, MCP tool usage, reset countdowns, current model, and context window occupancy — one status line, full visibility.

---

## Status Bar at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [███░░░░░░░] 5h 30% │ [█░░░░░░░░░] 7d 2% │ ⏰0h43m │ zai-max@ZHIPU 🔧2/4.0k(1%) │ GLM-5.1(18.2k/128k) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Segment breakdown:

```
[███░░░░░░░] 5h 30%          Short-term token quota usage (3-day rolling window) + progress bar
[█░░░░░░░░░] 7d 2%           Long-term token quota usage (6-day rolling window) + progress bar
⏰0h43m                      Countdown to short-term quota reset (from API)
zai-max@ZHIPU                Current plan @ platform
🔧2/4.0k(1%)                 MCP tool usage: 2 used / 4000 total (1%)
GLM-5.1(18.2k/128k)          Current model + context window occupancy (from stdin)
```

### Color Rules

```
[█████░░░░░]  Green (< 30%)    Usage is safe
[███████░░░]  Yellow (30-70%)  Usage is moderate
[██████████]  Red (> 70%)      Usage is high
```

---

## Typical Output Examples

### ZHIPU Platform

Low usage:
```
[█░░░░░░░░░] 5h 5% | [█░░░░░░░░░] 7d 1% | ⏰2h30m | zai-max@ZHIPU 🔧2/4.0k(1%) | GLM-5.1(3.2k/128k)
```

Moderate usage:
```
[█████░░░░░] 5h 48% | [███░░░░░░░] 7d 22% | ⏰1h12m | zai-pro@ZHIPU 🔧156/2.0k(8%) | GLM-5.1(89k/128k)
```

High usage:
```
[█████████░] 5h 87% | [██████░░░░] 7d 65% | ⏰0h08m | zai-lite@ZHIPU 🔧98/1.0k(10%) | GLM-5.1(120k/128k)
```

### ZAI Platform

```
[██░░░░░░░░] 5h 18% | [█░░░░░░░░░] 7d 3% | ⏰3h45m | zai-pro@ZAI 🔧45/3.0k(2%) | Claude Sonnet 4(52k/200k)
```

### Anthropic Official Data (Pro / Max Users)

```
[██████░░░░] 5h 63% | [█░░░░░░░░░] 7d 5% | ⏰2h14m | max5 🔥x2[03:00~21:00] | Opus 4.6(13.4k/1.0M)
```

### JSON Output Mode

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
  "model_usage": { "...": "hourly aggregated model call counts" },
  "tool_usage":  { "...": "hourly aggregated tool call counts" },
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

## Data Sources & Priority

```
                    ┌─────────────────────┐
                    │   cs command called  │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │ Read Claude Code     │
                    │ stdin injected data  │
                    │ (model, context_win) │
                    └─────────┬───────────┘
                              │
                ┌─────────────▼──────────────┐
                │ ANTHROPIC_BASE_URL points   │
                │ to z.ai / bigmodel.cn ?     │
                └─────┬──────────────┬────────┘
                   Yes              No
            ┌─────────▼───┐    ┌────▼──────────────┐
            │ Query platform│   │ stdin has rate_limit│
            │ API (30s cache)│  │ (official Anthropic)│
            └─────┬───────┘    └────┬──────────────┘
                  │                 │
            ┌─────▼──────┐    ┌────▼──────────────┐
            │ short_term  │    │ 5h / 7d official   │
            │ long_term   │    │ quota from API     │
            │ MCP usage   │    └────┬──────────────┘
            │ nextReset   │         │
            └─────┬──────┘         │
                  └───────┬────────┘
                          │
                ┌─────────▼───────────┐
                │  Assemble status bar │
                │  [progress] + labels │
                └─────────────────────┘
```

Priority: **ZAI/ZHIPU Platform API > Anthropic Official stdin > Local File Analysis**

Platform queries are automatically enabled when `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` are available and point to:

| Platform | URL |
|----------|-----|
| ZAI | `https://api.z.ai` |
| ZHIPU | `https://open.bigmodel.cn` |
| ZHIPU (Dev) | `https://dev.bigmodel.cn` |

The platform API returns 3 types of quota data:

| Type | Description | Status Bar Mapping |
|------|-------------|-------------------|
| `TOKENS_LIMIT` (short-term) | 3-day rolling window token limit | `5h` progress bar |
| `TOKENS_LIMIT` (long-term) | 6-day rolling window token limit | `7d` progress bar |
| `TIME_LIMIT` | MCP tool monthly limit | `🔧` label |

---

## Installation

### Build from Source

```bash
git clone <repo-url>
cd claude-code-usage-bar-2.2.4
python3 -m build
uv tool install dist/claude_statusbar-2.3.0-py3-none-any.whl
```

Or in development mode:

```bash
python3 -m pip install -e .
```

### Via pip / uv / pipx

```bash
pip install claude-statusbar
uv tool install claude-statusbar
pipx install claude-statusbar
```

After installation, 3 equivalent commands are available: `claude-statusbar`, `cstatus`, `cs`

---

## Configure Claude Code

Edit `~/.claude/settings.json`:

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

Restart Claude Code to see usage data in the status bar.

---

## CLI Usage

```bash
cs                          # Show status bar (shortest command)
cs --json-output            # Output JSON (for script integration)
cs --plan zai-max           # Set plan manually
cs --reset-hour 14          # Specify reset hour
cs --no-color               # Disable colors
cs --no-auto-update         # Disable auto-update checks
cs --version                # Show version
cs --help                   # Show help
```

### Setting Your Plan

Set once and it's saved automatically:

```bash
cs --plan zai-lite    # Lite plan
cs --plan zai-pro     # Pro plan
cs --plan zai-max     # Max plan
```

Also supports native Anthropic plans: `pro`, `max5`, `max20`

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_BASE_URL` | Platform API base URL (auto-detects ZAI / ZHIPU) |
| `ANTHROPIC_AUTH_TOKEN` | Platform authentication token |
| `CLAUDE_PLAN` | Default plan type |
| `CLAUDE_RESET_HOUR` | Default reset hour (0-23) |
| `CLAUDE_STATUSBAR_JSON=1` | Default to JSON output |
| `CLAUDE_STATUSBAR_NO_UPDATE=1` | Disable auto-updates |
| `NO_COLOR=1` | Disable colored output |

---

## Refresh Rate

```
Claude Code each turn ──triggers──▶ cs command
                                        │
                          ┌─────────────▼─────────────┐
                          │  last_zai_query.json       │
                          │  cache < 30s ?             │
                          └─────┬──────────────┬───────┘
                            Yes              No
                        Read cache       Call platform API
                        (<1ms)           (~1.2s)
                              └──────┬──────┘
                                     │
                              Write to cache file
                              (30s TTL)
```

| Scenario | Frequency |
|----------|-----------|
| Claude Code triggers statusLine | Each conversation turn |
| Actual platform API requests | **At most once per 30 seconds** |
| Auto-update checks | Once per day |

Platform monitoring APIs do not consume tokens and will not increase your usage.

---

## Other Integrations

### tmux Status Bar

```bash
set -g status-right '#(cs --no-color)'
set -g status-interval 30
```

### zsh / bash Prompt

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

## Project Structure

```
src/claude_statusbar/
├── __init__.py       # Package entry, version
├── cli.py            # CLI entry point (cs / cstatus / claude-statusbar)
├── core.py           # Core logic: data fetching, quota parsing, output assembly
├── progress.py       # Progress bar rendering + ANSI coloring (pure functions)
├── cache.py          # Cache layer: atomic writes, 30s TTL, stale-read
├── cache_refresh.py  # Background cache refresh subprocess
├── updater.py        # Auto-updater (daily PyPI check)
└── zai_query.py      # ZAI / ZHIPU platform API queries
```

---

## Notes

- Old installation scripts and promotional images in the repo may not represent current capabilities
- The package name and executable commands still use the original `claude-statusbar`
- Backward-compatible fallback logic for original Anthropic official data is retained

## License

MIT
