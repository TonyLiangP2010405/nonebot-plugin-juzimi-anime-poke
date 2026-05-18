"""JSON 缓存模块"""
import json
import random
import time
from pathlib import Path
from typing import List, Optional

from nonebot import logger
from nonebot_plugin_localstore import get_plugin_data_dir

from .config import plugin_config
from .models import CacheData, Quote

CACHE_FILE: Optional[Path] = None


def _get_cache_path() -> Path:
    """获取缓存文件路径"""
    global CACHE_FILE
    if CACHE_FILE is None:
        data_dir = Path(get_plugin_data_dir()) / "juzimi_anime_poke"
        data_dir.mkdir(parents=True, exist_ok=True)
        CACHE_FILE = data_dir / "anime_quotes.json"
    return CACHE_FILE


def _load_cache_raw() -> dict:
    """加载原始缓存数据"""
    path = _get_cache_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"[JuzimiAnimePoke] 缓存文件损坏: {e}")
        return {}


def load_cache() -> CacheData:
    """加载缓存数据"""
    raw = _load_cache_raw()
    if not raw:
        return CacheData()
    try:
        quotes = []
        for q in raw.get("quotes", []):
            if isinstance(q, dict):
                quotes.append(Quote(text=q.get("text", ""), source=q.get("source", ""), url=q.get("url", "")))
            elif isinstance(q, str):
                quotes.append(Quote(text=q))
        return CacheData(
            updated_at=raw.get("updated_at", 0),
            quotes=quotes,
        )
    except Exception as e:
        logger.warning(f"[JuzimiAnimePoke] 缓存解析失败: {e}")
        return CacheData()


def save_cache(data: CacheData):
    """保存缓存数据"""
    path = _get_cache_path()
    try:
        raw = {
            "updated_at": data.updated_at,
            "quotes": [
                {"text": q.text, "source": q.source, "url": q.url}
                for q in data.quotes
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"[JuzimiAnimePoke] 缓存保存失败: {e}")


def is_cache_expired(data: CacheData) -> bool:
    """检查缓存是否过期"""
    if not data.updated_at:
        return True
    expire_seconds = plugin_config.juzimi_cache_expire_hours * 3600
    return (time.time() - data.updated_at) > expire_seconds


def is_cache_low(data: CacheData) -> bool:
    """检查缓存数量是否低于阈值"""
    return len(data.quotes) < plugin_config.juzimi_min_cache_count


def get_random_quote(data: CacheData) -> Optional[Quote]:
    """从缓存中随机获取一条语录"""
    if not data.quotes:
        return None
    return random.choice(data.quotes)


def add_quotes(data: CacheData, quotes: List[Quote]):
    """向缓存中添加语录（去重）"""
    existing_texts = {q.text for q in data.quotes}
    for q in quotes:
        if q.text not in existing_texts:
            data.quotes.append(q)
            existing_texts.add(q.text)
    data.updated_at = int(time.time())


def clear_cache():
    """清空缓存"""
    path = _get_cache_path()
    if path.exists():
        try:
            path.unlink()
            logger.info("[JuzimiAnimePoke] 缓存已清空")
        except OSError as e:
            logger.error(f"[JuzimiAnimePoke] 缓存清空失败: {e}")
