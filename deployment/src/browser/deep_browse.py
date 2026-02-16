#!/usr/bin/env python3
"""
AIsatoshi V30.0 - 深度浏览模块
修复了 V29 的链接提取 bug
"""

import logging
import time
import re
from typing import Dict, Any, List, Optional, Callable
from urllib.parse import urljoin, urlparse

from .scraper import create_scraper


class DeepBrowser:
    """深度浏览器 - 访问主页和相关子页面"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.scraper = create_scraper(logger)

    def browse(
        self,
        url: str,
        question: str = "",
        max_pages: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """深度浏览网页"""
        try:
            self.logger.info(f"[DeepBrowse] 开始深度浏览: {url}")

            # 获取主页
            main_result = self.scraper.fetch(url, timeout=30000)

            if not main_result.get('success'):
                return {
                    'success': False,
                    'error': main_result.get('error', '无法访问主页'),
                    'pages_visited': 0
                }

            all_pages = []
            all_content = ""
            visited_urls = set()

            # 保存主页
            visited_urls.add(url)
            all_pages.append({
                'url': url,
                'title': main_result.get('title', '主页'),
                'content': main_result.get('content', ''),
                'is_main': True
            })
            all_content += f"\n\n=== 主页 ===\n{main_result.get('content', '')}"

            # V30 修复: 直接使用 Playwright 提取的 links
            links = main_result.get('links', [])
            self.logger.info(f"[DeepBrowse] Playwright 提取到 {len(links)} 个链接")

            # 过滤和排序链接
            filtered_links = self._filter_links(url, links, visited_urls)
            self.logger.info(f"[DeepBrowse] 过滤后 {len(filtered_links)} 个链接")

            # 访问子页面
            max_sub_pages = min(len(filtered_links), max_pages)
            for i, sub_url in enumerate(filtered_links[:max_sub_pages]):
                if progress_callback:
                    progress_callback(i + 1, max_sub_pages)

                self.logger.info(f"[DeepBrowse] 访问子页 ({i+1}/{max_sub_pages}): {sub_url}")

                sub_result = self.scraper.fetch(sub_url, timeout=15000)
                if sub_result.get('success'):
                    visited_urls.add(sub_url)
                    all_pages.append({
                        'url': sub_url,
                        'title': sub_result.get('title', sub_url),
                        'content': sub_result.get('content', ''),
                        'is_main': False
                    })
                    all_content += f"\n\n=== 子页: {sub_result.get('title', sub_url)} ===\n{sub_result.get('content', '')}"

                time.sleep(1)

            self.logger.info(f"[DeepBrowse] 浏览完成，共访问 {len(all_pages)} 个页面")

            return {
                'success': True,
                'pages': all_pages,
                'all_content': all_content,
                'pages_visited': len(all_pages),
                'total_chars': len(all_content)
            }

        except Exception as e:
            self.logger.error(f"[DeepBrowse] 深度浏览失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'pages_visited': 0
            }

    def _filter_links(self, base_url: str, links: List[str], visited: set) -> List[str]:
        """过滤和排序链接"""
        if not links:
            return []

        base_domain = urlparse(base_url).netloc.lower()
        if base_domain.startswith('www.'):
            base_domain = base_domain[4:]

        # 排除模式
        exclude_patterns = [
            '/logout', '/signout', '/login', '/register', '/signin',
            'twitter.com', 'telegram.org', 'discord.com', 'github.com'
        ]

        filtered = []
        for link in links:
            try:
                # 转为绝对 URL
                absolute = urljoin(base_url, link)

                # 只保留 http/https
                if not absolute.startswith(('http://', 'https://')):
                    continue

                # 移除 fragment
                absolute = absolute.split('#')[0]

                parsed = urlparse(absolute)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]

                # 只保留同域名
                if domain != base_domain:
                    continue

                # 排除特定模式
                if any(pattern in absolute.lower() for pattern in exclude_patterns):
                    continue

                # 去重
                if absolute in visited:
                    continue

                filtered.append(absolute)

            except Exception:
                continue

        # 优先级排序
        high_priority = [
            'about', 'docs', 'api', 'features', 'how-it-works',
            'guide', 'tutorial', 'introduction', 'overview', 'whitepaper',
            'tokenomics', 'faq', 'help', 'learn', 'blog', 'news'
        ]

        scored = []
        for link in filtered:
            score = 0
            link_lower = link.lower()

            # 检查高优先级关键词
            for kw in high_priority:
                if f'/{kw}' in link_lower or f'/{kw}?' in link_lower:
                    score += 10
                    break

            # 路径深度惩罚
            score -= link.count('/')

            scored.append((score, link))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [link for _, link in scored]


def create_deep_browser(logger: logging.Logger) -> DeepBrowser:
    """创建深度浏览器实例"""
    return DeepBrowser(logger)
