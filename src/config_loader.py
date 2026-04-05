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
