"""采集主流程(GitHub Actions 每天跑一次)：
  1. 巨潮按关键词拉公告
  2. 正则抽取成结构化信号 + 长三角/新能源新材料 过滤
  3. upsert signals 到 Supabase
  4. 拉最近一年全量信号，重算 leads(交叉验证打分) 并 upsert

本地 dry-run(不写库、不需要 Supabase)：
  DRY_RUN=1 python collector/run.py
"""
from __future__ import annotations

import os
from datetime import date

import config
import extract
import score
from sources import cninfo

DRY_RUN = os.environ.get("DRY_RUN") == "1"


def collect() -> list[dict]:
    seen_hash: set[str] = set()
    signals: list[dict] = []
    for kw in config.CNINFO_SEARCH_KEYWORDS:
        for item in cninfo.search(
            kw,
            lookback_days=config.LOOKBACK_DAYS,
            max_pages=config.MAX_PAGES_PER_KEYWORD,
            delay=config.REQUEST_DELAY_SEC,
        ):
            sig = extract.build_signal(item)
            if sig["source_hash"] in seen_hash:
                continue
            if not extract.in_scope(sig):
                continue
            seen_hash.add(sig["source_hash"])
            signals.append(sig)
    return signals


def main() -> None:
    print(f"[run] 开始采集 (dry_run={DRY_RUN}) …")
    fresh = collect()
    print(f"[run] 命中范围内信号 {len(fresh)} 条")

    if DRY_RUN:
        leads = score.aggregate(fresh, today=date.today())
        for l in leads[:15]:
            print(
                f"  {l['intent_score']:>3} {l['status']:<5} "
                f"{l['company_name'][:18]:<18} "
                f"{l.get('top_industry') or '-':<5} "
                f"{l.get('top_location') or '-':<8} "
                f"信号{l['signal_count']}/源{l['distinct_sources']}"
            )
        print(f"[run] dry-run: 聚合出 {len(leads)} 条线索(未写库)")
        return

    import store
    n = store.upsert_signals(fresh)
    print(f"[run] 写入 signals {n} 条")

    all_sigs = store.fetch_recent_signals(days=365)
    leads = score.aggregate(all_sigs, today=date.today())
    store.upsert_leads(leads)
    print(f"[run] 重算并写入 leads {len(leads)} 条")


if __name__ == "__main__":
    main()
