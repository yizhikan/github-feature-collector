"""tests/test_dedup_manager.py"""
import pytest
import os
from src.dedup_manager import DedupManager


class TestDedupManager:
    """测试去重管理模块"""

    def test_new_manager_empty_storage(self, tmp_path):
        """测试新建管理器（空存储）"""
        storage_file = str(tmp_path / "processed.json")
        manager = DedupManager(storage_file)

        assert manager.is_processed("issue-1") == False
        assert manager.get_stats()['total_processed'] == 0

    def test_mark_and_check(self, tmp_path):
        """测试标记和检查"""
        storage_file = str(tmp_path / "processed.json")
        manager = DedupManager(storage_file)

        manager.mark_processed("issue-1")
        assert manager.is_processed("issue-1") == True
        assert manager.is_processed("issue-2") == False

    def test_persistence(self, tmp_path):
        """测试持久化"""
        storage_file = str(tmp_path / "processed.json")

        # 第一次创建并标记
        manager1 = DedupManager(storage_file)
        manager1.mark_processed("issue-1")

        # 重新加载
        manager2 = DedupManager(storage_file)
        assert manager2.is_processed("issue-1") == True
