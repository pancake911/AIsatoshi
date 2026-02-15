"""
AIsatoshi V27 - 网页浏览服务

支持：
1. API优先获取数据（CoinGecko等）
2. HTML解析
3. 子页面深度浏览
"""

import re
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from core.logger import Logger
from core.exceptions import WebScrapingError


class WebScraper:
    """网页浏览服务

    支持多种浏览方式：
    - API优先（快速）
    - HTML解析（通用）
    - 深度浏览（访问子页面）
    """

    def __init__(self, logger: Optional[Logger] = None):
        """初始化网页浏览服务

        Args:
            logger: 日志记录器
        """
        self.logger = logger or Logger(name="WebScraper")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 已访问的URL（避免重复）
        self.visited_urls = set()

        # API配置
        self.apis = {
            'coingecko': {
                'base_url': 'https://api.coingecko.com/api/v3',
                'endpoints': {
                    'price': '/simple/price',
                    'market_cap': '/global',
                }
            }
        }

        self.logger.info("网页浏览服务已初始化")

    # === API优先方法 ===

    def get_crypto_price(self, coin_id: str) -> Dict[str, Any]:
        """获取加密货币价格（API优先）

        Args:
            coin_id: 代币ID（如bitcoin, ethereum）

        Returns:
            价格信息
        """
        try:
            url = f"{self.apis['coingecko']['base_url']}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd,cny',
                'include_market_cap': 'true',
                'include_24hr_change': 'true'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if coin_id in data:
                return data[coin_id]
            else:
                return {}

        except Exception as e:
            self.logger.error(f"获取价格失败: {e}")
            return {}

    def get_global_market_data(self) -> Dict[str, Any]:
        """获取全球市场数据

        Returns:
            市场数据
        """
        try:
            url = f"{self.apis['coingecko']['base_url']}/global"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get('data', {})

        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return {}

    # === HTML解析方法 ===

    def browse(self, url: str, depth: int = 1) -> Dict[str, Any]:
        """浏览网页（支持子页面）

        Args:
            url: 目标URL
            depth: 深度（0=仅主页，1=主页+一级链接）

        Returns:
            浏览结果
        """
        self.logger.info(f"浏览网页: {url}, 深度: {depth}")

        result = {
            'url': url,
            'title': '',
            'content': '',
            'links': [],
            'sub_pages': [],
            'error': None
        }

        try:
            # 获取主页面
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            result['title'] = self._extract_title(soup)

            # 提取主要内容
            result['content'] = self._extract_content(soup)

            # 提取链接
            links = self._extract_links(url, soup)
            result['links'] = links[:20]  # 限制链接数量

            # 深度浏览：访问相关子页面
            if depth > 0 and links:
                sub_pages = self._browse_sub_pages(links[:3], depth-1)  # 最多3个子页面
                result['sub_pages'] = sub_pages

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"浏览失败: {e}")

        return result

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        # 优先级：h1 > title > meta og:title
        if soup.h1:
            return soup.h1.get_text(strip=True)
        if soup.title:
            return soup.title.get_text(strip=True)
        meta_og_title = soup.find('meta', property='og:title')
        if meta_og_title:
            return meta_og_title.get('content', '')
        return "无标题"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取页面主要内容"""
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 尝试找到主要内容区域
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
            soup.body
        )

        if main_content:
            # 提取文本，保留段落结构
            paragraphs = []
            for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # 忽略太短的内容
                    paragraphs.append(text)

            return '\n\n'.join(paragraphs[:30])  # 最多30段

        return soup.get_text(separator='\n', strip=True)[:2000]

    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> List[Dict]:
        """提取页面链接"""
        links = []
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)[:50]

            # 转换为绝对URL
            absolute_url = urljoin(base_url, href)

            # 只保留同域名的链接（避免爬取外部网站）
            if urlparse(absolute_url).netloc == base_domain:
                links.append({
                    'url': absolute_url,
                    'text': text
                })

        return links

    def _browse_sub_pages(self, links: List[Dict], depth: int) -> List[Dict]:
        """浏览子页面"""
        sub_pages = []

        for link in links:
            if depth <= 0:
                break

            url = link['url']

            # 避免重复访问
            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            # 访问子页面
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                sub_pages.append({
                    'url': url,
                    'title': self._extract_title(soup),
                    'content': self._extract_content(soup)[:500],  # 子页面只取摘要
                })

                time.sleep(1)  # 避免请求过快

            except Exception as e:
                self.logger.debug(f"子页面浏览失败 {url}: {e}")

        return sub_pages

    # === 智能浏览 ===

    def smart_browse(self, url: str, question: str = "") -> str:
        """智能浏览：根据URL类型选择最佳方式

        Args:
            url: 目标URL
            question: 用户问题（用于聚焦内容）

        Returns:
            格式化的浏览结果
        """
        self.logger.info(f"智能浏览: {url}")

        # 检测URL类型
        url_type = self._detect_url_type(url)

        if url_type == 'coingecko_price':
            # CoinGecko价格页面
            coin_id = self._extract_coin_id(url)
            if coin_id:
                price_data = self.get_crypto_price(coin_id)
                return self._format_price_data(coin_id, price_data)

        elif url_type == 'coingecko':
            # CoinGecko其他页面
            return self._browse_coingecko(url)

        # 通用浏览
        result = self.browse(url, depth=1)

        return self._format_browse_result(result, question)

    def _detect_url_type(self, url: str) -> str:
        """检测URL类型"""
        if 'coingecko.com' in url:
            if '/price/' in url or '/en/coins/' in url:
                return 'coingecko_price'
            return 'coingecko'
        return 'general'

    def _extract_coin_id(self, url: str) -> Optional[str]:
        """从CoinGecko URL提取代币ID"""
        # 例如：https://www.coingecko.com/en/coins/bitcoin
        match = re.search(r'/en/coins/([^/]+)', url)
        if match:
            return match.group(1)
        return None

    def _browse_coingecko(self, url: str) -> str:
        """浏览CoinGecko页面"""
        result = self.browse(url, depth=0)
        return self._format_browse_result(result)

    def _format_price_data(self, coin_id: str, data: Dict) -> str:
        """格式化价格数据"""
        if not data:
            return f"❌ 无法获取 {coin_id} 的价格数据"

        lines = [f"💰 {coin_id.upper()} 价格信息"]

        if 'usd' in data:
            lines.append(f"\n💵 价格: ${data['usd']:,.2f} USD")

        if 'cny' in data:
            lines.append(f"💴 价格: ¥{data['cny']:,.2f} CNY")

        if 'usd_market_cap' in data:
            lines.append(f"📊 市值: ${data['usd_market_cap']:,.0f}")

        if 'usd_24h_change' in data:
            change = data['usd_24h_change']
            emoji = "📈" if change > 0 else "📉"
            lines.append(f"{emoji} 24h: {change:+.2f}%")

        return '\n'.join(lines)

    def _format_browse_result(self, result: Dict, question: str = "") -> str:
        """格式化浏览结果"""
        if result.get('error'):
            return f"❌ 浏览失败: {result['error']}"

        lines = [f"📄 {result['title']}", f"🔗 {result['url']}"]

        # 主要内容
        content = result['content']
        if question:
            # 如果有问题，尝试提取相关部分
            lines.append(f"\n【相关内容】")
            lines.append(content[:1000])
        else:
            lines.append(f"\n【内容摘要】")
            lines.append(content[:1500])

        # 子页面
        if result.get('sub_pages'):
            lines.append(f"\n【相关页面】")
            for page in result['sub_pages'][:3]:
                lines.append(f"- {page['title']}")
                lines.append(f"  {page['content'][:100]}...")

        return '\n'.join(lines)

    # === 批量浏览 ===

    def browse_multiple(self, urls: List[str]) -> List[Dict]:
        """批量浏览多个URL

        Args:
            urls: URL列表

        Returns:
            浏览结果列表
        """
        results = []

        for url in urls:
            try:
                result = self.browse(url, depth=0)
                results.append(result)
                time.sleep(1)  # 避免请求过快

            except Exception as e:
                results.append({
                    'url': url,
                    'error': str(e)
                })

        return results

    # === 工具方法 ===

    def is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def clean_text(self, html: str) -> str:
        """清理HTML文本"""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
