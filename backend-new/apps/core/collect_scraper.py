"""
多平台商品采集引擎
- 支持平台: 1688 / 拼多多 / 淘宝
- 反屏蔽: UA 轮换 / 随机延迟 / 请求限流
- 规则驱动: 每个平台可配置 CSS 选择器规则
"""
import re
import time
import random
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("scraper")

# ── 反屏蔽：轮换 User-Agent ──
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]

# ── 请求会话池（带限流）──
_last_request_time: Dict[str, float] = {}
_MIN_INTERVAL = 1.5  # 同域名最小请求间隔（秒）


def _rate_limit(domain: str):
    """请求限流：确保同一域名请求间隔 >= _MIN_INTERVAL 秒"""
    now = time.time()
    if domain in _last_request_time:
        elapsed = now - _last_request_time[domain]
        if elapsed < _MIN_INTERVAL:
            delay = _MIN_INTERVAL - elapsed + random.uniform(0.2, 0.8)
            time.sleep(delay)
    _last_request_time[domain] = time.time()


def _random_headers(referer: str = "") -> dict:
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    return headers


# ── 平台采集规则（可扩展为数据库配置）──
@dataclass
class ScrapeRule:
    platform: str
    title_selector: str = ""
    title_regex: str = ""
    price_selector: str = ""
    price_regex: str = ""
    image_selector: str = ""
    image_attr: str = "src"
    spec_selectors: Dict[str, str] = field(default_factory=dict)
    data_script_regex: str = ""  # 从 <script> 提取 JSON


# 内置规则（后续可迁移到数据库 ScrapeRule 表）
_BUILTIN_RULES = {
    "1688": ScrapeRule(
        platform="1688",
        data_script_regex=r'window\.__PRELOADED_STATE__\s*=\s*({.+?});',
        title_selector="h1[data-testid='offerTitle'], .offer-title",
        price_selector=".price-original, .offer-price",
        image_selector="img.detail-gallery-img",
        image_attr="src",
    ),
    "pdd": ScrapeRule(
        platform="pdd",
        title_selector=".goods-name, .product-title, h1",
        price_selector=".price, .goods-price, .current-price",
        image_selector=".goods-img img, .product-img img",
        image_attr="src",
    ),
    "taobao": ScrapeRule(
        platform="taobao",
        title_selector="h1[data-spm='1000983'], .tb-main-title",
        price_selector=".tb-rmb-num, .tm-price",
        image_selector="#J_UlThumb img",
        image_attr="data-src",
    ),
}


# ── 解析工具函数 ──

def _safe_text(soup: BeautifulSoup, selector: str) -> str:
    try:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""
    except Exception:
        return ""


def _safe_attr(soup: BeautifulSoup, selector: str, attr: str) -> str:
    try:
        el = soup.select_one(selector)
        return (el.get(attr) or "").strip() if el else ""
    except Exception:
        return ""


def _extract_from_script(html: str, regex: str) -> Optional[dict]:
    """从 <script> 标签中提取 JSON 数据"""
    if not regex:
        return None
    m = re.search(regex, html, re.DOTALL)
    if not m:
        return None
    try:
        import json
        return json.loads(m.group(1))
    except Exception:
        return None


def _recursive_extract(obj: Any, keys: tuple, max_depth=10) -> Optional[str]:
    """递归遍历 JSON 对象，找到匹配的 key 对应的字符串值"""
    if max_depth <= 0:
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, str) and v.strip():
                return v.strip()
            r = _recursive_extract(v, keys, max_depth - 1)
            if r:
                return r
    elif isinstance(obj, list):
        for item in obj:
            r = _recursive_extract(item, keys, max_depth - 1)
            if r:
                return r
    return None


def _extract_number(text: str) -> float:
    """从文本中提取价格数字"""
    m = re.search(r'[\d.]+', text.replace(",", ""))
    return float(m.group()) if m else 0.0


# ── 主采集函数 ──

@dataclass
class ScrapedProduct:
    title: str = ""
    price: float = 0.0
    images: List[str] = field(default_factory=list)
    specs: Dict[str, str] = field(default_factory=dict)
    stock: int = 0
    platform: str = ""
    source_url: str = ""
    platform_product_id: str = ""
    raw: dict = field(default_factory=dict)


