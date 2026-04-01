# ZAI Coding Plugins HUD

基于 `leeguooooo/claude-code-usage-bar` 重构，改为面向 ZAI / 智谱平台使用量的命令行状态栏工具。

它会优先读取 ZAI / ZHIPU 接口返回的额度数据，并在 Claude Code `statusLine` 场景下补充当前模型和上下文窗口信息。

## 功能

- 显示 token 用量百分比
- 显示 MCP 月度用量百分比
- 显示重置倒计时
- 显示当前模型与上下文占用
- 支持 `statusLine`、终端命令、tmux、shell prompt
- 支持 JSON 输出，便于二次集成

示例输出：

```text
[██████░░░░] 5h 63% | [██░░░░░░░░] MCP 21% | ⏰2h14m | zai-pro@ZAI | GLM-4.5(18.2k/128k)
```

## 数据来源

当前实现的取数优先级：

1. ZAI / ZHIPU 平台接口
2. 本地缓存
3. 原始本地分析逻辑

当环境变量 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` 可用，且地址指向以下平台之一时，会优先查询官方接口：

- `https://api.z.ai`
- `https://open.bigmodel.cn`
- `https://dev.bigmodel.cn`

其中：

- token 百分比来自额度接口中的 `TOKENS_LIMIT`
- MCP 百分比来自额度接口中的 `TIME_LIMIT`
- 模型名和上下文窗口信息可从 Claude Code `statusLine` 的 stdin 中补充

## 安装

旧版 README 里的 `install.sh` / `web-install.sh` 一键安装说明已不适用，这个仓库当前建议使用本地安装。

开发模式安装：

```bash
python3 -m pip install -e .
```

或普通安装：

```bash
python3 -m pip install .
```

安装后可用命令：

```bash
claude-statusbar
cstatus
cs
```

## 在 Claude Code 中使用

将命令配置到 `~/.claude/settings.json`：

```json
{
  "statusLine": {
    "type": "command",
    "command": "cs"
  }
}
```

如果你是在带有 ZAI / 智谱接入能力的 Claude Code 环境里运行，并且运行时已经注入：

- `ANTHROPIC_BASE_URL`
- `ANTHROPIC_AUTH_TOKEN`

那么 `cs` 会优先显示对应平台的使用量数据。

## 命令用法

```bash
cs
cs --json-output
cs --detail
cs --plan zai-lite
cs --plan zai-pro
cs --plan zai-max
cs --reset-hour 14
cs --no-color
cs --no-auto-update
```

## 参数说明

| 参数 | 说明 |
| --- | --- |
| `--json-output` | 输出 JSON |
| `--detail` | 输出更详细的用量信息 |
| `--plan` | 手动指定套餐，例如 `zai-lite`、`zai-pro`、`zai-max` |
| `--reset-hour` | 指定本地重置小时数 |
| `--no-color` | 关闭 ANSI 颜色 |
| `--no-auto-update` | 关闭自动更新检查 |

## 环境变量

| 变量 | 作用 |
| --- | --- |
| `ANTHROPIC_BASE_URL` | ZAI / ZHIPU 平台 API 基地址 |
| `ANTHROPIC_AUTH_TOKEN` | 对应平台认证令牌 |
| `CLAUDE_PLAN` | 默认套餐类型 |
| `CLAUDE_RESET_HOUR` | 默认重置小时 |
| `CLAUDE_STATUSBAR_JSON=1` | 默认输出 JSON |
| `CLAUDE_STATUSBAR_NO_UPDATE=1` | 禁用自动更新 |
| `NO_COLOR=1` | 禁用彩色输出 |

## 适用场景

- Claude Code `statusLine`
- tmux 状态栏
- shell prompt
- 独立命令行查询

示例：

```bash
set -g status-right '#(cs)'
```

```bash
RPROMPT='$(cs)'
```

## 已知情况

- 仓库中的旧安装脚本和旧宣传图片不再代表当前版本能力
- 当前项目名和可执行命令仍沿用原始包名 `claude-statusbar`
- 仍保留部分兼容原实现的回退逻辑，因此代码中会看到旧命名

## 开发

本地运行：

```bash
python3 -m claude_statusbar.cli --help
```

可编辑安装后验证版本：

```bash
cs --version
```

## License

MIT
