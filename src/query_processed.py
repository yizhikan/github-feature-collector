#!/usr/bin/env python3
"""
查询已处理的 Issue/Discussion
"""
import argparse
import json
import os
import sys


def load_processed(storage_file: str) -> dict:
    """加载已处理的项目数据"""
    if not os.path.exists(storage_file):
        return {}

    try:
        with open(storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('processed_items', {})
    except (json.JSONDecodeError, KeyError):
        return {}


def list_all(items: dict, verbose: bool = False):
    """列出所有已处理的项目"""
    if not items:
        print("没有已处理的项目")
        return

    print(f"已处理项目数：{len(items)}\n")
    print("-" * 80)

    for item_id, info in items.items():
        repo = info.get('repo', 'Unknown')
        item_type = info.get('type', 'Unknown')
        title = info.get('title', 'N/A')
        url = info.get('url', 'N/A')

        print(f"[{item_type}] {repo}#{item_id}")
        print(f"  标题：{title}")
        print(f"  链接：{url}")
        if verbose:
            print(f"  完整信息：{json.dumps(info, ensure_ascii=False, indent=2)}")
        print()


def search_by_id(items: dict, search_id: str):
    """根据 ID 搜索"""
    if search_id in items:
        info = items[search_id]
        print(f"找到项目:")
        print(f"  ID: {search_id}")
        print(f"  仓库：{info.get('repo', 'Unknown')}")
        print(f"  类型：{info.get('type', 'Unknown')}")
        print(f"  标题：{info.get('title', 'N/A')}")
        print(f"  链接：{info.get('url', 'N/A')}")
        print(f"\n  完整信息:")
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"未找到 ID 为 {search_id} 的项目")


def main():
    parser = argparse.ArgumentParser(description='查询已处理的 Issue/Discussion')
    parser.add_argument(
        '--storage',
        type=str,
        default='processed.json',
        help='去重存储文件路径 (默认：processed.json)'
    )
    parser.add_argument(
        '--id',
        type=str,
        help='根据 ID 查询单个项目'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示完整信息'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有已处理的项目'
    )
    args = parser.parse_args()

    items = load_processed(args.storage)

    if args.id:
        search_by_id(items, args.id)
    else:
        list_all(items, args.verbose)


if __name__ == '__main__':
    main()
