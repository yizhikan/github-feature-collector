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
