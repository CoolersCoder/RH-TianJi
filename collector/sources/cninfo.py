"""巨潮资讯网(cninfo) 上市公司公告采集器 —— P0 数据源(免费、结构规整、几乎无反爬)。

用公开全文检索接口 fulltextSearch/full，按关键词拉公告。礼貌采集：慢、随机停顿(见 polite)。
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import config
import polite

FULLTEXT_URL = "http://www.cninfo.com.cn/new/fulltextSearch/full"
_EM = re.compile(r"</?em>")  # 接口会把命中关键词包在 <em> 里


def _clean(s: str | None) -> str:
    return _EM.sub("", s or "").strip()


def search(keyword: str, lookback_days: int, max_pages: int):
    """按关键词全文检索公告，yield 规整后的 dict。"""
    edate = datetime.now().date()
    sdate = edate - timedelta(days=lookback_days)
    with polite.client(
        "http://www.cninfo.com.cn/new/fulltextSearch",
        timeout=20.0,
        extra_headers={"Accept": "application/json, text/plain, */*", "X-Requested-With": "XMLHttpRequest"},
    ) as client:
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
            polite.nap(config)  # 慢、随机停顿
