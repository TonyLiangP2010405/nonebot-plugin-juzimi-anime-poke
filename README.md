# nonebot-plugin-juzimi-anime-poke

<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

_✨ 戳一戳机器人，送你一句动漫语录 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/TonyLiangP2010405/nonebot-plugin-juzimi-anime-poke.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-juzimi-anime-poke">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-juzimi-anime-poke.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">

</div>

适用于 **QQ 群聊**的 NoneBot2 插件。当群友在群里戳一戳（双击头像）机器人时，机器人会自动回复一句动漫/二次元相关语录。也支持主动发送命令获取语录。

> ⚠️ **数据源说明**：原 juzimi.com（句子迷）因技术升级暂时停止访问，本插件使用 **juzikong.com（句子控）** 的「二次元经典语录」专辑作为数据源。

---

## 📖 功能

- **戳一戳触发**：群里戳机器人 → 自动回复动漫语录
- **命令触发**：`/动漫语录`、`/anime_quote`、`/二次元语录`
- **异步爬取**：从句子控网站实时爬取动漫语录
- **本地缓存**：JSON 缓存，避免高频请求网站
- **冷却机制**：戳一戳和命令独立冷却，防止刷屏
- **异常兜底**：网络失败时使用内置语录库，不报错崩溃

---

## 💿 安装

### 使用 nb-cli

```bash
nb plugin install nonebot-plugin-juzimi-anime-poke
```

### 使用 pip

```bash
pip install nonebot-plugin-juzimi-anime-poke
```

然后在 `pyproject.toml` 中添加：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_juzimi_anime_poke"]
```

---

## ⚙️ 配置

在 `.env` 文件中添加：

| 配置项 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `juzimi_cache_expire_hours` | 否 | `24` | 缓存过期时间（小时） |
| `juzimi_min_cache_count` | 否 | `20` | 缓存少于多少条时触发重新爬取 |
| `juzimi_max_pages` | 否 | `3` | 每次最多爬取多少页 |
| `juzimi_request_timeout` | 否 | `10` | 请求超时时间（秒） |
| `juzimi_poke_cd` | 否 | `10` | 戳一戳冷却时间（秒），按群计算 |
| `juzimi_command_cd` | 否 | `5` | 命令冷却时间（秒），按群/用户计算 |
| `juzimi_at_user` | 否 | `False` | 回复时是否 @ 触发用户 |

---

## 🎉 使用

### 戳一戳触发

在 QQ 群里**双击机器人头像**（戳一戳），机器人会回复一句动漫语录。

示例回复：
```
被戳到了！送你一句：
「人永远不知道，谁哪次不经意的跟你说了再见之后，就真的不会再见了。」
```

### 主动命令

发送以下任一命令：
- `/动漫语录`
- `/anime_quote`
- `/二次元语录`

示例：
```
/动漫语录

→ 「如果时光可以倒流，我还是会选择认识你，虽然会伤痕累累，但是心中的温暖记忆是谁都无法给予的。」
```

---

## 📁 项目结构

```
nonebot_plugin_juzimi_anime_poke/
├── __init__.py      # 插件入口：戳一戳监听、命令监听
├── config.py        # Pydantic 配置模型
├── crawler.py       # 异步爬虫（httpx + BeautifulSoup）
├── cache.py         # JSON 缓存读写
├── models.py        # 数据模型（Quote、CacheData）
├── README.md        # 本文件
└── pyproject.toml   # 项目配置
```

---

## 🕷️ 爬虫原理

1. 使用 `httpx.AsyncClient` 异步请求句子控网站
2. 页面使用 Nuxt.js SSR，语录数据注入在 `window.__NUXT__` 中
3. 通过正则提取 `content:"..."` 模式解析语录
4. 请求间隔 1-3 秒随机延迟，避免对网站造成压力
5. 爬取结果存入 `~/.local/share/nonebot2/juzimi_anime_poke/anime_quotes.json`
6. 优先使用缓存，缓存过期/不足时才重新爬取

---

## ⚠️ 注意事项

1. **本插件仅用于个人学习和低频自用**，不应高频请求句子控网站。
2. **请遵守目标网站的服务条款和版权要求**。
3. **不要把爬取内容用于商业用途**。
4. 爬取频率受 `juzimi_max_pages` 和延迟控制，默认每次最多请求 3 页，间隔 1-3 秒。

---

## 📋 更新日志

### [0.1.0] - 2026-05-18
- 首次发布
- 戳一戳触发动漫语录回复
- 支持主动命令 `/动漫语录`、`/anime_quote`
- 异步爬取 + JSON 缓存 + 冷却机制

---

## 📄 许可证

本项目使用 [MIT License](./LICENSE) 开源。