#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 记忆存储模块
"""

import logging
import pickle
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..config import config


class MemoryStorage:
    """记忆存储"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.data_dir = config.DATA_DIR
        self.memory_file = os.path.join(self.data_dir, "memory.pkl")

        # 记忆数据
        self.conversations: Dict[str, List[Dict]] = {}
        self.metadata: Dict[str, Any] = {}

        # 加载记忆
        self._load()

    def _load(self):
        """加载记忆"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)

            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'rb') as f:
                    data = pickle.load(f)
                    self.conversations = data.get('conversations', {})
                    self.metadata = data.get('metadata', {})
                    self.logger.info(f"[Memory] 加载了 {len(self.conversations)} 个对话的记忆")

        except Exception as e:
            self.logger.error(f"[Memory] 加载失败: {e}")

    def save(self):
        """保存记忆"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)

            data = {
                'conversations': self.conversations,
                'metadata': self.metadata,
                'updated_at': datetime.now().isoformat()
            }

            with open(self.memory_file, 'wb') as f:
                pickle.dump(data, f)

            self.logger.debug(f"[Memory] 记忆已保存")

        except Exception as e:
            self.logger.error(f"[Memory] 保存失败: {e}")

    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        action: str = "",
        metadata: Dict = None
    ):
        """添加消息"""
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []

        self.conversations[chat_id].append({
            'role': role,
            'content': content,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })

        # 限制每个对话的长度
        if len(self.conversations[chat_id]) > 100:
            self.conversations[chat_id] = self.conversations[chat_id][-100:]

        # 定期保存
        if len(self.conversations[chat_id]) % 10 == 0:
            self.save()

    def get_history(
        self,
        chat_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取历史"""
        history = self.conversations.get(chat_id, [])
        return history[-limit:]

    def search(
        self,
        query: str,
        chat_id: str = None,
        limit: int = 5
    ) -> List[Dict]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        # 搜索范围
        conversations = (
            {chat_id: self.conversations.get(chat_id, [])}
            if chat_id
            else self.conversations
        )

        for cid, messages in conversations.items():
            for msg in messages:
                content = msg.get('content', '')
                if query_lower in content.lower():
                    results.append(msg)
                    if len(results) >= limit:
                        return results

        return results

    def get_metadata(self, key: str, default=None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.metadata[key] = value


def create_memory_storage(logger: logging.Logger) -> MemoryStorage:
    """创建记忆存储"""
    return MemoryStorage(logger)
