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
