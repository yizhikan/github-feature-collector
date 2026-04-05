# GitHub 热门仓库新功能需求智能采集与过滤系统实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个自动化工具，从 GitHub 热门仓库中智能采集和过滤新功能需求，输出 Markdown 和 JSON 格式的需求清单。

**Architecture:** 模块化单进程架构（方案 A），串行执行：获取热门仓库 → 爬取 Issues/Discussions → 调用 Qwen API 过滤 → 生成输出文件。

**Tech Stack:** Python 3.10+, requests, pyyaml, pyinstaller

---

## 任务清单

| 任务 | 组件 | 预计时间 |
|------|------|----------|
| 1 | 项目骨架与配置文件 | 5 分钟 |
| 2 | 日志模块 | 5 分钟 |
| 3 | 配置加载模块 | 10 分钟 |
| 4 | 去重管理模块 | 10 分钟 |
| 5 | GitHub 数据获取模块 | 20 分钟 |
| 6 | Qwen 大模型过滤模块 | 15 分钟 |
| 7 | 输出生成模块 | 15 分钟 |
| 8 | 主流程编排 | 15 分钟 |
| 9 | requirements.txt 与配置模板 | 5 分钟 |
| 10 | README 使用说明 | 10 分钟 |
| 11 | 真实数据测试运行 | 10 分钟 |
| 12 | PyInstaller 打包配置 | 10 分钟 |

---

### Task 1: 项目骨架与配置文件

**Files:**
- Create: `config.yaml`
- Create: `src/`
- Create: `output/`
- Create: `logs/`

**Step 1: 创建项目目录结构**

```bash
mkdir -p src output logs
```

**Step 2: 创建 config.yaml**

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
  api_key: "sk-3f1064f79d9d45cda7d58005b89ff926"
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

**Step 3: 提交**

```bash
git add config.yaml
git commit -m "chore: add project skeleton and config template"
```

---

### Task 2: 日志模块

**Files:**
- Create: `src/logger.py`
- Modify: `config.yaml` (已有 logging 配置)

**Step 1: 编写日志模块**

```python
"""日志配置模块"""
import logging
import os
from datetime import datetime


def setup_logger(config: dict) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        config: 日志配置字典
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger('github_collector')
    logger.setLevel(getattr(logging, config['level'].upper()))
    
    # 确保日志目录存在
    log_file = config.get('file', 'logs/app.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

**Step 2: 验证日志模块**

```bash
python -c "from src.logger import setup_logger; logger = setup_logger({'level': 'DEBUG', 'file': 'logs/test.log'}); logger.info('Test')"
```

Expected: 日志输出到 logs/test.log 和控制台

**Step 3: 提交**

```bash
git add src/logger.py
git commit -m "feat: add logger module"
```

---

### Task 3: 配置加载模块

**Files:**
- Create: `src/config_loader.py`
- Test: `tests/test_config_loader.py`

**Step 1: 编写配置加载模块**

```python
"""配置文件加载模块"""
import os
import yaml
from typing import Any, Dict


class ConfigError(Exception):
    """配置错误异常"""
    pass


def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    加载 YAML 配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        ConfigError: 配置文件不存在或格式错误
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"配置文件不存在：{config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    validate_config(config)
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    校验配置项是否完整
    
    Args:
        config: 配置字典
        
    Raises:
        ConfigError: 缺少必填配置项
    """
    required_keys = [
        'collection',
        'github',
        'qwen',
        'output',
        'dedup',
        'retry',
        'logging'
    ]
    
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"缺少必填配置项：{key}")
    
    # 校验 Qwen API Key
    if not config.get('qwen', {}).get('api_key'):
        raise ConfigError("qwen.api_key 不能为空")
    
    # 校验默认值
    config.setdefault('collection', {})
    config['collection'].setdefault('top_n', 1)
    
    config['github'].setdefault('issues_per_page', 2)
    config['github'].setdefault('max_pages', 1)
    config['github'].setdefault('issue_state', 'open')
    config['github'].setdefault('sort_by', 'created')
    config['github'].setdefault('sort_direction', 'desc')
    config['github'].setdefault('request_interval', 1.0)
    
    config['qwen'].setdefault('model', 'qwen-plus')
    config['qwen'].setdefault('request_interval', 0.5)
    
    config['output'].setdefault('base_dir', 'output')
    config['output'].setdefault('format', ['markdown', 'json'])
    
    config['dedup'].setdefault('storage_file', 'processed.json')
    
    config['retry'].setdefault('max_retries', 3)
    config['retry'].setdefault('backoff_multiplier', 2)
    
    config['logging'].setdefault('level', 'DEBUG')
    config['logging'].setdefault('file', 'logs/app.log')
```

**Step 2: 编写测试**

```python
"""tests/test_config_loader.py"""
import pytest
import yaml
import os
from src.config_loader import load_config, ConfigError


class TestConfigLoader:
    """测试配置加载模块"""
    
    def test_load_valid_config(self, tmp_path):
        """测试加载有效配置"""
        config_content = """
