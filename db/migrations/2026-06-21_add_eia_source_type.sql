-- 2026-06-21 接入「环评公示」第二信源:给 signals.source_type 白名单加 'eia'。
-- 在 Supabase → SQL Editor 里执行一次(已建库的项目必须跑,否则环评信号写入会被 CHECK 拒绝)。
alter table signals drop constraint if exists signals_source_type_check;
alter table signals add constraint signals_source_type_check
  check (source_type in
    ('listed_announce','invest_record','tender','news','qualification','gov_project','eia'));
