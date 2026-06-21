"""招标公告采集器 —— 全国公共资源交易平台(www.ggzy.gov.cn)。

默认关闭(config.ENABLE_GGZY=False)：其数据接口 getTradList 受 WAF 保护、且对境外 IP 不友好。
留作**境内 IP 部署**时备用。结构与 cninfo 对齐(source_type='tender')。礼貌：慢、随机停顿。
失败时安全返回、不影响其他源。
"""
from __future__ import annotations

from datetime import datetime, timedelta

import config
import polite

GGZY_API = "https://www.ggzy.gov.cn/information/pubTradingInfo/getTradList"


def search(keyword: str, province_code: str, lookback_days: int, max_pages: int):
    edate = datetime.now().date()
    sdate = edate - timedelta(days=lookback_days)
    with polite.client(
        "https://www.ggzy.gov.cn/deal/dealList.html?HEADER_DEAL_TYPE=01",
        timeout=20.0,
        extra_headers={"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"},
    ) as client:
        for page in range(1, max_pages + 1):
            body = {
                "TIMEBEGIN": sdate.isoformat(), "TIMEEND": edate.isoformat(),
                "DEAL_TIME": "06", "DEAL_CLASSIFY": "", "DEAL_STAGE": "",
                "DEAL_PROVINCE": province_code, "DEAL_CITY": "", "DEAL_DISTRICT": "",
                "BID_PLATFORM": "", "DEAL_TRADE": "", "DEAL_NOTICE_TYPE": "",
                "FINDTXT": keyword, "PAGENUMBER": page, "PAGESIZE": 20,
            }
            try:
                r = client.post(GGZY_API, json=body)
                if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
                    print(f"[tender] {keyword}/{province_code} 非JSON(可能被WAF拦)，跳过")
                    return
                data = r.json()
            except Exception as e:  # noqa: BLE001
                print(f"[tender] {keyword}/{province_code} p{page} 失败: {e}")
                return

            rows = (data.get("data") or {}).get("data") if isinstance(data.get("data"), dict) else data.get("data")
            rows = rows or data.get("records") or []
            if not rows:
                break
            for a in rows:
                title = a.get("title") or a.get("NAME") or a.get("name") or ""
                pub = a.get("timeShow") or a.get("transactionTime") or a.get("PUBLISHDATE") or ""
                link = a.get("url") or a.get("link") or a.get("URL") or GGZY_API
                yield {
                    "source_type": "tender",
                    "company_name_raw": "",
                    "title": title,
                    "source_url": link if link.startswith("http") else f"https://www.ggzy.gov.cn{link}",
                    "published_at": (pub or "")[:10] or None,
                    "matched_keyword": keyword,
                }
            polite.nap(config)
