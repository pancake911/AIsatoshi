#!/usr/bin/env python3
"""
Browser Scraper Module - V28 Fixed
使用 Playwright 实现完整浏览器渲染，支持动态网站
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class ScraperWithBrowser:
    """使用 Playwright 的浏览器 Scraper"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.browser_type = "playwright"

    async def fetch_url_async(self, url: str, timeout: int = 15000, question: str = "") -> Dict[str, Any]:
        """异步获取网页内容（使用 Playwright）"""
        try:
            from playwright.async_api import async_playwright

            self.logger.info(f"[Playwright] 正在启动浏览器...")

            async with async_playwright() as p:
                # 增加默认超时到 15 秒（用户要求）
                # 网站超时 = timeout / 1000 毫秒
                self.logger.info(f"[Playwright] 超时设置: {timeout/1000} 秒")

                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                # 延长页面加载超时到超时的 80%
                page_timeout = int(timeout * 0.8)

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # 设置超时
                page.set_default_timeout(page_timeout)

                self.logger.info(f"[Playwright] 正在访问: {url}")

                # 访问页面
                await page.goto(url, wait_until='networkidle', timeout=timeout)

                # 等待页面完全加载（额外时间）
                await page.wait_for_load_state('networkidle', timeout=timeout)
                await asyncio.sleep(2)  # 额外等待 2 秒

                # 获取页面内容
                content = await page.content()

                # 尝试提取标题
                try:
                    title = await page.title()
                except:
                    title = ""

                # 尝试提取链接
                try:
                    links = await page.query_selector_all('a[href]')
                    hrefs = [await link.get_attribute('href') for link in links]
                except:
                    hrefs = []

                # 关闭浏览器
                await context.close()
                await browser.close()

                # 使用 BeautifulSoup 解析 HTML
                soup = BeautifulSoup(content, 'html.parser')

                # 移除脚本和样式
                for script in soup(['script', 'style']):
                    script.decompose()

                # 获取文本
                text = soup.get_text()

                # 清理文本
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)

                result = {
                    'success': True,
                    'method': 'playwright',
                    'url': url,
                    'title': title,
                    'content': text[:50000],  # 限制返回长度
                    'full_content': content[:100000],  # 保留更多内容用于分析
                    'links': hrefs[:50],  # 最多返回 50 个链接
                    'js_detected': True,
                    'char_count': len(text)
                }

                self.logger.info(f"[Playwright] 获取成功: {len(text)} 字符, {len(hrefs)} 链接")

                return result

        except (ImportError, Exception) as e:
            self.logger.error(f"[Playwright] 浏览失败: {e}")
            return {
                'success': False,
                'method': 'playwright',
                'url': url,
                'error': str(e),
                'content': '',
                'links': []
            }

    def fetch_url(self, url: str, timeout: int = 15000, question: str = "") -> Dict[str, Any]:
        """同步包装器 - 使用 asyncio 运行异步函数"""
        try:
            import asyncio

            # 获取当前事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

            result = loop.run_until_complete(
                self.fetch_url_async(url, timeout, question)
            )

            return result

        except Exception as e:
            self.logger.error(f"[Browser] 同步调用失败: {e}")
            return {
                'success': False,
                'method': 'sync_wrapper',
                'url': url,
                'error': str(e),
                'content': '',
                'links': []
            }


if __name__ == '__main__':
    # 测试代码
    import sys
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async def test():
        scraper = ScraperWithBrowser(logger)

        # 测试简单页面
        result1 = await scraper.fetch_url_async('https://example.com', 15000)
        print(f"Example.com: {len(result1.get('content', ''))} 字符")

        # 测试动态页面
        result2 = await scraper.fetch_url_async('https://bankr.bot/', 30000)  # 30 秒
        print(f"bankr.bot: {len(result2.get('content', ''))} 字符")

    asyncio.run(test())
