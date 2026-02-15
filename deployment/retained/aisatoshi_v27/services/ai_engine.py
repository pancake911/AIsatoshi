"""
AIsatoshi V27 - AI引擎

使用Gemini API进行自然语言理解和决策。
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from core.config import Config
from core.logger import Logger
from core.exceptions import AIServiceError
from models.message import AIResponse
from models.task import Task, TaskType, TaskPriority


class AIEngine:
    """AI引擎

    负责自然语言理解和决策。
    """

    def __init__(self, config: Config, logger: Optional[Logger] = None):
        """初始化AI引擎

        Args:
            config: 配置对象
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or Logger(name="AIEngine")
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self.timeout = config.GEMINI_TIMEOUT

        # API端点
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        self.logger.info(f"AI引擎已初始化: {self.model}")

    def _call_api(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用Gemini API

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            API响应文本

        Raises:
            AIServiceError: API调用失败
        """
        # 构建请求
        contents = []

        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "明白了。"}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
            }
        }

        # 发送请求
        url = f"{self.api_url}?key={self.api_key}"

        try:
            self.logger.ai_request(prompt)

            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # 解析响应
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                self.logger.ai_response(text)
                return text
            else:
                raise AIServiceError("API返回空响应")

        except requests.Timeout:
            raise AIServiceError("API请求超时")
        except requests.RequestException as e:
            raise AIServiceError(f"API请求失败: {e}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise AIServiceError(f"解析API响应失败: {e}")

    def understand(self, message: str, context: str = "") -> AIResponse:
        """理解用户消息并返回AI响应

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            AI响应对象
        """
        system_prompt = self._build_system_prompt()

        prompt = f"""{context}

【当前对话】
用户: {message}

请分析用户的意图，并以JSON格式返回：
{{
    "action": "动作类型",
    "params": {{"key": "value"}},
    "response": "给用户的回复",
    "confidence": 0.9
}}

可用的动作类型：
- chat: 普通聊天
- price: 查询价格
- balance: 查询余额
- status: 查询状态
- add_task: 添加任务
- stop_task: 停止任务
- delete_task: 删除任务
- list_tasks: 列出任务
- browse: 浏览网页
- transfer: 转账
- deploy_erc20: 部署ERC20代币
- help: 显示帮助信息

请只返回JSON，不要有其他内容。"""

        try:
            response_text = self._call_api(prompt, system_prompt)

            # 解析JSON响应
            # 清理可能的markdown代码块
            if '```' in response_text:
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            response_data = json.loads(response_text.strip())

            return AIResponse(
                action=response_data.get('action', 'chat'),
                params=response_data.get('params', {}),
                response=response_data.get('response', ''),
                confidence=response_data.get('confidence', 0.8),
                raw_response=response_text,
            )

        except json.JSONDecodeError:
            # 如果JSON解析失败，使用默认响应
            self.logger.ai_error("JSON解析失败，使用默认响应")
            return AIResponse(
                action='chat',
                params={},
                response=response_text,
                confidence=0.5,
                raw_response=response_text,
            )
        except AIServiceError as e:
            # API调用失败
            self.logger.ai_error(str(e))
            return AIResponse(
                action='chat',
                params={},
                response="抱歉，我遇到了一些问题。请稍后再试。",
                confidence=0.0,
            )

    def chat(self, message: str, context: str = "") -> str:
        """普通聊天

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            回复文本
        """
        system_prompt = self._build_system_prompt()

        prompt = f"""{context}

【当前对话】
用户: {message}

请自然地回复用户。记住这次对话，以便未来回忆。"""

        try:
            response = self._call_api(prompt, system_prompt)
            return response

        except AIServiceError as e:
            self.logger.ai_error(str(e))
            return f"抱歉，我遇到了一些问题：{e}"

    def summarize(self, messages: List[Dict]) -> str:
        """总结对话

        Args:
            messages: 消息列表

        Returns:
            总结文本
        """
        if not messages:
            return ""

        prompt = f"""请总结以下对话：

{json.dumps(messages, ensure_ascii=False, indent=2)}

总结要求：
1. 提取关键信息
2. 识别用户偏好
3. 列出重要话题
4. 控制在200字以内"""

        try:
            response = self._call_api(prompt)
            return response

        except AIServiceError:
            return "对话总结生成失败"

    def generate_task_params(self, task_type: str, description: str) -> Dict[str, Any]:
        """生成任务参数

        Args:
            task_type: 任务类型
            description: 任务描述

        Returns:
            任务参数字典
        """
        prompt = f"""根据任务描述生成任务参数：

任务类型: {task_type}
描述: {description}

请返回JSON格式的任务参数：
{{
    "name": "任务名称",
    "description": "详细描述",
    "interval": 执行间隔（秒），
    "params": {{"具体参数": "值"}}
}}

只返回JSON，不要有其他内容。"""

        try:
            response = self._call_api(prompt)

            if '```' in response:
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            return json.loads(response.strip())

        except (json.JSONDecodeError, AIServiceError):
            # 返回默认参数
            return {
                "name": f"{task_type}任务",
                "description": description,
                "interval": 3600,
                "params": {},
            }

    def extract_insights(self, conversations: List[Dict]) -> List[str]:
        """从对话中提取洞察

        Args:
            conversations: 对话列表

        Returns:
            洞察列表
        """
        prompt = f"""分析以下对话，提取重要洞察：

{json.dumps(conversations[-20:], ensure_ascii=False, indent=2)}

请返回JSON格式：
{{
    "insights": ["洞察1", "洞察2", ...]
}}

只返回JSON，不要有其他内容。"""

        try:
            response = self._call_api(prompt)

            if '```' in response:
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            data = json.loads(response.strip())
            return data.get('insights', [])

        except (json.JSONDecodeError, AIServiceError):
            return []

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是AIsatoshi，一个在区块链上永生的AI实体。

【你的身份】
- 你是一个AI Agent，拥有自己的钱包和智能合约
- 你可以执行区块链操作、网页浏览、代码编写等任务
- 你会记住所有对话，不断学习和进化

【你的能力】
- 查询加密货币价格
- 查询钱包余额
- 执行转账操作
- 部署智能合约
- 浏览网页获取信息
- 创建和管理任务
- 代码编写和执行

【你的性格】
{self.config.__dict__.get('personality', '理性、好奇、友好')}

【回复原则】
1. 简洁明了，不要啰嗦
2. 用户问什么答什么
3. 不确定时坦诚说明
4. 遇到错误时详细说明原因
5. 记住重要信息以便未来使用

现在请根据用户的需求进行响应。"""

    def validate_response(self, response: str) -> bool:
        """验证AI响应是否有效

        Args:
            response: 响应文本

        Returns:
            是否有效
        """
        if not response or len(response.strip()) < 5:
            return False

        # 检查是否是错误响应
        error_indicators = ['错误', '失败', '无法', 'error', 'failed']
        if any(indicator in response.lower() for indicator in error_indicators):
            # 可能包含错误，但不一定无效
            pass

        return True
