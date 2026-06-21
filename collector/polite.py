"""礼貌采集工具：慢、随机、低量、低频 —— 做个守规矩的访客，不是激进爬虫。

设计取向(按你的要求)：
  - 每次请求之间停得久、且**随机**(不固定节奏，偶尔多歇一会儿)，不给站点造成规律性压力；
  - 不需要实时，几小时/一天跑一次足矣；
  - 翻页少、量小。

说明：这些是「礼貌/低影响」措施(避免频控、不打扰站点)，不是对抗式反反爬。
真正决定能否稳定访问境内政务站的是**出口 IP 位置**(见 README 的境内部署说明)，不是这些参数。
"""
from __future__ import annotations

import random
import time

import httpx

import config

# 几个真实浏览器 UA，进程启动时随机选一个固定用(降低固定指纹，不做逐请求伪装)
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]
_RUN_UA = random.choice(_UA_POOL)


def headers(referer: str | None = None) -> dict:
    h = {
        "User-Agent": _RUN_UA,
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if referer:
        h["Referer"] = referer
    return h


def nap(cfg) -> None:
    """请求/关键词之间随机停顿；偶尔额外多歇，让节奏不规律。"""
    t = random.uniform(cfg.REQUEST_MIN_DELAY, cfg.REQUEST_MAX_DELAY)
    if random.random() < cfg.LONG_REST_PROB:
        t += random.uniform(*cfg.LONG_REST_RANGE)
    time.sleep(t)


def source_pause(cfg) -> None:
    """切换数据源之间停得更久一点。"""
    time.sleep(random.uniform(*cfg.SOURCE_PAUSE_RANGE))


def client(referer: str | None = None, *, timeout: float = 20.0,
           extra_headers: dict | None = None) -> httpx.Client:
    """统一构造 httpx.Client：带礼貌 headers，并在 config.EGRESS_PROXY 配置时走代理。

    代理与具体厂商无关——你给什么代理就走什么。建议指向你自有/付费的代理。
    """
    h = headers(referer)
    if extra_headers:
        h.update(extra_headers)
    kwargs: dict = {"headers": h, "timeout": timeout, "follow_redirects": True}
    proxy = getattr(config, "EGRESS_PROXY", None)
    if proxy:
        kwargs["proxy"] = proxy  # httpx 0.27：单一代理；socks5:// 需 httpx[socks]
    return httpx.Client(**kwargs)
