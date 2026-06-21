"""中国政府采购网(ccgp.gov.cn) 采集 —— 免费、全国、全公开的政务招标/采购源。

用公开搜索 search.ccgp.gov.cn/bxsearch，按 省份 + 关键词 + 时间 拉公告，
作为与巨潮(上市公告)**互相独立**的第二信源 → 触发交叉验证(高置信 + 印章)。

⚠️ 实测：该站对**境外出口 IP** 限频严重(直接返回"您的访问过于频繁")；
   需在**境内 IP**(国内云服务器/单位网络)上运行才稳定。命中限频时安全返回空、不抛错。

礼貌采集：慢、随机停顿(见 polite)、低翻页。解析结构若日后改版需微调正则。
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import config
import polite

SEARCH_URL = "http://search.ccgp.gov.cn/bxsearch"

# 结果条目：<a href="...htm">标题</a> ... 其后文本含 采购人/行政区域/公告时间，直到 </li>
_ITEM = re.compile(r'<a href="(?P<url>https?://[^"]+?\.htm[^"]*)"[^>]*>(?P<title>.*?)</a>(?P<rest>.*?)</li>', re.S)
_BUYER = re.compile(r"采购人[:：]\s*([^\s|<]+)")
_DATE = re.compile(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})")
_COMPANYISH = re.compile(r"(有限公司|股份|集团|有限责任公司)$")
_TAG = re.compile(r"<[^>]+>")


def _clean(s: str | None) -> str:
    return _TAG.sub("", s or "").strip()


def search(keyword: str, province_name: str, lookback_days: int, max_pages: int):
    """按关键词 + 省份检索政府采购公告，yield 与 cninfo 对齐的 dict。"""
    edate = datetime.now().date()
    sdate = edate - timedelta(days=lookback_days)
    with polite.client("http://www.ccgp.gov.cn/", timeout=25.0) as client:
        for page in range(1, max_pages + 1):
            params = {
                "searchtype": 1, "page_index": page, "bidSort": 0,
                "buyerName": "", "projectId": "", "pinMu": 0, "bidType": 0,
                "dbselect": "bidx", "kw": keyword,
                "start_time": sdate.isoformat(), "end_time": edate.isoformat(),
                "timeType": 6, "displayZone": province_name,
                "zoneId": "", "pppStatus": 0, "agentName": "",
            }
            try:
                r = client.get(SEARCH_URL, params=params)
                html = r.text
            except Exception as e:  # noqa: BLE001
                print(f"[ccgp] {keyword}/{province_name} p{page} 失败: {e}")
                return
            if r.status_code != 200 or "频繁访问" in html or "访问过于频繁" in html:
                print(f"[ccgp] {keyword}/{province_name} 被限频/异常(多半出口IP在境外)，跳过")
                return

            items = list(_ITEM.finditer(html))
            if not items:
                break
            for m in items:
                rest = m.group("rest")
                bm = _BUYER.search(rest)
                buyer = _clean(bm.group(1)) if bm else ""
                company = buyer if _COMPANYISH.search(buyer) else ""  # 只把"公司类"采购人当企业，过滤政府部门
                dm = _DATE.search(rest)
                pub = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else None
                yield {
                    "source_type": "tender",
                    "company_name_raw": company,        # 空则交给 extract 从标题兜底抽公司
                    "title": _clean(m.group("title")),
                    "source_url": m.group("url"),
                    "published_at": pub,
                    "province": province_name,          # 显式省份，extract 兜底定位用
                    "matched_keyword": keyword,
                }
            polite.nap(config)
