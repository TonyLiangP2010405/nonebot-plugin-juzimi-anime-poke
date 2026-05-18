"""异步爬虫模块 - 从句子控网站爬取动漫语录"""
import asyncio
import random
import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from nonebot import logger

from .config import plugin_config
from .models import CrawlResult, Quote


async def fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """异步获取页面HTML"""
    try:
        headers = {
            "User-Agent": plugin_config.juzimi_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        resp = await client.get(url, headers=headers, timeout=plugin_config.juzimi_request_timeout)
        resp.raise_for_status()
        return resp.text
    except httpx.TimeoutException:
        logger.warning(f"[JuzimiAnimePoke] 请求超时: {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"[JuzimiAnimePoke] HTTP错误 {e.response.status_code}: {url}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"[JuzimiAnimePoke] 网络错误: {e}")
        return None


def extract_from_nuxt(html: str) -> List[Quote]:
    """从 Nuxt SSR 数据中解析语录"""
    quotes = []

    # 查找 window.__NUXT__ 数据
    nuxt_match = re.search(
        r'window\.__NUXT__=\(function\(.*?\)\{(.*?)\}\(',
        html,
        re.DOTALL
    )
    if not nuxt_match:
        logger.debug("[JuzimiAnimePoke] 未找到 __NUXT__ 数据")
        return quotes

    nuxt_content = nuxt_match.group(1)

    # 方法1: 直接匹配 content:"text" 模式
    contents = re.findall(
        r'content:"([^"]{10,500})"',
        nuxt_content
    )

    # 方法2: 尝试从 JSON 结构中提取（带引号转义的）
    contents_escaped = re.findall(
        r'content:"((?:[^"\\]|\\.){10,500})"',
        nuxt_content
    )

    all_texts = set(contents + contents_escaped)

    for text in all_texts:
        text = text.strip()
        # 过滤掉太短的
        if len(text) < 10:
            continue
        # 过滤掉 URL/路径
        if text.startswith("/") or text.startswith("http"):
            continue
        # 过滤掉导航路径
        if text.startswith("discovery/") or text.startswith("collections/"):
            continue
        # 过滤掉可能的代码片段
        if text.startswith("function") or text.startswith("var "):
            continue

        # 清理转义字符
        text = text.replace("\\n", "\n").replace("\\r", "").replace("\\t", " ")
        text = text.replace('\\"', '"').replace("\\'", "'")

        # 尝试从附近提取来源（如果页面有的话）
        source = ""

        quotes.append(Quote(text=text, source=source, url=""))

    logger.info(f"[JuzimiAnimePoke] 从 Nuxt SSR 提取到 {len(quotes)} 条语录")
    return quotes


def extract_from_html(html: str) -> List[Quote]:
    """从纯HTML中解析语录（备用方案）"""
    quotes = []
    soup = BeautifulSoup(html, "html.parser")

    # 尝试多种可能的 CSS 选择器
    selectors = [
        # 句子控可能的选择器
        '.sentence-item .content',
        '.quote-item .text',
        '.sentence-card .sentence-content',
        '[class*="sentence"] [class*="content"]',
        '[class*="quote"] [class*="text"]',
        # 通用选择器
        '.content',
        'p.content',
        'blockquote',
    ]

    for selector in selectors:
        elements = soup.select(selector)
        for elem in elements:
            text = elem.get_text(strip=True)
            if len(text) >= 10 and len(text) <= 500:
                # 尝试找来源
                source = ""
                parent = elem.parent
                if parent:
                    source_elem = parent.select_one('.author, .source, .from, [class*="author"], [class*="source"]')
                    if source_elem:
                        source = source_elem.get_text(strip=True)

                quotes.append(Quote(text=text, source=source, url=""))

        if quotes:
            logger.info(f"[JuzimiAnimePoke] 选择器 '{selector}' 提取到 {len(quotes)} 条语录")
            break

    return quotes


async def crawl_collection(collection_id: str, page: int = 1) -> CrawlResult:
    """爬取单个收藏集的语录"""
    url = f"https://www.juzikong.com/collections/{collection_id}"
    if page > 1:
        url += f"?page={page}"

    result = CrawlResult()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        html = await fetch_page(client, url)
        if html is None:
            result.error = "网络请求失败"
            return result

        # 优先使用 Nuxt SSR 解析
        quotes = extract_from_nuxt(html)

        # 如果 SSR 没数据，尝试 HTML 解析
        if not quotes:
            quotes = extract_from_html(html)

        result.quotes = quotes
        result.total_found = len(quotes)
        result.success = len(quotes) > 0

        if result.success:
            logger.info(f"[JuzimiAnimePoke] 成功从 {url} 爬取 {len(quotes)} 条语录")
        else:
            result.error = "未从页面解析到语录"
            logger.warning(f"[JuzimiAnimePoke] 从 {url} 未解析到语录")

    return result


async def crawl_all() -> CrawlResult:
    """爬取所有配置的收藏集"""
    all_quotes: List[Quote] = []
    total_found = 0

    collection_ids = plugin_config.juzimi_collection_ids
    max_pages = plugin_config.juzimi_max_pages

    logger.info(f"[JuzimiAnimePoke] 开始爬取 {len(collection_ids)} 个收藏集，每集最多 {max_pages} 页")

    for cid in collection_ids:
        for page in range(1, max_pages + 1):
            # 添加随机延迟，避免对网站造成压力
            if page > 1 or cid != collection_ids[0]:
                delay = random.uniform(1.0, 3.0)
                logger.debug(f"[JuzimiAnimePoke] 等待 {delay:.1f} 秒后请求下一页")
                await asyncio.sleep(delay)

            result = await crawl_collection(cid, page)
            if result.success:
                all_quotes.extend(result.quotes)
                total_found += result.total_found
            else:
                if "网络请求失败" in result.error:
                    # 网络错误，不再继续
                    break

    # 去重
    seen = set()
    unique_quotes = []
    for q in all_quotes:
        if q.text not in seen:
            seen.add(q.text)
            unique_quotes.append(q)

    final_result = CrawlResult(
        quotes=unique_quotes,
        total_found=total_found,
        success=len(unique_quotes) > 0,
    )

    if not final_result.success:
        final_result.error = "爬取失败，未获取到语录"

    logger.info(f"[JuzimiAnimePoke] 爬取完成，共 {len(unique_quotes)} 条唯一语录（原始 {total_found} 条）")
    return final_result


async def get_quote_with_cache() -> Optional[Quote]:
    """
    获取一条动漫语录（带缓存逻辑）
    优先使用缓存，缓存为空/过期时才爬取
    """
    from .cache import add_quotes, get_random_quote, is_cache_expired, is_cache_low, load_cache, save_cache

    cache = load_cache()

    # 检查缓存是否可用
    if cache.quotes and not is_cache_expired(cache) and not is_cache_low(cache):
        logger.debug("[JuzimiAnimePoke] 使用缓存语录")
        return get_random_quote(cache)

    # 缓存不可用，尝试爬取
    logger.info("[JuzimiAnimePoke] 缓存为空/过期/不足，开始爬取")
    result = await crawl_all()

    if result.success:
        add_quotes(cache, result.quotes)
        save_cache(cache)
        return get_random_quote(cache)

    # 爬取失败，尝试使用已有缓存（即使过期）
    if cache.quotes:
        logger.warning("[JuzimiAnimePoke] 爬取失败，使用过期缓存")
        return get_random_quote(cache)

    # 彻底失败，返回 None
    logger.error("[JuzimiAnimePoke] 无法获取语录（网络失败且缓存为空）")
    return None
