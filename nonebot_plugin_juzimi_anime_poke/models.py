"""数据模型定义"""
from typing import List

from pydantic import BaseModel, Field


class Quote(BaseModel):
    """动漫语录数据模型"""
    text: str = Field(..., description="语录内容")
    source: str = Field(default="", description="出处/来源")
    url: str = Field(default="", description="来源页面URL")


class CacheData(BaseModel):
    """缓存数据结构"""
    updated_at: int = Field(default=0, description="最后更新时间戳")
    quotes: List[Quote] = Field(default_factory=list, description="语录列表")


class CrawlResult(BaseModel):
    """爬虫结果"""
    quotes: List[Quote] = Field(default_factory=list)
    total_found: int = Field(default=0)
    success: bool = Field(default=False)
    error: str = Field(default="")
