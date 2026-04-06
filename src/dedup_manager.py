"""去重管理模块"""
import json
import os
from typing import Dict, List, Optional


class DedupManager:
    """
    去重管理器
    使用 JSON 文件存储已处理的 Issue/Discussion 完整信息
    """

    def __init__(self, storage_file: str):
        """
        Args:
            storage_file: 去重数据存储文件路径
        """
        self.storage_file = storage_file
        self.processed_items: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        """从文件加载已处理的项目信息"""
        if not os.path.exists(self.storage_file):
            return {}

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 支持旧格式迁移
                if 'processed_ids' in data and isinstance(data['processed_ids'], list):
                    # 旧格式只有 ID 列表，转换为新格式
                    return {item_id: {} for item_id in data['processed_ids']}
                return data.get('processed_items', {})
        except (json.JSONDecodeError, KeyError):
            return {}

    def _save(self) -> None:
        """保存已处理的项目信息到文件"""
        os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processed_items': {
                    item_id: item_data
                    for item_id, item_data in self.processed_items.items()
                }
            }, f, indent=2, ensure_ascii=False)

    def is_processed(self, item_id: str) -> bool:
        """
        检查是否已处理

        Args:
            item_id: Issue/Discussion ID

        Returns:
            True 如果已处理，False 否则
        """
        return item_id in self.processed_items

    def mark_processed(
        self,
        item_id: str,
        repo: str = '',
        item_type: str = '',
        url: str = '',
        title: str = '',
        **kwargs
    ) -> None:
        """
        标记为已处理

        Args:
            item_id: Issue/Discussion ID
            repo: 仓库全名 (owner/repo)
            item_type: 类型 (Issue/Discussion)
            url: GitHub URL
            title: 标题
        """
        if item_id not in self.processed_items:
            self.processed_items[item_id] = {
                'id': item_id,
                'repo': repo,
                'type': item_type,
                'url': url,
                'title': title,
                **kwargs
            }
            self._save()

    def get_item(self, item_id: str) -> Optional[dict]:
        """
        获取单个项目信息

        Args:
            item_id: Issue/Discussion ID

        Returns:
            项目信息字典，不存在返回 None
        """
        return self.processed_items.get(item_id)

    def get_all_items(self) -> List[dict]:
        """获取所有已处理的项目列表"""
        return list(self.processed_items.values())

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'total_processed': len(self.processed_items),
            'storage_file': self.storage_file
        }