collection:
  top_n: 5
github:
  api_token: ""
qwen:
  api_key: "sk-test"
output:
  base_dir: "output"
dedup:
  storage_file: "processed.json"
retry:
  max_retries: 3
logging:
  level: "DEBUG"
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        assert config['collection']['top_n'] == 5
    
    def test_load_missing_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(ConfigError):
            load_config('nonexistent.yaml')
    
    def test_validate_missing_qwen_key(self, tmp_path):
        """测试缺少 Qwen API Key"""
        config_content = """
collection: {}
github: {}
qwen: {}
output: {}
dedup: {}
retry: {}
logging: {}
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ConfigError, match="qwen.api_key"):
            load_config(str(config_file))
```

**Step 3: 运行测试**

```bash
pip install pytest
pytest tests/test_config_loader.py -v
```

Expected: 所有测试通过

**Step 4: 提交**

```bash
git add src/config_loader.py tests/test_config_loader.py
git commit -m "feat: add config loader with tests"
```

---

### Task 4: 去重管理模块

**Files:**
- Create: `src/dedup_manager.py`
- Test: `tests/test_dedup_manager.py`

**Step 1: 编写去重管理模块**

```python
"""去重管理模块"""
import json
import os
from typing import Set


class DedupManager:
    """
    去重管理器
    使用 JSON 文件存储已处理的 Issue/Discussion ID
    """
    
    def __init__(self, storage_file: str):
        """
        Args:
            storage_file: 去重数据存储文件路径
        """
        self.storage_file = storage_file
        self.processed_ids: Set[str] = self._load()
    
    def _load(self) -> Set[str]:
        """从文件加载已处理的 ID"""
        if not os.path.exists(self.storage_file):
            return set()
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except (json.JSONDecodeError, KeyError):
            return set()
    
    def _save(self) -> None:
        """保存已处理的 ID 到文件"""
        os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump({'processed_ids': list(self.processed_ids)}, f, indent=2)
    
    def is_processed(self, item_id: str) -> bool:
        """
        检查是否已处理
        
        Args:
            item_id: Issue/Discussion ID
            
        Returns:
            True 如果已处理，False 否则
        """
        return item_id in self.processed_ids
    
    def mark_processed(self, item_id: str) -> None:
        """
        标记为已处理
        
        Args:
            item_id: Issue/Discussion ID
        """
        if item_id not in self.processed_ids:
            self.processed_ids.add(item_id)
            self._save()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'total_processed': len(self.processed_ids),
            'storage_file': self.storage_file
        }
```

**Step 2: 编写测试**

```python
"""tests/test_dedup_manager.py"""
import pytest
import os
from src.dedup_manager import DedupManager


class TestDedupManager:
    """测试去重管理模块"""
    
    def test_new_manager_empty_storage(self, tmp_path):
        """测试新建管理器（空存储）"""
        storage_file = str(tmp_path / "processed.json")
        manager = DedupManager(storage_file)
        
        assert manager.is_processed("issue-1") == False
        assert manager.get_stats()['total_processed'] == 0
    
    def test_mark_and_check(self, tmp_path):
        """测试标记和检查"""
        storage_file = str(tmp_path / "processed.json")
        manager = DedupManager(storage_file)
        
        manager.mark_processed("issue-1")
        assert manager.is_processed("issue-1") == True
        assert manager.is_processed("issue-2") == False
    
    def test_persistence(self, tmp_path):
        """测试持久化"""
        storage_file = str(tmp_path / "processed.json")
        
        # 第一次创建并标记
        manager1 = DedupManager(storage_file)
        manager1.mark_processed("issue-1")
        
        # 重新加载
        manager2 = DedupManager(storage_file)
        assert manager2.is_processed("issue-1") == True
```

**Step 3: 运行测试**

```bash
pytest tests/test_dedup_manager.py -v
```

Expected: 所有测试通过

**Step 4: 提交**

```bash
git add src/dedup_manager.py tests/test_dedup_manager.py
git commit -m "feat: add dedup manager with tests"
```

---

### Task 5: GitHub 数据获取模块

**Files:**
- Create: `src/github_fetcher.py`
- Test: `tests/test_github_fetcher.py`

**Step 1: 编写 GitHub 数据获取模块**

```python
"""GitHub 数据获取模块"""
import time
import requests
from typing import List, Dict, Any, Optional
from src.logger import setup_logger

logger = setup_logger({'level': 'DEBUG', 'file': 'logs/app.log'})


class GitHubFetcher:
    """GitHub API 数据获取器"""
    
    BASE_URL = "https://api.github.com"
    OSSINSIGHT_URL = "https://api.ossinsight.io/v1/trends/repos"
    
    def __init__(self, config: dict):
        """
        Args:
            config: GitHub 配置字典
        """
        self.token = config.get('api_token', '')
        self.request_interval = config.get('request_interval', 1.0)
        self.issues_per_page = config.get('issues_per_page', 2)
        self.max_pages = config.get('max_pages', 1)
        self.issue_state = config.get('issue_state', 'open')
        self.sort_by = config.get('sort_by', 'created')
        self.sort_direction = config.get('sort_direction', 'desc')
        
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        else:
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def _request(self, url: str, params: Optional[dict] = None) -> Optional[Dict]:
        """
        发送 HTTP 请求，带重试和速率限制
        
        Args:
            url: 请求 URL
            params: 查询参数
            
        Returns:
            JSON 响应数据，失败返回 None
        """
        try:
            time.sleep(self.request_interval)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败：{url}, 错误：{e}")
            return None
    
    def fetch_trending_repos(self, top_n: int = 1) -> List[Dict]:
        """
        从 OSSInsight API 获取热门仓库
        
        Args:
            top_n: 获取前 N 个热门仓库
            
        Returns:
            仓库列表
        """
        logger.info(f"正在获取热门仓库列表 (TOP {top_n})...")
        
        params = {'period': 'past_week'}
        data = self._request(self.OSSINSIGHT_URL, params)
        
        if not data or 'data' not in data:
            logger.error("OSSInsight API 调用失败")
            return []
        
        repos = data['data'][:top_n]
        logger.info(f"成功获取 {len(repos)} 个热门仓库")
        
        return repos
    
    def fetch_issues(self, owner: str, repo: str) -> List[Dict]:
        """
        获取仓库的 Issues
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            Issues 列表
        """
        logger.debug(f"正在获取 {owner}/{repo} 的 Issues...")
        
        all_issues = []
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        
        for page in range(1, self.max_pages + 1):
            params = {
                'state': self.issue_state,
                'sort': self.sort_by,
                'direction': self.sort_direction,
                'per_page': self.issues_per_page,
                'page': page
            }
            
            issues = self._request(url, params)
            if not issues:
                logger.warning(f"获取 Issues 失败：{owner}/{repo} page {page}")
                break
            
            if not issues:  # 空列表表示没有更多数据
                break
            
            all_issues.extend(issues)
            logger.debug(f"获取到 {len(issues)} 条 Issues (page {page})")
            
            if len(issues) < self.issues_per_page:
                break
        
        logger.info(f"{owner}/{repo} 共获取到 {len(all_issues)} 条 Issues")
        return all_issues
    
    def fetch_discussions(self, owner: str, repo: str) -> List[Dict]:
        """
        获取仓库的 Discussions (GraphQL API)
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            Discussions 列表
        """
        logger.debug(f"正在获取 {owner}/{repo} 的 Discussions...")
        
        # GitHub Discussions 需要 GraphQL API
        graphql_url = f"{self.BASE_URL}/graphql"
        
        query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                discussions(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
                    nodes {
                        id
                        number
                        title
                        body
                        url
                        createdAt
                        updatedAt
                        author {
                            login
                        }
                        comments(first: 100) {
                            totalCount
                        }
                        upvotes: reactions(content: THUMBS_UP) {
                            totalCount
                        }
                    }
                }
            }
        }
        """
        
        variables = {'owner': owner, 'repo': repo}
        
        if not self.token:
            logger.warning(f"Discussions API 需要认证 Token，跳过：{owner}/{repo}")
            return []
        
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.post(
            graphql_url,
            json={'query': query, 'variables': variables},
            timeout=30
        )
        
        if response.status_code != 200:
            logger.warning(f"Discussions API 调用失败：{owner}/{repo}")
            return []
        
        try:
            data = response.json()
            discussions = data.get('data', {}).get('repository', {}).get('discussions', {}).get('nodes', [])
            logger.info(f"{owner}/{repo} 共获取到 {len(discussions)} 条 Discussions")
            return discussions
        except (json.JSONDecodeError, KeyError):
            logger.error(f"解析 Discussions 响应失败：{owner}/{repo}")
            return []
