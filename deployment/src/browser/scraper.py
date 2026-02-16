#!/usr/bin/env python3
"""
AIsatoshi V30.0 - Playwright 浏览器模块
使用 Playwright 实现完整浏览器渲染
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse


class PlaywrightScraper:
    """使用 Playwright 的网页 Scraper"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.browser_type = "playwright"

    async def fetch_async(
        self,
        url: str,
        timeout: int = 30000,
        question: str = ""
    ) -> Dict[str, Any]:
        """异步获取网页内容"""
        try:
            from playwright.async_api import async_playwright

            self.logger.info(f"[Playwright] 正在启动浏览器...")

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page_timeout = int(timeout * 0.8)

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                page.set_default_timeout(page_timeout)

                self.logger.info(f"[Playwright] 正在访问: {url}")

                await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                await asyncio.sleep(2)

                # 获取内容
                content = await page.content()

                try:
                    title = await page.title()
                except:
                    title = ""

                # 获取链接 - 直接用 Playwright 提取
                try:
                    links_elements = await page.query_selector_all('a[href]')
                    links = []
                    for link in links_elements:
                        href = await link.get_attribute('href')
                        if href:
                            links.append(href)
                except:
                    links = []

                await context.close()
                await browser.close()

                # 使用 BeautifulSoup 提取文本
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                for script in soup(['script', 'style']):
                    script.decompose()

                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)

                result = {
                    'success': True,
                    'method': 'playwright',
                    'url': url,
                    'title': title,
                    'content': text[:50000],
                    'full_content': content[:100000],
                    'links': links[:50],  # V30: 保留 Playwright 提取的链接
                    'js_detected': True,
                    'char_count': len(text)
                }

                self.logger.info(f"[Playwright] 获取成功: {len(text)} 字符, {len(links)} 链接")
                return result

        except Exception as e:
            self.logger.error(f"[Playwright] 浏览失败: {e}")
            return {
                'success': False,
                'method': 'playwright',
                'url': url,
                'error': str(e),
                'content': '',
                'links': []
            }

    def fetch(self, url: str, timeout: int = 30000, question: str = "") -> Dict[str, Any]:
        """同步包装器"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        result = loop.run_until_complete(
            self.fetch_async(url, timeout, question)
        )
        return result


def create_scraper(logger: logging.Logger) -> PlaywrightScraper:
    """创建 scraper 实例"""
    return PlaywrightScraper(logger)
