"""NoneBot2 插件：句子迷动漫语录戳一戳

当 QQ 群里有人戳机器人时，自动回复一句动漫语录。
也支持主动命令触发。

注意：原 juzimi.com 因技术升级暂停访问，本插件使用句子控 juzikong.com 的二次元经典语录专辑作为数据源。
"""
import random
import time
from typing import Dict

from nonebot import logger, on_command, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment, PokeNotifyEvent
from nonebot.plugin import PluginMetadata

from .config import Config, plugin_config
from .crawler import get_quote_with_cache
from .models import Quote

__plugin_meta__ = PluginMetadata(
    name="动漫语录戳一戳",
    description="当有人戳机器人时，自动回复一句动漫/二次元语录。支持主动命令触发。",
    usage=(
        "戳一戳机器人（群里）→ 自动回复动漫语录\n"
        "发送 /动漫语录 或 /anime_quote 主动获取语录"
    ),
    type="application",
    homepage="https://github.com/TonyLiangP2010405/nonebot-plugin-juzimi-anime-poke",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# ========== 内存冷却状态 ==========
_poke_cooldowns: Dict[int, float] = {}  # {group_id: last_poke_time}
_cmd_cooldowns: Dict[tuple, float] = {}  # {(group_id, user_id): last_cmd_time}


def _is_poke_cooled(group_id: int) -> bool:
    """检查戳一戳冷却"""
    last = _poke_cooldowns.get(group_id, 0)
    return (time.time() - last) >= plugin_config.juzimi_poke_cd


def _record_poke(group_id: int):
    """记录戳一戳时间"""
    _poke_cooldowns[group_id] = time.time()


def _is_cmd_cooled(group_id: int, user_id: int) -> bool:
    """检查命令冷却"""
    key = (group_id, user_id)
    last = _cmd_cooldowns.get(key, 0)
    return (time.time() - last) >= plugin_config.juzimi_command_cd


def _record_cmd(group_id: int, user_id: int):
    """记录命令时间"""
    _cmd_cooldowns[(group_id, user_id)] = time.time()


# ========== 格式化回复 ==========

def format_reply(quote: Quote, is_poke: bool = True) -> str:
    """格式化语录回复"""
    text = quote.text
    source = quote.source or "句子控"

    formats = plugin_config.juzimi_reply_formats
    template = random.choice(formats)

    reply = template.format(text=text, source=source)

    # 如果是戳一戳触发，50% 概率加上戳一戳相关的开头
    if is_poke and random.random() < 0.5:
        poke_intros = [
            "被戳到了！送你一句：\n",
            "哎呀被戳了，给你一句动漫语录：\n",
            "戳我干嘛？算了送你一句吧：\n",
            "感受到了你的戳戳，回你一句：\n",
            "别戳了别戳了，给句动漫语录：\n",
        ]
        reply = random.choice(poke_intros) + reply

    return reply


# ========== 戳一戳事件监听 ==========

poke_handler = on_notice(priority=10, block=False)


@poke_handler.handle()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    """处理戳一戳事件"""
    # 获取目标 ID 和自身 ID
    target_id = getattr(event, "target_id", None)
    self_id = getattr(event, "self_id", None) or bot.self_id

    # 如果不是戳机器人自己，不处理
    if str(target_id) != str(self_id):
        return

    # 只处理群聊场景
    if not isinstance(event, PokeNotifyEvent):
        return

    # 获取群号
    group_id = getattr(event, "group_id", None)
    if group_id is None:
        return

    logger.info(f"[JuzimiAnimePoke] 收到群 {group_id} 的戳一戳")

    # 冷却检查
    if not _is_poke_cooled(group_id):
        logger.debug(f"[JuzimiAnimePoke] 群 {group_id} 戳一戳冷却中，跳过")
        return

    _record_poke(group_id)

    # 获取语录
    quote = await get_quote_with_cache()

    if quote is None:
        # 使用兜底语录
        fallback = random.choice(plugin_config.juzimi_fallback_quotes)
        reply = f"暂时没能从句子控拿到动漫语录，先送你一句吧：\n「{fallback}」"
    else:
        reply = format_reply(quote, is_poke=True)

    # 构建消息
    msg = Message()
    if plugin_config.juzimi_at_user:
        user_id = getattr(event, "user_id", None)
        if user_id:
            msg += MessageSegment.at(user_id)
            msg += "\n"
    msg += reply

    # 发送回复
    try:
        await bot.send_group_msg(group_id=group_id, message=msg)
        logger.info(f"[JuzimiAnimePoke] 已向群 {group_id} 发送动漫语录")
    except Exception as e:
        logger.error(f"[JuzimiAnimePoke] 发送消息失败: {e}")


# ========== 主动命令 ==========

anime_quote_cmd = on_command("动漫语录", aliases={"anime_quote", "二次元语录", "anime"}, priority=5, block=True)


@anime_quote_cmd.handle()
async def handle_anime_quote(bot: Bot, event: GroupMessageEvent):
    """处理主动命令"""
    group_id = event.group_id
    user_id = event.user_id

    # 冷却检查
    if not _is_cmd_cooled(group_id, user_id):
        logger.debug(f"[JuzimiAnimePoke] 用户 {user_id} 命令冷却中")
        # 低概率回复冷却提示，避免刷屏
        if random.random() < 0.3:
            await anime_quote_cmd.finish("别催啦，动漫语录也需要冷静一下～")
        return

    _record_cmd(group_id, user_id)

    # 获取语录
    quote = await get_quote_with_cache()

    if quote is None:
        fallback = random.choice(plugin_config.juzimi_fallback_quotes)
        reply = f"暂时没能从句子控拿到语录，先送你一句吧：\n「{fallback}」"
    else:
        reply = format_reply(quote, is_poke=False)

    await anime_quote_cmd.finish(reply)


logger.info("[JuzimiAnimePoke] 动漫语录戳一戳插件已加载")
