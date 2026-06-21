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

import random

import config
import extract
import polite
import score
from sources import ccgp, cninfo, eia, tender

DRY_RUN = os.environ.get("DRY_RUN") == "1"


def _ingest(items, seen_hash, signals):
    for item in items:
        sig = extract.build_signal(item)
        if sig["source_hash"] in seen_hash or not extract.in_scope(sig):
            continue
        seen_hash.add(sig["source_hash"])
        signals.append(sig)


def collect() -> list[dict]:
    seen_hash: set[str] = set()
    signals: list[dict] = []

    # 源1：巨潮上市公告(主力，稳定可达)。打乱关键词顺序，让访问节奏不规律。
    kws = list(config.CNINFO_SEARCH_KEYWORDS)
    random.shuffle(kws)
    for kw in kws:
        _ingest(cninfo.search(kw, config.LOOKBACK_DAYS, config.MAX_PAGES_PER_KEYWORD), seen_hash, signals)
        polite.nap(config)
    polite.source_pause(config)

    # 源2：中国政府采购网。境外IP被限频、0 产出、空等约 25 分钟,默认关闭(境内 IP 可在 config 打开)。
    if getattr(config, "ENABLE_CCGP", False):
        polite.source_pause(config)
        try:
            combos = [(kw, prov) for kw in config.CCGP_SEARCH_KEYWORDS
                      for prov in config.CHANGSANJIAO_PROVINCES]
            random.shuffle(combos)
            for kw, prov in combos:
                _ingest(ccgp.search(kw, prov, config.LOOKBACK_DAYS, config.MAX_PAGES_PER_KEYWORD), seen_hash, signals)
                polite.nap(config)
        except Exception as e:  # noqa: BLE001
            print(f"[run] 政府采购源整体跳过: {e}")

    # 源3：环评公示(上海生态环境局)。**境外可达的真·第二信源**，与巨潮独立 → 交叉验证。
    if getattr(config, "ENABLE_EIA", True):
        polite.source_pause(config)
        try:
            n0 = len(signals)
            _ingest(eia.search(config.LOOKBACK_DAYS, config.EIA_MAX_PAGES), seen_hash, signals)
            print(f"[run] 环评源命中 {len(signals) - n0} 条")
        except Exception as e:  # noqa: BLE001
            print(f"[run] 环评源整体跳过: {e}")

    # 源4：全国公共资源交易平台(默认关闭，多被 WAF/境外IP 拦；境内IP 可在 config 打开)。
    if getattr(config, "ENABLE_GGZY", False):
        polite.source_pause(config)
        try:
            for kw in config.TENDER_SEARCH_KEYWORDS:
                for code in config.GGZY_PROVINCE_CODES.values():
                    _ingest(tender.search(kw, code, config.LOOKBACK_DAYS, config.MAX_PAGES_PER_KEYWORD), seen_hash, signals)
                    polite.nap(config)
        except Exception as e:  # noqa: BLE001
            print(f"[run] 招标源整体跳过: {e}")

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
