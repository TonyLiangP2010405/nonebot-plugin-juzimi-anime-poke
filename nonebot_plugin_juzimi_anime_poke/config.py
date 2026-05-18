"""插件配置"""
from typing import List

from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class JuzimiConfig(BaseModel):
    """句子迷动漫语录插件配置"""

    # 数据源配置
    juzimi_source_url: str = Field(
        default="https://www.juzikong.com/collections/5cb13c30-c010-44dc-b44d-57ea4eb5bae9",
        description="句子来源页面URL（默认：句子控二次元经典语录专辑）"
    )
    juzimi_collection_ids: List[str] = Field(
        default_factory=lambda: [
            "5cb13c30-c010-44dc-b44d-57ea4eb5bae9",  # 二次元经典语录
        ],
        description="多个句子控收藏集ID，用于轮询爬取"
    )

    # 缓存配置
    juzimi_cache_expire_hours: int = Field(
        default=24,
        description="缓存过期时间（小时）"
    )
    juzimi_min_cache_count: int = Field(
        default=20,
        description="缓存少于多少条时触发重新爬取"
    )

    # 爬虫配置
    juzimi_max_pages: int = Field(
        default=3,
        description="每次最多爬取多少页"
    )
    juzimi_request_timeout: int = Field(
        default=10,
        description="请求超时时间（秒）"
    )
    juzimi_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="HTTP请求User-Agent"
    )

    # 冷却配置
    juzimi_poke_cd: int = Field(
        default=10,
        description="戳一戳冷却时间（秒），按群计算"
    )
    juzimi_command_cd: int = Field(
        default=5,
        description="命令冷却时间（秒），按群/用户计算"
    )

    # 回复配置
    juzimi_at_user: bool = Field(
        default=False,
        description="回复时是否@触发用户"
    )
    juzimi_reply_formats: List[str] = Field(
        default_factory=lambda: [
            "「{text}」",
            "「{text}」\n—— {source}",
            "被戳到啦，送你一句动漫句子：\n「{text}」",
            "「{text}」\n来源：句子控",
        ],
        description="回复格式模板列表，支持 {text} {source} 占位符"
    )

    # 兜底配置
    juzimi_fallback_quotes: List[str] = Field(
        default_factory=lambda: [
            "人永远不知道，谁哪次不经意的跟你说了再见之后，就真的不会再见了。——《千与千寻》",
            "如果时光可以倒流，我还是会选择认识你，虽然会伤痕累累，但是心中的温暖记忆是谁都无法给予的。",
            "按照自己的喜好去做，得不到别人的赞赏也没关系。",
            "什么都无法舍弃的人，什么也改变不了。——《进击的巨人》",
            "我想一直在你身边，直到你不需要我的时候。",
            "我不知道去哪里，但我一直在路上。",
            "我们的相遇绝不是偶然，我们定不会毫无理由地出现在彼此的生命中。",
            "所有人都知道，自由并不是放纵，那是火一般的梦想。",
            "一举一动，都是承诺，会被另一个人看在眼里，记在心上的。",
            "即使不下雨，我也在这里啊。",
        ],
        description="网络不可用时的兜底语录库"
    )


plugin_config = get_plugin_config(JuzimiConfig)
Config = JuzimiConfig  # 兼容别名