```

**Step 2: 编写测试**

```python
"""tests/test_github_fetcher.py"""
import pytest
from src.github_fetcher import GitHubFetcher


class TestGitHubFetcher:
    """测试 GitHub 数据获取模块"""
    
    @pytest.fixture
    def fetcher_no_token(self):
        return GitHubFetcher({'api_token': '', 'request_interval': 0})
    
    @pytest.fixture
    def fetcher_with_token(self):
        import os
        token = os.environ.get('GITHUB_TOKEN', '')
        return GitHubFetcher({'api_token': token, 'request_interval': 0})
    
    def test_fetch_trending_repos(self, fetcher_no_token):
        """测试获取热门仓库（实时 API）"""
        repos = fetcher_no_token.fetch_trending_repos(top_n=1)
        assert isinstance(repos, list)
        if repos:
            assert 'full_name' in repos[0] or 'repo' in repos[0]
    
    def test_fetch_issues_real(self, fetcher_no_token):
        """测试获取 Issues（实时 API）"""
        issues = fetcher_no_token.fetch_issues('anthropics', 'claude-code')
        assert isinstance(issues, list)
        # 验证基本字段
        if issues:
            assert 'title' in issues[0]
            assert 'body' in issues[0]
```

**Step 3: 运行测试**

```bash
pytest tests/test_github_fetcher.py -v
```

Expected: 所有测试通过（实时 API 调用）

**Step 4: 提交**

```bash
git add src/github_fetcher.py tests/test_github_fetcher.py
git commit -m "feat: add GitHub fetcher module"
```

---

### Task 6: Qwen 大模型过滤模块

**Files:**
- Create: `src/qwen_filter.py`
- Test: `tests/test_qwen_filter.py`

**Step 1: 编写 Qwen 过滤模块**

```python
"""通义千问大模型过滤模块"""
import json
import time
import requests
from typing import Dict, Any, Optional
from src.logger import setup_logger

