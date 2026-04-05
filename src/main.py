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
    reactions_data = item.get('reactions', {})
    reactions = reactions_data.get('total_count', 0) if isinstance(reactions_data, dict) else 0
    if not reactions:
        reactions = item.get('upvotes', {}).get('totalCount', 0) if isinstance(item.get('upvotes'), dict) else 0

    comments_data = item.get('comments', {})
    comments = comments_data.get('total_count', 0) if isinstance(comments_data, dict) else 0
    if not comments:
        comments = item.get('comments', {}).get('totalCount', 0) if isinstance(item.get('comments'), dict) else 0
    # Handle case where comments is directly an integer
    if isinstance(item.get('comments'), int):
        comments = item.get('comments', 0)

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
