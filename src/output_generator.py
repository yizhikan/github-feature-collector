"""输出生成模块"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any


class OutputGenerator:
    """需求清单输出生成器"""

    def __init__(self, config: dict):
        """
        Args:
            config: 输出配置字典
        """
        self.base_dir = config.get('base_dir', 'output')
        self.formats = config.get('format', ['markdown', 'json'])

    def generate(
        self,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict
    ) -> Dict[str, str]:
        """
        生成输出文件

        Args:
            repo: 仓库名称 (owner/repo)
            requirements: 需求列表
            config_summary: 配置摘要

        Returns:
            生成的文件路径字典
        """
        owner, repo_name = repo.split('/') if '/' in repo else ('unknown', repo)
        output_dir = os.path.join(self.base_dir, f"{owner}-{repo_name}")
        os.makedirs(output_dir, exist_ok=True)

        generated_files = {}

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'markdown' in self.formats:
            md_path = os.path.join(output_dir, 'requirements.md')
            self._generate_markdown(md_path, repo, requirements, config_summary, timestamp)
            generated_files['markdown'] = md_path

        if 'json' in self.formats:
            json_path = os.path.join(output_dir, 'requirements.json')
            self._generate_json(json_path, repo, requirements, config_summary, timestamp)
            generated_files['json'] = json_path

        return generated_files

    def _generate_markdown(
        self,
        path: str,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict,
        timestamp: str
    ) -> None:
        """生成 Markdown 文件"""
        content = f"""# GitHub 热门仓库新功能需求清单

**仓库**: {repo}
**采集时间**: {timestamp}
**筛选条件**: {config_summary.get('issue_state', 'open')} issues, {config_summary.get('sort_by', 'created')} {config_summary.get('sort_direction', 'desc')}

---
"""

        for i, req in enumerate(requirements, 1):
            priority_score = req.get('priority_score', 5)
            if priority_score >= 9:
                label = '很高'
            elif priority_score >= 7:
                label = '高'
            elif priority_score >= 4:
                label = '中'
            else:
                label = '低'

            content += f"""
## 需求 #{i}: {req.get('title', 'Untitled')}

**来源**: {req.get('source_type', 'Issue')} #{req.get('number', '')}
**链接**: {req.get('url', '')}
**创建时间**: {req.get('created_at', 'Unknown')}
**互动**: 👍 {req.get('reactions', 0)}, 💬 {req.get('comments', 0)}

**原始摘要**:
{req.get('original_summary', '无')}

**大模型判断理由**:
{req.get('reason', '无')}

**需求价值**:
{req.get('value', '无')}

**优先级**: {priority_score}/10 ({label})

---
"""

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_json(
        self,
        path: str,
        repo: str,
        requirements: List[Dict[str, Any]],
        config_summary: dict,
        timestamp: str
    ) -> None:
        """生成 JSON 文件"""
        data = {
            'repo': repo,
            'collected_at': timestamp,
            'filter_config': config_summary,
            'requirements': requirements
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
