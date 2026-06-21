-- 招商线索引擎 · 数据模型 (Supabase / Postgres)
-- 两张核心表：signals(原子信号, 证据级) + leads(按企业聚合的线索)
-- 免费模式说明：没有付费API做实体归一，所以用「标准化企业全称」当主键(company_key)，
-- uscc 列预留，等以后接天眼查/企查查再回填。

-- ── 信号表：每条公开信息抽取出的一个原子事件 ─────────────────────────────
create table if not exists signals (
  signal_id        bigint generated always as identity primary key,
  source_type      text not null
                   check (source_type in
                     ('listed_announce','invest_record','tender','news','qualification','gov_project')),
  source_url       text not null,
  source_hash      text not null unique,        -- md5(source_url)，主去重键
  doc_fingerprint  text,                        -- 内容指纹，防转载灌水(同新闻多站转载)
  company_name_raw text not null,               -- 抽到的原始企业名(脏)
  company_key      text,                        -- 标准化后的企业名(归一主键)
  uscc             text,                         -- 统一社会信用代码(免费模式下多为空)
  event_type       text,                        -- 新建项目|扩产|对外投资|招标采购|选址签约|投资备案|获得资质
  amount_wan       numeric,                      -- 投资/中标金额(万元)
  location_prov    text,                         -- 省
  location_city    text,                         -- 市
  industry         text,                         -- 新能源|新材料|...
  contact_public   text,                         -- 工商公开联系电话(仅企业，绝不存个人)
  title            text,
  published_at     date,
  fetched_at       timestamptz default now(),
  extract_conf     real default 0.5,             -- 抽取置信度 0~1
  raw              jsonb                          -- 原始返回，可回放重抽
);

create index if not exists idx_signals_company on signals (company_key);
create index if not exists idx_signals_pubdate on signals (published_at desc);
create index if not exists idx_signals_fp      on signals (doc_fingerprint);

-- ── 线索表：按企业滚动聚合，App 直接读这张 ───────────────────────────────
create table if not exists leads (
  company_key      text primary key,
  company_name     text not null,
  uscc             text,
  intent_score     int  default 0,               -- 意向强度 0~100
  status           text,                          -- 高置信|待验证|前置观察
  signal_count     int  default 0,
  distinct_sources int  default 0,                -- 互相独立的来源数(交叉验证核心)
  top_industry     text,
  top_location     text,
  max_amount_wan   numeric,
  contact_public   text,
  first_seen       date,
  last_active      date,
  updated_at       timestamptz default now()
);

create index if not exists idx_leads_score  on leads (intent_score desc);
create index if not exists idx_leads_active on leads (last_active desc);

-- App 是只读消费者：开启 RLS，匿名只读 leads/signals，写入只走 service_role(GitHub Actions)。
alter table leads   enable row level security;
alter table signals enable row level security;

drop policy if exists "anon read leads"   on leads;
drop policy if exists "anon read signals" on signals;
create policy "anon read leads"   on leads   for select using (true);
create policy "anon read signals" on signals for select using (true);

-- 2026-05-30 起 Supabase 新项目不再自动给 anon/authenticated 授权，必须显式 GRANT，
-- 否则 App 走 REST API 读不到数据(返回空)。service_role(CI写入)同样补上。
grant select on leads, signals to anon, authenticated;
grant select, insert, update on leads, signals to service_role;
grant usage, select on all sequences in schema public to service_role;
