"""意向打分 + 交叉验证：把一堆信号聚合成排好序的线索。

score = Σ( 事件权重 × 时间衰减 ) × 多源印证乘数，封顶 100。
关键：distinct_sources 必须是「互相独立」的来源 —— 同一条新闻多站转载先按
doc_fingerprint 去重，否则评分会被转载噪音灌水。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

EVENT_WEIGHTS = {
    "招标采购": 1.0,
    "投资备案": 0.9,
    "新建项目": 0.9,
    "对外投资": 0.6,
    "选址签约": 0.6,
    "扩产":     0.5,
    "获得资质": 0.3,
    None:       0.3,
}

HALF_LIFE_DAYS = 180.0   # 时间半衰期
BASE_SCALE     = 40.0    # 单条满权重满新鲜度信号的基础分


def _recency(pub: str | None, today: date) -> float:
    if not pub:
        return 0.6
    try:
        age = (today - date.fromisoformat(pub)).days
    except (ValueError, TypeError):
        return 0.6
    age = max(age, 0)
    return 0.5 ** (age / HALF_LIFE_DAYS)


def _multiplier(distinct_sources: int) -> float:
    if distinct_sources >= 3:
        return 1.8
    if distinct_sources == 2:
        return 1.4
    return 1.0


def _status(score: int) -> str:
    if score >= 70:
        return "高置信"
    if score >= 40:
        return "待验证"
    return "前置观察"


def aggregate(signals: list[dict], today: date | None = None) -> list[dict]:
    """输入若干 signal 行，按 company_key 聚合成 leads 行。"""
    today = today or date.today()
    by_company: dict[str, list[dict]] = defaultdict(list)
    for s in signals:
        if s.get("company_key"):
            by_company[s["company_key"]].append(s)

    leads = []
    for key, sigs in by_company.items():
        # 转载去重：同一 doc_fingerprint 只算一次
        seen_fp, unique = set(), []
        for s in sigs:
            fp = s.get("doc_fingerprint")
            if fp and fp in seen_fp:
                continue
            seen_fp.add(fp)
            unique.append(s)

        distinct_sources = len({s["source_type"] for s in unique})
        raw = sum(
            EVENT_WEIGHTS.get(s.get("event_type"), 0.3)
            * _recency(s.get("published_at"), today)
            * BASE_SCALE
            for s in unique
        )
        score = min(100, round(raw * _multiplier(distinct_sources)))

        pubs = [s["published_at"] for s in unique if s.get("published_at")]
        amounts = [s["amount_wan"] for s in unique if s.get("amount_wan")]
        industries = [s["industry"] for s in unique if s.get("industry")]
        locations = [
            f"{s.get('location_prov','')}{s.get('location_city','')}"
            for s in unique
            if s.get("location_prov") or s.get("location_city")
        ]
        contacts = [s["contact_public"] for s in unique if s.get("contact_public")]

        leads.append({
            "company_key": key,
            "company_name": unique[0]["company_name_raw"] or key,
            "uscc": next((s.get("uscc") for s in unique if s.get("uscc")), None),
            "intent_score": score,
            "status": _status(score),
            "signal_count": len(unique),
            "distinct_sources": distinct_sources,
            "top_industry": max(set(industries), key=industries.count) if industries else None,
            "top_location": max(set(locations), key=locations.count) if locations else None,
            "max_amount_wan": max(amounts) if amounts else None,
            "contact_public": contacts[0] if contacts else None,
            "first_seen": min(pubs) if pubs else None,
            "last_active": max(pubs) if pubs else None,
        })

    leads.sort(key=lambda x: x["intent_score"], reverse=True)
    return leads
