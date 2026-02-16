#!/usr/bin/env python3
"""
AIsatoshi V30.0 - Gemini API 模块
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from ..config import config


class GeminiClient:
    """Gemini API 客户端"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self.timeout = config.GEMINI_TIMEOUT
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models"

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ) -> str:
        """生成内容"""
        try:
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }

            self.logger.info(f"[Gemini] 调用 API，prompt 长度: {len(prompt)}")
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {})
                text = content.get("parts", [{}])[0].get("text", "")
                self.logger.info(f"[Gemini] 生成成功，输出长度: {len(text)}")
                return text
            else:
                self.logger.error(f"[Gemini] API 错误: {response.status_code}")
                return f"API 错误: {response.status_code}"

        except requests.Timeout:
            self.logger.error(f"[Gemini] 请求超时")
            return "请求超时"
        except Exception as e:
            self.logger.error(f"[Gemini] 请求失败: {e}")
            return f"请求失败: {str(e)}"

    def analyze_webpage(
        self,
        content: str,
        question: str = "",
        max_length: int = 3000
    ) -> str:
        """分析网页内容"""
        prompt = f"""请分析以下网页内容：

{'问题：' + question if question else '请总结这个网页的主要内容'}

网页内容（前 {max_length} 字符）：
{content[:max_length]}

请基于网页内容回答问题，用中文回复。"""

        return self.generate_content(prompt, temperature=0.7, max_tokens=2048)

    def chat(
        self,
        message: str,
        context: str = "",
        history: List[Dict] = None
    ) -> Dict[str, Any]:
        """对话 - 理解用户意图"""
        from .prompts import INTENT_PROMPT

        # 构建上下文
        full_context = context
        if history:
            recent = history[-10:]  # 最近 10 条
            if recent:
                full_context += "\n【最近对话】\n"
                for msg in recent:
                    role = "用户" if msg.get('role') == 'user' else "AIsatoshi"
                    content = msg.get('content', '')[:200]
                    full_context += f"{role}: {content}\n"

        # 构建完整 prompt
        full_prompt = f"""{INTENT_PROMPT}

{full_context}

【当前对话】
用户说：{message}

分析用户意图，返回 JSON 格式："""

        response = self.generate_content(full_prompt, temperature=0.8, max_tokens=4096)

        # 解析 JSON
        return self._parse_intent(response)

    def _parse_intent(self, response: str) -> Dict[str, Any]:
        """解析 AI 返回的意图"""
        import json
        import re

        try:
            # 提取 JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'action': result.get('action', 'chat'),
                    'params': result.get('params', {}),
                    'response': result.get('response', ''),
                    'raw_response': response
                }

            # 没找到 JSON，返回 chat
            return {
                'action': 'chat',
                'params': {},
                'response': response[:1000],
                'raw_response': response
            }

        except Exception as e:
            self.logger.error(f"[Gemini] 解析意图失败: {e}")
            return {
                'action': 'chat',
                'params': {},
                'response': response[:500] if response else '无法理解',
                'raw_response': response
            }


def create_gemini_client(logger: logging.Logger) -> GeminiClient:
    """创建 Gemini 客户端"""
    return GeminiClient(logger)
