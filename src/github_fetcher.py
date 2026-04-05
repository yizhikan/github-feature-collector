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
        从 OSSinsight API 获取热门仓库

        Args:
            top_n: 获取前 N 个热门仓库

        Returns:
            仓库列表
        """
        logger.info(f"正在获取热门仓库列表 (TOP {top_n})...")

        params = {'period': 'past_week'}
        data = self._request(self.OSSINSIGHT_URL, params)

        if not data or 'data' not in data:
            logger.error("OSSinsight API 调用失败")
            return []

        # OSSinsight returns {columns: [...], rows: [...]} where rows is a list of dicts
        rows = data['data'].get('rows', [])

        # Convert to list of dicts with full_name alias
        repos = []
        for row in rows[:top_n]:
            if isinstance(row, dict):
                row['full_name'] = row.get('repo_name', '')
                repos.append(row)

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
