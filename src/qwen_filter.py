"""通义千问大模型过滤模块"""
import json
import time
import requests
from typing import Dict, Any, Optional
from src.logger import setup_logger

logger = setup_logger({'level': 'DEBUG', 'file': 'logs/app.log'})


SYSTEM_PROMPT = """你是一个技术需求分析师。请分析以下 GitHub Issue/Discussion 内容，判断是否属于"新功能需求"。

【收录标准】
✅ 全新功能、新增模块、架构级重构、跨平台支持、插件体系、API 扩展、重大新能力

【排除标准】
❌ Bug 修复、文案/样式/UI 小改、文档更新、参数调整、现有功能小优化、体验微调

【输出格式】(严格 JSON)
{
  "included": true/false,
  "summary": "需求摘要 (50 字内)",
  "reason": "判断理由",
  "value": "需求价值与实现意义",
  "priority_score": 1-10
}"""


class QwenFilter:
    """通义千问大模型过滤器"""

    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def __init__(self, config: dict):
        """
        Args:
            config: Qwen 配置字典
        """
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'qwen-plus')
        self.request_interval = config.get('request_interval', 0.5)

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    def filter_content(
        self,
        title: str,
        body: str,
        url: str,
        reactions: int = 0,
        comments: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        调用 Qwen API 进行内容过滤

        Args:
            title: 标题
            body: 正文
            url: 链接
            reactions: 互动数（点赞等）
            comments: 评论数

        Returns:
            大模型返回的结构化结果，失败返回 None
        """
        user_prompt = f"""【输入内容】
标题：{title[:500]}
正文：{body[:2000] if body else '无'}
链接：{url}
互动数据：👍 {reactions}, 💬 {comments}"""

        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt}
        ]

        payload = {
            'model': self.model,
            'input': {'messages': messages},
            'parameters': {
                'result_format': 'message',
                'temperature': 0.1
            }
        }

        try:
            time.sleep(self.request_interval)
            response = self.session.post(self.API_URL, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            content = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')

            return self._parse_response(content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API 调用失败：{e}")
            return None
        except Exception as e:
            logger.error(f"解析 Qwen 响应失败：{e}")
            return None

    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析大模型返回的 JSON

        Args:
            content: 大模型返回的内容

        Returns:
            解析后的字典，失败返回 None
        """
        try:
            # 尝试提取 JSON（处理可能的 markdown 包裹）
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            return None
