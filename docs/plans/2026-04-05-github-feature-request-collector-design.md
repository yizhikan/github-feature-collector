# GitHub 热门仓库新功能需求智能采集与过滤系统设计

**设计日期**: 2026-04-05  
**版本**: 1.0  
**状态**: 已批准

---

## 一、系统概述

### 1.1 目标

构建一个自动化工具，从 GitHub 热门仓库中智能采集和过滤新功能需求：
- 从 OSSInsight API 获取过去一周 Star 增长最快的热门仓库
- 爬取每个仓库的 Issues 和 Discussions
- 使用通义千问 Qwen 大模型进行语义判断与过滤
- 输出结构化的需求清单（Markdown + JSON）

### 1.2 核心约束

- **必须使用的大模型**: 通义千问 Qwen API
- **必须使用的数据源**: OSSInsight API（主）、GitHub Trending 网页（备用）
- **配置与代码分离**: API Key 等敏感信息必须放在配置文件中
- **增量去重**: 避免重复处理相同内容

---

## 二、架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│  (命令行入口：解析参数 → 加载配置 → 执行流程 → 输出报告)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: 获取热门仓库列表                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ github_fetcher.py                                            ││
│  │ - fetch_trending_repos() → OSSInsight API                   ││
│  │ - fallback: 网页爬取 (API 失败时)                              ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: 遍历每个仓库处理                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ github_fetcher  │→ │ github_fetcher  │→ │   qwen_filter   │ │
│  │ fetch_issues()  │  │ fetch_discuss() │  │   filter_one()  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│         ↓                      ↓                      ↓          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ dedup_manager.py (检查 processed.json → 去重判断)            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: 生成输出文件                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ output_generator.py                                          ││
│  │ - generate_markdown() → output/<repo>/requirements.md       ││
│  │ - generate_json() → output/<repo>/requirements.json         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 处理流程

```
[开始]
   ↓
加载 config.yaml
   ↓
调用 OSSInsight API → 获取热门仓库列表
   ↓
遍历每个仓库 ─────────────────────────────┐
   ↓                                      │
┌─────────────────────────────────────┐   │
│ 1. 检查本地去重记录 (processed.json)   │   │
│ 2. 调用 GitHub API 获取 Issues       │   │
│ 3. 调用 GitHub API 获取 Discussions  │   │
│ 4. 对每条内容：                      │   │
│    ├─ 检查是否已处理 → 跳过          │   │
│    ├─ 调用 Qwen API 判断             │   │
│    └─ 通过 → 暂存结果               │   │
│ 5. 更新 processed.json               │   │
│ 6. 生成 output/<repo>/requirements.* │←──┘
   ↓
所有仓库处理完成
   ↓
输出统计报告
   ↓
[结束]
```

---

## 三、模块设计

### 3.1 模块清单

| 模块 | 职责 | 关键函数 |
|------|------|----------|
| `config_loader.py` | 加载 config.yaml，校验必填字段 | `load_config()`, `validate()` |
| `github_fetcher.py` | GitHub API 调用，网页爬取备用 | `fetch_trending_repos()`, `fetch_issues()`, `fetch_discussions()` |
| `qwen_filter.py` | 通义千问 API 调用，语义判断 | `filter_content()`, `parse_response()` |
| `dedup_manager.py` | processed.json 读写，去重判断 | `is_processed()`, `mark_processed()` |
| `output_generator.py` | 生成 Markdown/JSON | `generate_markdown()`, `generate_json()` |
| `logger.py` | 日志配置 | `setup_logger()` |
| `main.py` | 流程编排 | `main()`, `process_repo()` |

### 3.2 执行模型

**方案 A：模块化单进程架构（串行执行）**

- 从 OSSInsight API 获取一个仓库 → 处理该仓库的 Issues/Discussions → 调用 Qwen API 判断 → 输出结果
- 然后处理下一个仓库
- 优点：结构简单，易于调试，适合中小规模采集

---

## 四、配置文件设计

### 4.1 config.yaml 结构

```yaml
# 采集配置
collection:
  top_n: 1  # 采集热门仓库数量，运行时命令行参数可覆盖

# GitHub 配置
github:
  api_token: ""  # 可选，留空时使用未认证 API
  issues_per_page: 2
  max_pages: 1
  issue_state: "open"
  sort_by: "created"
  sort_direction: "desc"
  request_interval: 1.0  # 秒

# 通义千问配置
qwen:
  api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  model: "qwen-plus"
  request_interval: 0.5  # 秒

# 输出配置
output:
  base_dir: "output"
  format: ["markdown", "json"]

# 去重配置
dedup:
  storage_file: "processed.json"

# 重试配置
retry:
  max_retries: 3
  backoff_multiplier: 2

# 日志配置
logging:
  level: "DEBUG"
  file: "logs/app.log"
```

