"""
AIsatoshi V27 - 消息模型

定义Telegram消息相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MessageEntity:
    """Telegram消息实体

    表示消息中的特殊实体，如URL、命令等。
    """
    type: str  # 'url', 'link', 'command', etc.
    offset: int
    length: int
    url: Optional[str] = None  # 对于link类型，包含实际URL


@dataclass
class TelegramMessage:
    """Telegram消息

    表示从Telegram接收或发送的消息。
    """
    chat_id: str
    message_id: int
    text: str
    from_user: str
    is_command: bool = False
    entities: List[MessageEntity] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """后处理：确保entities是列表"""
        if self.entities is None:
            self.entities = []

    @property
    def is_url(self) -> bool:
        """检查消息是否包含URL"""
        return any(entity.type in ('url', 'link') for entity in self.entities)

    @property
    def extracted_urls(self) -> List[str]:
        """提取消息中的所有URL"""
        urls = []
        for entity in self.entities:
            if entity.type == 'link' and entity.url:
                urls.append(entity.url)
            elif entity.type == 'url':
                # 从text中提取
                start = entity.offset
                end = start + entity.length
                if start <= len(self.text):
                    urls.append(self.text[start:end])
        return urls

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'text': self.text,
            'from_user': self.from_user,
            'is_command': self.is_command,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramMessage':
        """从字典创建"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=data['text'],
            from_user=data['from_user'],
            is_command=data.get('is_command', False),
            timestamp=timestamp,
            metadata=data.get('metadata', {}),
        )


@dataclass
class AIResponse:
    """AI响应

    表示AI的响应结果。
    """
    action: str  # 动作类型
    params: Dict[str, Any]  # 动作参数
    response: str  # 给用户的回复
    confidence: float = 1.0  # 置信度
    raw_response: str = ""  # 原始响应

    def is_valid(self) -> bool:
        """检查响应是否有效"""
        return bool(self.action)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'action': self.action,
            'params': self.params,
            'response': self.response,
            'confidence': self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIResponse':
        """从字典创建"""
        return cls(
            action=data.get('action', ''),
            params=data.get('params', {}),
            response=data.get('response', ''),
            confidence=data.get('confidence', 1.0),
        )