logger = setup_logger({'level': 'DEBUG', 'file': 'logs/app.log'})


SYSTEM_PROMPT = """你是一个技术需求分析师。请分析以下 GitHub Issue/Discussion 内容，判断是否属于"新功能需求"。

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
}"""


class QwenFilter:
    """通义千问大模型过滤器"""
    
    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    def __init__(self, config: dict):
        """
        Args:
            config: Qwen 配置字典
        """
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'qwen-plus')
        self.request_interval = config.get('request_interval', 0.5)
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def filter_content(
        self,
        title: str,
        body: str,
        url: str,
        reactions: int = 0,
        comments: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        调用 Qwen API 进行内容过滤
        
        Args:
            title: 标题
            body: 正文
            url: 链接
            reactions: 互动数（点赞等）
            comments: 评论数
            
        Returns:
            大模型返回的结构化结果，失败返回 None
        """
        user_prompt = f"""【输入内容】
标题：{title[:500]}
正文：{body[:2000] if body else '无'}
链接：{url}
互动数据：👍 {reactions}, 💬 {comments}"""
        
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt}
        ]
        
        payload = {
            'model': self.model,
            'input': {'messages': messages},
            'parameters': {
                'result_format': 'message',
                'temperature': 0.1
            }
        }
        
        try:
            time.sleep(self.request_interval)
            response = self.session.post(self.API_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return self._parse_response(content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API 调用失败：{e}")
            return None
        except Exception as e:
            logger.error(f"解析 Qwen 响应失败：{e}")
            return None
    
    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析大模型返回的 JSON
        
        Args:
            content: 大模型返回的内容
            
        Returns:
            解析后的字典，失败返回 None
        """
        try:
            # 尝试提取 JSON（处理可能的 markdown 包裹）
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            return None
```

**Step 2: 编写测试**

```python
"""tests/test_qwen_filter.py"""
import pytest
import os
from src.qwen_filter import QwenFilter


class TestQwenFilter:
    """测试 Qwen 过滤模块"""
    
    @pytest.fixture
    def qwen_filter(self):
        config = {
            'api_key': os.environ.get('QWEN_API_KEY', 'sk-3f1064f79d9d45cda7d58005b89ff926'),
            'model': 'qwen-plus',
            'request_interval': 0.5
        }
        return QwenFilter(config)
    
    def test_filter_issue_real(self, qwen_filter):
        """测试过滤 Issue（实时 API）"""
        result = qwen_filter.filter_content(
            title="Add workspace-level memory configuration",
            body="We should support project-level memory config in CLAUDE.md...",
            url="https://github.com/test/repo/issues/1",
            reactions=10,
            comments=5
        )
        
        assert result is not None
        assert 'included' in result
        assert 'summary' in result
        assert isinstance(result['included'], bool)
```

**Step 3: 运行测试**

```bash
export QWEN_API_KEY="sk-3f1064f79d9d45cda7d58005b89ff926"
pytest tests/test_qwen_filter.py -v
```

Expected: 所有测试通过（实时 API 调用）

**Step 4: 提交**

```bash
git add src/qwen_filter.py tests/test_qwen_filter.py
git commit -m "feat: add Qwen filter module"
```

---

### Task 7: 输出生成模块

**Files:**
- Create: `src/output_generator.py`
- Test: `tests/test_output_generator.py`

**Step 1: 编写输出生成模块**

```python
"""输出生成模块"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any


class OutputGenerator:
    """需求清单输出生成器"""
    
    def __init__(self, config: dict):
        """
        Args:
            config: 输出配置字典
        """
        self.base_dir = config.get('base_dir', 'output')
        self.formats = config.get('format', ['markdown', 'json'])
    
    def generate(
        self,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict
    ) -> Dict[str, str]:
        """
        生成输出文件
        
        Args:
            repo: 仓库名称 (owner/repo)
            requirements: 需求列表
            config_summary: 配置摘要
            
        Returns:
            生成的文件路径字典
        """
        owner, repo_name = repo.split('/') if '/' in repo else ('unknown', repo)
        output_dir = os.path.join(self.base_dir, f"{owner}-{repo_name}")
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = {}
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'markdown' in self.formats:
            md_path = os.path.join(output_dir, 'requirements.md')
            self._generate_markdown(md_path, repo, requirements, config_summary, timestamp)
            generated_files['markdown'] = md_path
        
        if 'json' in self.formats:
            json_path = os.path.join(output_dir, 'requirements.json')
            self._generate_json(json_path, repo, requirements, config_summary, timestamp)
            generated_files['json'] = json_path
        
        return generated_files
    
    def _generate_markdown(
        self,
        path: str,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict,
        timestamp: str
    ) -> None:
        """生成 Markdown 文件"""
        content = f"""# GitHub 热门仓库新功能需求清单

**仓库**: {repo}
**采集时间**: {timestamp}
**筛选条件**: {config_summary.get('issue_state', 'open')} issues, {config_summary.get('sort_by', 'created')} {config_summary.get('sort_direction', 'desc')}

---
"""
        
        for i, req in enumerate(requirements, 1):
            priority_label = {
                (9, 10): '很高',
                (7, 8): '高',
                (4, 6): '中',
                (1, 3): '低'
            }
            priority = req.get('priority_score', 5)
            label = next((v for k, v in priority_label.items() if priority in range(k[0], k[1]+1)), '中')
            
            content += f"""
## 需求 #{i}: {req.get('title', 'Untitled')}

**来源**: {req.get('source_type', 'Issue')} #{req.get('number', '')}
**链接**: {req.get('url', '')}
**创建时间**: {req.get('created_at', 'Unknown')}
**互动**: 👍 {req.get('reactions', 0)}, 💬 {req.get('comments', 0)}

**原始摘要**:
{req.get('original_summary', '无')}

**大模型判断理由**:
{req.get('reason', '无')}

**需求价值**:
{req.get('value', '无')}

**优先级**: {priority}/10 ({label})

---
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_json(
        self,
        path: str,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict,
        timestamp: str
    ) -> None:
        """生成 JSON 文件"""
        data = {
            'repo': repo,
            'collected_at': timestamp,
            'filter_config': config_summary,
            'requirements': requirements
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

**Step 2: 编写测试**

```python
"""tests/test_output_generator.py"""
import pytest
import os
import json
from src.output_generator import OutputGenerator


class TestOutputGenerator:
    """测试输出生成模块"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        config = {
            'base_dir': str(tmp_path / 'output'),
            'format': ['markdown', 'json']
        }
        return OutputGenerator(config)
    
    def test_generate_both_formats(self, generator, tmp_path):
        """测试生成两种格式"""
        requirements = [{
            'title': 'Test Feature',
            'source_type': 'Issue',
            'number': 1,
            'url': 'https://github.com/test/repo/issues/1',
            'created_at': '2026-04-05',
            'reactions': 10,
            'comments': 5,
            'original_summary': 'Test summary',
            'reason': 'Test reason',
            'value': 'Test value',
            'priority_score': 8,
            'included': True
        }]
        
        config_summary = {'issue_state': 'open', 'sort_by': 'created', 'sort_direction': 'desc'}
        
        files = generator.generate('test/repo', requirements, config_summary)
        
        assert 'markdown' in files
        assert 'json' in files
        assert os.path.exists(files['markdown'])
        assert os.path.exists(files['json'])
    
    def test_json_structure(self, generator, tmp_path):
        """测试 JSON 结构"""
        requirements = [{'title': 'Test', 'included': True}]
        config_summary = {}
        
        files = generator.generate('test/repo', requirements, config_summary)
        
        with open(files['json'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'repo' in data
        assert 'requirements' in data
```

**Step 3: 运行测试**

```bash
pytest tests/test_output_generator.py -v
```

Expected: 所有测试通过

**Step 4: 提交**

```bash
git add src/output_generator.py tests/test_output_generator.py
git commit -m "feat: add output generator module"
```

---

### Task 8: 主流程编排

**Files:**
- Create: `src/main.py`
- Modify: `config.yaml` (确认配置完整)

**Step 1: 编写主程序**

```python
#!/usr/bin/env python3
"""
GitHub 热门仓库新功能需求智能采集与过滤系统
主程序入口
"""
import argparse
import sys
from datetime import datetime

from src.config_loader import load_config, ConfigError
from src.logger import setup_logger
from src.github_fetcher import GitHubFetcher
from src.qwen_filter import QwenFilter
from src.dedup_manager import DedupManager
from src.output_generator import OutputGenerator


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='GitHub 热门仓库新功能需求智能采集与过滤系统'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        help='采集热门仓库数量（覆盖配置文件）'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='配置文件路径 (默认：config.yaml)'
    )
    return parser.parse_args()


def process_item(fetcher, qwen_filter, dedup, item: dict, item_type: str) -> dict:
    """
    处理单条 Issue/Discussion
    
    Args:
        fetcher: GitHub 获取器（用于重试等）
        qwen_filter: Qwen 过滤器
        dedup: 去重管理器
        item: Issue/Discussion 数据
        item_type: 'Issue' 或 'Discussion'
        
    Returns:
        处理结果字典，不包含则返回 None
    """
    item_id = str(item.get('id', '') or item.get('number', ''))
    
    if not item_id:
        return None
    
    # 检查去重
    if dedup.is_processed(item_id):
        return None
    
    # 提取基本信息
    title = item.get('title', '')
    body = item.get('body', '')
    url = item.get('url', '') or item.get('html_url', '')
    
    # 提取互动数据
    reactions = item.get('reactions', {}).get('total_count', 0) or \
                item.get('upvotes', {}).get('totalCount', 0) or 0
    comments = item.get('comments', {}).get('total_count', 0) or \
               item.get('comments', {}).get('totalCount', 0) or 0
    
    # 调用大模型过滤
    result = qwen_filter.filter_content(
        title=title,
        body=body,
        url=url,
        reactions=reactions,
        comments=comments
    )
    
    if not result or not result.get('included'):
        # 标记为已处理（即使不收录）
        dedup.mark_processed(item_id)
        return None
    
    # 构建结果
    return {
        'title': title,
        'source_type': item_type,
        'number': item.get('number', ''),
        'url': url,
        'created_at': item.get('created_at', item.get('createdAt', 'Unknown')),
        'reactions': reactions,
        'comments': comments,
        'original_summary': body[:200] + '...' if len(body) > 200 else body,
        'summary': result.get('summary', ''),
        'reason': result.get('reason', ''),
        'value': result.get('value', ''),
        'priority_score': result.get('priority_score', 5),
        'included': True
    }


def process_repo(fetcher, qwen_filter, dedup, repo: dict) -> list:
    """
    处理单个仓库
    
    Args:
        fetcher: GitHub 获取器
        qwen_filter: Qwen 过滤器
        dedup: 去重管理器
        repo: 仓库信息
        
    Returns:
        需求列表
    """
    full_name = repo.get('full_name', repo.get('repo', ''))
    if '/' not in full_name:
        return []
    
    owner, repo_name = full_name.split('/', 1)
    
    logger.info(f"开始处理仓库：{owner}/{repo_name}")
    
    requirements = []
    
    # 获取并处理 Issues
    issues = fetcher.fetch_issues(owner, repo_name)
    for issue in issues:
        # 跳过 PR（GitHub API 中 PR 也返回在 issues 中）
        if 'pull_request' in issue:
            continue
        
        result = process_item(fetcher, qwen_filter, dedup, issue, 'Issue')
        if result:
            requirements.append(result)
    
    # 获取并处理 Discussions
    discussions = fetcher.fetch_discussions(owner, repo_name)
    for discussion in discussions:
        result = process_item(fetcher, qwen_filter, dedup, discussion, 'Discussion')
        if result:
            requirements.append(result)
    
    logger.info(f"仓库 {owner}/{repo_name} 处理完成，收录 {len(requirements)} 条需求")
    return requirements


def main():
    """主函数"""
    args = parse_args()
    
    # 加载配置
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"配置错误：{e}", file=sys.stderr)
        sys.exit(1)
    
    # 覆盖 top_n
    if args.top_n:
        config['collection']['top_n'] = args.top_n
    
    # 初始化日志
    global logger
    logger = setup_logger(config['logging'])
    
    logger.info("=" * 60)
    logger.info("GitHub 热门仓库新功能需求智能采集与过滤系统")
    logger.info(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"采集数量：TOP {config['collection']['top_n']}")
    logger.info("=" * 60)
    
    # 初始化组件
    github_fetcher = GitHubFetcher(config['github'])
    qwen_filter = QwenFilter(config['qwen'])
    dedup = DedupManager(config['dedup']['storage_file'])
    output_generator = OutputGenerator(config['output'])
    
    # 获取热门仓库
    repos = github_fetcher.fetch_trending_repos(config['collection']['top_n'])
    if not repos:
        logger.error("未能获取热门仓库列表")
        sys.exit(1)
    
    all_requirements = []
    
    # 处理每个仓库
    for repo in repos:
        requirements = process_repo(github_fetcher, qwen_filter, dedup, repo)
        full_name = repo.get('full_name', repo.get('repo', ''))
        
        if requirements:
            # 生成输出文件
            config_summary = {
                'issue_state': config['github']['issue_state'],
                'sort_by': config['github']['sort_by'],
                'sort_direction': config['github']['sort_direction'],
                'issues_per_page': config['github']['issues_per_page'],
                'max_pages': config['github']['max_pages']
            }
            
            files = output_generator.generate(full_name, requirements, config_summary)
            logger.info(f"已生成输出文件：{', '.join(files.values())}")
        
        all_requirements.extend(requirements)
    
    # 输出统计
    logger.info("=" * 60)
    logger.info("处理完成")
    logger.info(f"处理仓库数：{len(repos)}")
    logger.info(f"收录需求数：{len(all_requirements)}")
    logger.info(f"去重记录数：{dedup.get_stats()['total_processed']}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
```

**Step 2: 创建 src/__init__.py**

```python
"""GitHub 热门仓库新功能需求智能采集与过滤系统"""
__version__ = '1.0.0'
```

**Step 3: 测试运行（最小数据集）**

```bash
# 确保配置正确
cat config.yaml

# 运行程序（1 个仓库）
python src/main.py --top-n 1
```

Expected: 程序正常运行，生成 output 目录下的需求清单

**Step 4: 提交**

```bash
git add src/main.py src/__init__.py
git commit -m "feat: add main program entry point"
```

---

### Task 9: requirements.txt 与配置模板

**Files:**
- Create: `requirements.txt`
- Create: `config.example.yaml`

**Step 1: 创建 requirements.txt**

```
requests>=2.28.0
pyyaml>=6.0
pyinstaller>=5.0
```

**Step 2: 创建配置模板**

```bash
cp config.yaml config.example.yaml
```

然后编辑 `config.example.yaml`，将 API Key 替换为占位符：

```yaml
# 通义千问配置
qwen:
  api_key: "YOUR_QWEN_API_KEY_HERE"
  model: "qwen-plus"
  request_interval: 0.5
```

**Step 3: 提交**

```bash
git add requirements.txt config.example.yaml
git commit -m "chore: add requirements.txt and config template"
```

---

### Task 10: README 使用说明

**Files:**
- Create: `README.md`

**Step 1: 编写 README**

```markdown
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
python src/main.py

# 指定采集数量
python src/main.py --top-n 10

# 指定配置文件
python src/main.py --config my_config.yaml
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
```

**Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```

---

### Task 11: 真实数据测试运行

**Files:**
- 无新增文件

**Step 1: 运行完整测试**

```bash
# 确保配置正确
cat config.yaml

# 运行程序（1 个仓库，最小数据集）
python src/main.py --top-n 1
```

Expected: 
- 成功获取热门仓库
- 成功获取 Issues/Discussions
- 成功调用 Qwen API
- 生成 output 目录下的需求清单

**Step 2: 验证输出**

```bash
# 检查输出目录
ls -la output/

# 查看 Markdown 输出
cat output/*/requirements.md

# 查看 JSON 输出
cat output/*/requirements.json
```

**Step 3: 检查日志**

```bash
cat logs/app.log | tail -50
```

**Step 4: 提交输出（可选）**

```bash
git add output/ -f
git commit -m "docs: add sample output from test run"
```

---

### Task 12: PyInstaller 打包配置

**Files:**
- Create: `build.sh`

**Step 1: 创建打包脚本**

```bash
#!/bin/bash
# PyInstaller 打包脚本

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Building executable..."
pyinstaller --onefile \
    --name github-collector \
    --add-data "config.yaml:." \
    src/main.py

echo "Build complete!"
echo "Executable: dist/github-collector"
```

**Step 2: 赋予执行权限并运行**

```bash
chmod +x build.sh
./build.sh
```

**Step 3: 测试可执行文件**

```bash
./dist/github-collector --top-n 1
```

Expected: 可执行文件正常运行

**Step 4: 提交**

```bash
git add build.sh .gitignore
git commit -m "chore: add PyInstaller build script"
```

**Step 5: 创建 .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Logs
logs/
*.log

# Output (optional, include if you want sample data)
# output/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Config (keep template, ignore actual config)
config.yaml
processed.json
```

---

## 完成检查清单

- [ ] 所有 12 个任务完成
- [ ] 所有测试通过
- [ ] 真实数据测试运行成功
- [ ] README 文档完整
- [ ] 配置文件模板正确
- [ ] 可执行文件打包成功
- [ ] 示例输出生成

---

**计划完成。两个执行选项：**

**1. 子代理驱动（当前会话）** - 我为每个任务分配新的子代理，在任务之间进行代码审查，快速迭代

**2. 并行会话（单独会话）** - 在新会话中打开 executing-plans，分批执行并设置检查点

**选择哪种方式？**
