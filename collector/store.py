"""Supabase 读写：通过 PostgREST 直接 upsert，不引第三方SDK，依赖最小。

需要两个环境变量(在 GitHub Actions Secrets 里配)：
  SUPABASE_URL          形如 https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY  service_role 密钥(只在服务端/CI用，绝不进App)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _chunk(rows: list[dict], n: int = 200):
    for i in range(0, len(rows), n):
        yield rows[i : i + n]


def upsert_signals(rows: list[dict]) -> int:
    """按 source_hash 去重 upsert。"""
    if not rows:
        return 0
    written = 0
    with httpx.Client(timeout=30.0) as client:
        for batch in _chunk(rows):
            r = client.post(
                f"{URL}/rest/v1/signals?on_conflict=source_hash",
                headers=_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                json=batch,
            )
            r.raise_for_status()
            written += len(batch)
    return written


def upsert_leads(rows: list[dict]) -> int:
    if not rows:
        return 0
    ts = datetime.now(timezone.utc).isoformat()  # PostgREST 不会执行 now()，得给真实时间戳
    with httpx.Client(timeout=30.0) as client:
        for batch in _chunk(rows):
            r = client.post(
                f"{URL}/rest/v1/leads?on_conflict=company_key",
                headers=_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                json=[{**b, "updated_at": ts} for b in batch],
            )
            r.raise_for_status()
    return len(rows)


def fetch_recent_signals(days: int = 365) -> list[dict]:
    """拉最近 N 天信号，用于重算 leads(全量聚合，含历史)。"""
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{URL}/rest/v1/signals",
            headers=_headers(),
            params={
                "select": "company_key,company_name_raw,uscc,source_type,event_type,"
                          "amount_wan,location_prov,location_city,industry,contact_public,"
                          "doc_fingerprint,published_at",
                "published_at": f"gte.{_days_ago(days)}",
                "limit": "10000",
            },
        )
        r.raise_for_status()
        return r.json()


def _days_ago(days: int) -> str:
    from datetime import date, timedelta
    return (date.today() - timedelta(days=days)).isoformat()