def scrape_product(url: str, platform: str = "") -> Optional[ScrapedProduct]:
    """
    采集单个商品链接
    Args:
        url: 商品链接
        platform: 平台标识 (1688/pdd/taobao)，留空则自动识别
    """
    # 自动识别平台
    if not platform:
        platform = _detect_platform(url)
    if not platform:
        return None

    rule = _BUILTIN_RULES.get(platform)
    if not rule:
        return None

    # 反屏蔽处理
    domain = _extract_domain(url)
    _rate_limit(domain)
    headers = _random_headers(url)

    try:
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text
    except requests.RequestException as e:
        logger.warning(f"请求失败 [{platform}] {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    product = ScrapedProduct(platform=platform, source_url=url)

    # 策略1：从页面内嵌 JSON 提取（1688 __PRELOADED_STATE__）
    if rule.data_script_regex:
        data = _extract_from_script(html, rule.data_script_regex)
        if data:
            product.title = _recursive_extract(
                data, ("offerTitle", "title", "subject", "productName")
            ) or ""
            p = _recursive_extract(data, ("price", "offerPrice", "amount", "salePrice"))
            if p:
                product.price = _extract_number(p)
            # 提取图片列表
            img_data = _recursive_extract(data, ("offerImgList", "images", "imageList"))
            # 尝试从 JSON 中提取图片 URL 列表
            product.raw = data

    # 策略2：CSS 选择器解析
    if not product.title and rule.title_selector:
        product.title = _safe_text(soup, rule.title_selector)
    if not product.title and rule.title_regex:
        m = re.search(rule.title_regex, html)
        if m:
            product.title = m.group(1).strip()

    if not product.price and rule.price_selector:
        pt = _safe_text(soup, rule.price_selector)
        if pt:
            product.price = _extract_number(pt)
    if not product.price and rule.price_regex:
        m = re.search(rule.price_regex, html)
        if m:
            product.price = _extract_number(m.group(1))

    if rule.image_selector:
        imgs = soup.select(rule.image_selector)
        for img in imgs[:10]:
            src = img.get(rule.image_attr, "") or img.get("src", "")
            if src and src.startswith("http"):
                product.images.append(src)

    # 降级：从 <title> 和所有 <img> 提取
    if not product.title:
        t = soup.find("title")
        if t:
            product.title = t.get_text(strip=True)
    if not product.images:
        for img in soup.find_all("img")[:10]:
            src = img.get("src") or img.get("data-src") or ""
            if src.startswith("http"):
                product.images.append(src)

    # 提取平台商品ID
    product.platform_product_id = _extract_product_id(url, platform)

    if not product.title:
        logger.warning(f"无法提取标题 [{platform}] {url}")
        return None

    return product


def scrape_batch(urls: List[str], platform: str = "") -> List[Dict[str, Any]]:
    """批量采集，返回每个 URL 的结果"""
    results = []
    for url in urls:
        prod = scrape_product(url, platform)
        if prod:
            results.append({
                "title": prod.title,
                "price": prod.price,
                "images": prod.images,
                "specs": prod.specs,
                "platform": prod.platform,
                "source_url": prod.source_url,
                "platform_product_id": prod.platform_product_id,
                "status": "success",
            })
        else:
            results.append({
                "source_url": url,
                "status": "failed",
                "platform": platform or _detect_platform(url) or "unknown",
            })
        # 批量时加大间隔
        time.sleep(random.uniform(1.0, 2.5))
    return results


def _detect_platform(url: str) -> str:
    """根据 URL 自动识别平台"""
    url_lower = url.lower()
    if "1688.com" in url_lower:
        return "1688"
    if "yangkeduo.com" in url_lower or "pinduoduo.com" in url_lower:
        return "pdd"
    if "taobao.com" in url_lower or "tmall.com" in url_lower:
        return "taobao"
    return ""


def _extract_domain(url: str) -> str:
    m = re.match(r'https?://([^/]+)', url)
    return m.group(1) if m else url


def _extract_product_id(url: str, platform: str) -> str:
    if platform == "1688":
        m = re.search(r'offer/(\d+)', url)
        return m.group(1) if m else ""
    if platform == "pdd":
        m = re.search(r'goods/(\d+)', url)
        return m.group(1) if m else ""
    if platform in ("taobao", "tmall"):
        m = re.search(r'[?&]id=(\d+)', url)
        return m.group(1) if m else ""
    return ""
