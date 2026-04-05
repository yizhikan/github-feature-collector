"""去重管理模块"""
import json
import os
from typing import Set


class DedupManager:
    """
    去重管理器
    使用 JSON 文件存储已处理的 Issue/Discussion ID
    """

    def __init__(self, storage_file: str):
        """
        Args:
            storage_file: 去重数据存储文件路径
        """
        self.storage_file = storage_file
        self.processed_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        """从文件加载已处理的 ID"""
        if not os.path.exists(self.storage_file):
            return set()

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except (json.JSONDecodeError, KeyError):
            return set()

    def _save(self) -> None:
        """保存已处理的 ID 到文件"""
        os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump({'processed_ids': list(self.processed_ids)}, f, indent=2)

    def is_processed(self, item_id: str) -> bool:
        """
        检查是否已处理

        Args:
            item_id: Issue/Discussion ID

        Returns:
            True 如果已处理，False 否则
        """
        return item_id in self.processed_ids

    def mark_processed(self, item_id: str) -> None:
        """
        标记为已处理

        Args:
            item_id: Issue/Discussion ID
        """
        if item_id not in self.processed_ids:
            self.processed_ids.add(item_id)
            self._save()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'total_processed': len(self.processed_ids),
            'storage_file': self.storage_file
        }
