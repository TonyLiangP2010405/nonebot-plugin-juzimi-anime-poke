"""NoneBot 加载测试"""
import pytest
import nonebot


def test_plugin_load():
    """测试插件能否被 NoneBot 正常加载"""
    nonebot.init()
    plugin = nonebot.load_plugin("nonebot_plugin_juzimi_anime_poke")
    assert plugin is not None
    assert plugin.metadata is not None
    assert plugin.metadata.name == "动漫语录戳一戳"