### 4.2 命令行参数

```bash
# 使用配置文件中的 top_n (默认 1)
python main.py

# 命令行覆盖 top_n
python main.py --top-n 10
```

---

## 五、大模型 Prompt 设计

### 5.1 System Prompt

```
你是一个技术需求分析师。请分析以下 GitHub Issue/Discussion 内容，判断是否属于"新功能需求"。

【收录标准】
✅ 全新功能、新增模块、架构级重构、跨平台支持、插件体系、API 扩展、重大新能力

【排除标准】
❌ Bug 修复、文案/样式/UI 小改、文档更新、参数调整、现有功能小优化、体验微调

【输出格式】(严格 JSON)
{
  "included": true/false,
  "summary": "需求摘要 (50 字内)",
  "reason": "判断理由",
  "value": "需求价值与实现意义",
  "priority_score": 1-10
}
```

### 5.2 用户 Prompt 模板

```
【输入内容】
标题：{title}
正文：{body}
互动数据：👍 {reactions}, 💬 {comments}
链接：{url}
```

---

## 六、输出文件设计

### 6.1 目录结构

```
output/
└── {owner}-{repo}/
    ├── requirements.md
    └── requirements.json
```

### 6.2 Markdown 输出格式

```markdown
# GitHub 热门仓库新功能需求清单

**仓库**: anthropics/claude-code
**采集时间**: 2026-04-05 12:00:00
**筛选条件**: open issues, created desc, 2 issues/page, 1 page

---

## 需求 #1: Add workspace-level memory configuration

**来源**: Issue #12345
**链接**: https://github.com/anthropics/claude-code/issues/12345
**创建时间**: 2026-04-01
**互动**: 👍 45, 💬 12

**原始摘要**:
用户希望在 CLAUDE.md 中支持项目级记忆配置，而非仅全局配置...

**大模型判断理由**:
属于新增配置模块，支持项目级个性化设置，符合架构扩展需求...

**需求价值**:
提升多项目场景下的使用体验，减少重复配置...

**优先级**: 8/10 (高)
```

### 6.3 JSON 输出格式

```json
{
  "repo": "anthropics/claude-code",
  "collected_at": "2026-04-05T12:00:00Z",
  "requirements": [
    {
      "title": "Add workspace-level memory configuration",
      "source_url": "https://github.com/anthropics/claude-code/issues/12345",
      "created_at": "2026-04-01",
      "summary": "...",
      "reason": "...",
      "value": "...",
      "priority": 8
    }
  ]
}
```

---

## 七、技术决策

### 7.1 依赖选型

| 用途 | 库 | 理由 |
|------|-----|------|
| HTTP 客户端 | `requests` | 简单可靠，足够用 |
| YAML 解析 | `pyyaml` | Python 生态标准 |
| 打包 | `pyinstaller` | 跨平台支持好 |
| 日志 | `logging` | Python 标准库 |

### 7.2 核心策略

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 并发策略 | 串行 | 首版简单可靠，易调试 |
| 去重存储 | JSON 文件 | 轻量，无需依赖 |
| 重试策略 | 指数退避 | 适合 API 限流场景 |
| Issue 选择 | 最新 open | 配置文件可调整 |
| 大模型调用 | 单条调用 | 简单，避免 token 超限 |

---

## 八、测试策略

### 8.1 测试数据集

- **仓库数**: 1 个
- **Issue 数**: 1 个
- **Discussion 数**: 1 个

### 8.2 验证点

1. OSSInsight API 调用成功
2. GitHub API 调用成功
3. Qwen API 调用成功
4. 去重记录正确写入
5. Markdown 输出格式正确
6. JSON 输出格式正确

---

## 九、交付物清单

1. 完整可运行代码（7 个 Python 模块）
2. `requirements.txt`
3. `config.yaml`（配置文件模板）
4. 使用说明（README.md）
5. 示例需求清单（测试运行生成）

---

## 十、附录

### A. API 端点

- OSSInsight Trending API: `https://api.ossinsight.io/v1/trends/repos?period=past_week`
- GitHub Issues API: `https://api.github.com/repos/{owner}/{repo}/issues`
- GitHub Discussions API: `https://api.github.com/repos/{owner}/{repo}/discussions`
- Qwen API: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`

### B. 速率限制

| API | 限制 | 本策略 |
|-----|------|--------|
| OSSInsight | 未知 | 单次调用 |
| GitHub (未认证) | 60/小时 | 间隔 1 秒 |
| GitHub (认证) | 5000/小时 | 间隔 1 秒 |
| Qwen | 取决于配额 | 间隔 0.5 秒 |

---

**设计批准**: ✅ 用户已确认
