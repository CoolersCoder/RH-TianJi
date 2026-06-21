"""文本 → 结构化信号：免费的正则/词典抽取(不调任何付费API)。

输入一条公告/新闻的标题(+可选正文)，输出结构化字段：
事件类型、金额、城市、省、行业、企业名归一键。
模板化文本(公告/招标)正则命中率高；自由文本(新闻)以后可加 LLM 兜底。
"""
from __future__ import annotations

import hashlib
import re

from config import (
    CITY_PROV,
    PROVINCES,
    EVENT_RULES,
    INDUSTRY_KEYWORDS,
)

_PROV_SET = set(PROVINCES)
# 城市键(排除省名本身);市级优先于省级识别,拿到更具体的落地城市
_CITIES = [c for c in CITY_PROV if c not in _PROV_SET]

# 金额：总投资12.5亿元 / 投资约3亿 / 5000万元
_AMT_YI  = re.compile(r"(?:总投资|拟投资|投资|金额|中标价)[约为：:\s]*([\d.]+)\s*亿")
_AMT_WAN = re.compile(r"(?:总投资|拟投资|投资|金额|中标价)[约为：:\s]*([\d.]+)\s*万")
_COMPANY = re.compile(r"[一-龥（）()]{2,40}?(?:有限公司|股份有限公司|集团|有限责任公司)")


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def extract_amount_wan(text: str):
    m = _AMT_YI.search(text)
    if m:
        try:
            return float(m.group(1)) * 10000  # 亿 → 万
        except ValueError:
            pass
    m = _AMT_WAN.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def extract_event(text: str):
    for event_type, kws in EVENT_RULES:
        if any(k in text for k in kws):
            return event_type
    return None


# 公告里的样板词会造成假地域命中(如"上海证券交易所"→误判落地上海)，先剔除。
_LOC_NOISE = [
    "上海证券交易所", "深圳证券交易所", "北京证券交易所",
    "上海证券", "上交所", "深交所", "北交所", "上海清算所",
]


def extract_location(text: str):
    for noise in _LOC_NOISE:
        text = text.replace(noise, "")
    for city in _CITIES:               # 市级优先(更具体)
        if city in text:
            return CITY_PROV[city], city
    for prov in PROVINCES:             # 再退到省级
        if prov in text:
            return prov, ""
    return "", ""


def extract_industry(text: str):
    for industry, kws in INDUSTRY_KEYWORDS.items():
        if any(k in text for k in kws):
            return industry
    return None


def normalize_company(name: str) -> str:
    """免费模式的实体归一：去括号注释、去常见后缀差异，作为聚合主键。"""
    n = re.sub(r"[（(].*?[)）]", "", name or "").strip()
    return n or (name or "").strip()


def build_signal(item: dict) -> dict:
    """把一条源数据组装成 signals 表的一行。"""
    title = item.get("title", "")
    raw_name = item.get("company_name_raw", "")
    text = f"{title} {raw_name}"
    if not raw_name:
        m = _COMPANY.search(text)
        raw_name = m.group(0) if m else ""
    # 地域优先取企业名里的城市(最可靠，如"宿迁联盛"→宿迁)；名里没有再看标题；
    # 还没有就用源带的省份提示(如政府采购按省检索时已知省份)。
    prov, city = extract_location(raw_name)
    if not prov:
        prov, city = extract_location(title)
    if not prov and item.get("province"):
        prov = item["province"]
    return {
        "source_type": item["source_type"],
        "source_url": item["source_url"],
        "source_hash": md5(item["source_url"]),
        "doc_fingerprint": md5(item.get("title", "")[:80]),
        "company_name_raw": raw_name,
        "company_key": normalize_company(raw_name),
        # 源可显式给 event_type(如环评公示);没给才从标题正则推断
        "event_type": item.get("event_type") or extract_event(text),
        "amount_wan": extract_amount_wan(text),
        "location_prov": prov or None,
        "location_city": city or None,
        "industry": extract_industry(text),
        "title": item.get("title"),
        "published_at": item.get("published_at"),
        "extract_conf": 0.8 if item["source_type"] == "listed_announce" else 0.5,
        "raw": item,
    }


def in_scope(sig: dict) -> bool:
    """全国 + 高新技术:命中高新技术行业 = 入库闸门(只收高新科技,滤掉房地产/基建/传统贸易);
    地域全国一视同仁,只作标签不再作闸门。

    代价：标题/企业名里没出现行业关键词的真高新企业会被漏(免费模式无「企业→行业」库),
    宁缺毋滥优先；待接实体/行业归一后可召回。
    """
    name = sig.get("company_key") or ""
    # 含数字的简称基本是债券/特殊证券(如"23浙建02")，不是企业主体，剔除。
    has_company = bool(name) and not any(ch.isdigit() for ch in name)
    is_hightech = sig.get("industry") is not None
    return has_company and is_hightech
