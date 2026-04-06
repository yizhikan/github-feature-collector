# GitHub 热门仓库新功能需求智能采集与过滤系统

自动从 GitHub 热门仓库中采集和过滤新功能需求，使用通义千问大模型进行语义判断。

## 功能特点

- ✅ 自动获取 OSSInsight 热门仓库榜单
- ✅ 爬取 Issues 和 Discussions
- ✅ 通义千问大模型语义过滤（排除 Bug 修复、文档更新等）
- ✅ 增量去重，避免重复处理
- ✅ 输出 Markdown + JSON 双格式
- ✅ 详细的日志记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制配置文件模板并修改：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入你的通义千问 API Key：

```yaml
qwen:
  api_key: "sk-your-api-key-here"
```

（可选）配置 GitHub Token 以提高 API 限额：

```yaml
github:
  api_token: "ghp_your-token-here"
```

### 3. 运行

```bash
# 使用默认配置（1 个仓库）
python -m src.main

# 指定采集数量
python -m src.main --top-n 10

# 指定配置文件
python -m src.main --config my_config.yaml
```

### 4. 查看结果

输出文件位于 `output/<owner>-<repo>/` 目录：
- `requirements.md` - Markdown 格式需求清单
- `requirements.json` - JSON 格式需求清单

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `collection.top_n` | 1 | 采集热门仓库数量 |
| `github.issues_per_page` | 2 | 每页 Issues 数量 |
| `github.max_pages` | 1 | 处理页数 |
| `github.issue_state` | open | Issue 状态过滤 |
| `github.api_token` | "" | GitHub API Token（可选） |
| `qwen.api_key` | 必填 | 通义千问 API Key |
| `qwen.model` | qwen-plus | 模型名称 |
| `output.base_dir` | output | 输出目录 |
| `output.format` | [markdown, json] | 输出格式 |
| `dedup.storage_file` | processed.json | 去重存储文件 |
| `logging.level` | DEBUG | 日志级别 |

## 输出示例

```markdown
# GitHub 热门仓库新功能需求清单

**仓库**: anthropics/claude-code
**采集时间**: 2026-04-05 12:00:00

---

## 需求 #1: Add workspace-level memory configuration

**来源**: Issue #12345
**链接**: https://github.com/anthropics/claude-code/issues/12345
**互动**: 👍 45, 💬 12

**大模型判断理由**:
属于新增配置模块，支持项目级个性化设置...

**优先级**: 8/10 (高)
```

## 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --name github-collector src/main.py
```

生成的可执行文件位于 `dist/github-collector`

## License

MIT
