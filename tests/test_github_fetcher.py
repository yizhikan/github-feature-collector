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
