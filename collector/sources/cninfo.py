"""巨潮资讯网(cninfo) 上市公司公告采集器 —— P0 数据源。

为什么先做它：免费、结构规整、几乎无反爬，是练通整条 pipeline 的最佳起点。
用的是公开的全文检索接口 fulltextSearch/full，按关键词("对外投资/新建项目/扩产"…)拉公告。

注意：cninfo 是境内站点，本机(海外CI)直连可能超时；正式运行在 GitHub Actions 上
更稳。接口字段以线上实际返回为准，若改版需按返回结构微调 parse。
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta

import httpx

FULLTEXT_URL = "http://www.cninfo.com.cn/new/fulltextSearch/full"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "http://www.cninfo.com.cn/new/fulltextSearch",
    "X-Requested-With": "XMLHttpRequest",
}

_EM = re.compile(r"</?em>")  # 接口会把命中关键词包在 <em> 里


def _clean(s: str | None) -> str:
    return _EM.sub("", s or "").strip()


def search(keyword: str, lookback_days: int, max_pages: int, delay: float):
    """按关键词全文检索公告，yield 规整后的 dict。"""
    edate = datetime.now().date()
    sdate = edate - timedelta(days=lookback_days)
    with httpx.Client(headers=HEADERS, timeout=20.0) as client:
        for page in range(1, max_pages + 1):
            params = {
                "searchkey": keyword,
                "sdate": sdate.isoformat(),
                "edate": edate.isoformat(),
                "isfulltext": "false",
                "sortName": "pubdate",
                "sortType": "desc",
                "pageNum": page,
            }
            try:
                r = client.get(FULLTEXT_URL, params=params)
                r.raise_for_status()
                data = r.json()
            except Exception as e:  # noqa: BLE001
                print(f"[cninfo] {keyword} p{page} 失败: {e}")
                break

            anns = data.get("announcements") or []
            if not anns:
                break

            for a in anns:
                ms = a.get("announcementTime")
                pub = (
                    datetime.fromtimestamp(ms / 1000).date().isoformat()
                    if isinstance(ms, (int, float))
                    else None
                )
                adj = a.get("adjunctUrl") or ""
                url = f"http://static.cninfo.com.cn/{adj}" if adj else FULLTEXT_URL
                yield {
                    "source_type": "listed_announce",
                    "company_name_raw": _clean(a.get("secName")),
                    "title": _clean(a.get("announcementTitle")),
                    "source_url": url,
                    "published_at": pub,
                    "sec_code": a.get("secCode"),
                    "matched_keyword": keyword,
                }
            time.sleep(delay)
