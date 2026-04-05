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
