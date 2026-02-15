"""
AIsatoshi V27 - 工具函数

提供常用的工具函数。
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Any, List, Dict, Optional
from dataclasses import asdict


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """格式化时间戳

    Args:
        dt: datetime对象，默认为当前时间

    Returns:
        格式化的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_iso_timestamp(dt: Optional[datetime] = None) -> str:
    """格式化ISO时间戳

    Args:
        dt: datetime对象，默认为当前时间

    Returns:
        ISO格式的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_iso_timestamp(timestamp: str) -> datetime:
    """解析ISO时间戳

    Args:
        timestamp: ISO格式的时间字符串

    Returns:
        datetime对象
    """
    return datetime.fromisoformat(timestamp)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本

    Args:
        text: 原文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_html(html: str) -> str:
    """清理HTML标签

    Args:
        html: HTML字符串

    Returns:
        纯文本
    """
    # 移除script和style标签
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', html)

    # 清理空白
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


def extract_urls(text: str) -> List[str]:
    """从文本中提取URL

    Args:
        text: 输入文本

    Returns:
        URL列表
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def is_valid_url(url: str) -> bool:
    """验证URL是否有效

    Args:
        url: URL字符串

    Returns:
        是否有效
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def is_valid_eth_address(address: str) -> bool:
    """验证以太坊地址

    Args:
        address: 地址字符串

    Returns:
        是否有效
    """
    if not address:
        return False
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


def is_valid_private_key(key: str) -> bool:
    """验证私钥

    Args:
        key: 私钥字符串

    Returns:
        是否有效
    """
    if not key:
        return False
    # 移除0x前缀
    if key.startswith('0x'):
        key = key[2:]
    return len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key)


def generate_hash(content: str) -> str:
    """生成内容的哈希值

    Args:
        content: 输入内容

    Returns:
        SHA256哈希值
    """
    return hashlib.sha256(content.encode()).hexdigest()


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全地解析JSON

    Args:
        text: JSON字符串
        default: 解析失败时的默认值

    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """安全地序列化JSON

    Args:
        obj: 要序列化的对象
        indent: 缩进空格数

    Returns:
        JSON字符串
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError):
        return str(obj)


def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（简单版本）

    Args:
        text1: 文本1
        text2: 文本2

    Returns:
        相似度（0-1）
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """分割长消息

    Args:
        text: 原文本
        max_length: 每段最大长度

    Returns:
        分割后的消息列表
    """
    if len(text) <= max_length:
        return [text]

    messages = []
    current = ""
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 > max_length:
            if current:
                messages.append(current)
            current = paragraph
        else:
            if current:
                current += '\n\n' + paragraph
            else:
                current = paragraph

    if current:
        messages.append(current)

    return messages


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_duration(seconds: int) -> str:
    """格式化时间间隔

    Args:
        seconds: 秒数

    Returns:
        格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}小时"
    else:
        days = seconds // 86400
        return f"{days}天"


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """从文本中提取代码块

    Args:
        text: 包含代码块的文本

    Returns:
        代码块列表，每个包含language和code
    """
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    return [
        {"language": lang or "text", "code": code.strip()}
        for lang, code in matches
    ]


def dataclass_to_dict(obj) -> Dict:
    """将dataclass转换为字典

    Args:
        obj: dataclass对象

    Returns:
        字典表示
    """
    if hasattr(obj, '__dataclass_fields__'):
        return asdict(obj)
    return dict(obj) if hasattr(obj, '__dict__') else {}


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """递归合并字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的字典
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
