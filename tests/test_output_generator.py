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
