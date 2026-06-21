# 招商线索引擎（长三角 · 新能源/新材料）· 免费版 MVP

从**公开渠道**持续发现「有真实落地/扩产/投资意向」的企业，按意向强度排序，
推到手机 App 上。先聚焦**长三角 + 新能源/新材料**，**全程零成本**。

## 为什么不是"纯手机 App"

24/7 的采集器**不能**跑在手机上 —— iOS/Android 会杀后台进程，且从手机 IP 爬政府站
会被秒封、违反应用商店政策。所以正确拆法是：

```
┌── 采集(自动·免费) ──┐   ┌── 后端(免费) ──┐   ┌── 你用的(手机) ──┐
│ GitHub Actions 定时 │ → │ Supabase        │ → │ Expo App (iOS/   │
│ 跑 Python 采集器    │   │ Postgres+REST   │   │ Android) 看线索  │
│ (每天 09:00)        │   │ +Auth+免费推送  │   │ +高置信推送提醒  │
└─────────────────────┘   └─────────────────┘   └──────────────────┘
   你不用管，自己跑          免费额度够用            你只碰这一层
```

**你要触碰的东西全在手机上**；采集是云端自动化，零维护。三层全部走免费额度。

## 目录结构

```
db/schema.sql              Supabase 建表(signals 信号 / leads 线索)
collector/                 Python 采集器(跑在 GitHub Actions)
  config.py                采集范围：长三角城市 + 新能源/新材料词典 + 关键词
  sources/cninfo.py        P0 数据源：巨潮资讯网公告(免费·结构规整)
  extract.py               正则/词典抽取：金额/城市/行业/事件(零API)
  score.py                 意向打分 + 交叉验证(多源印证乘数)
  store.py                 Supabase PostgREST upsert
  run.py                   主流程入口
.github/workflows/collect.yml   免费定时调度(每天一次)
app/                       Expo(React Native) 手机 App：线索列表/详情/推送
```

## 跑通 MVP（约 30 分钟，全部免费账号）

### 1. 本地试采集（不需要任何账号）
```bash
cd collector
pip install -r requirements.txt
DRY_RUN=1 python run.py        # 直接打印抓到的线索，不写库
```
> 巨潮是境内站点，海外网络可能超时；正式运行在 GitHub Actions(境外但通常可达)上更稳，
> 实在不通可在 config.py 里换更近的源或加代理。

### 2. 建免费后端 Supabase
1. supabase.com 注册 → New Project（免费档：500MB 库 / 5GB 流量 / 自动 REST API）
2. SQL Editor 里粘贴执行 `db/schema.sql`
3. Project Settings → API 抄三个值：
   - `Project URL`、`anon` key（给 App，只读）、`service_role` key（给 CI，可写）
> 免费项目闲置 7 天会暂停 —— 但我们每天定时写库，自然保活。

### 3. 配 GitHub Actions 免费定时采集
1. 把本仓库推到 GitHub
2. Settings → Secrets and variables → Actions 加两个 Secret：
   `SUPABASE_URL`、`SUPABASE_SERVICE_KEY`
3. Actions 页手动点一次 `collect-leads` 跑通；之后每天 09:00 自动跑
> 公开仓库 Actions 分钟数无限；私有仓库每月 2000 分钟，足够。

### 4. 起手机 App
```bash
cd app
npm install
# 把 app.json 里 extra.supabaseUrl / supabaseAnonKey 填上第2步的值
npx expo start          # 手机装 Expo Go 扫码即可预览(iOS/Android)
```
打包成真正可安装的 App：用免费的 EAS（`npx eas build`），免费档可出 iOS/Android 包。

## 打分逻辑（核心）

```
意向分 = Σ( 事件权重 × 时间衰减 ) × 多源印证乘数   (封顶 100)

事件权重  招标采购 1.0 · 投资备案/新建项目 0.9 · 对外投资/选址签约 0.6 · 扩产 0.5 · 资质 0.3
时间衰减  半衰期 180 天(招商讲时效)
印证乘数  1 个独立源 ×1.0 · 2 个 ×1.4 · ≥3 个 ×1.8   ← 交叉验证
状态      ≥70 高置信 · 40~69 待验证 · <40 前置观察
```
转载新闻先按内容指纹去重，避免「一条新闻多站转载」把分数灌高。

## 合规红线（已内建）

- 只采**公开信息**，抽取层过滤掉一切个人手机号/私人邮箱（只留工商公开电话）
- 礼貌抓取：每请求间隔 ≥2s，遵守 robots，错峰低频，不打垮政府站
- 不破解反爬、不碰付费平台反爬接口
- 每条信号都存 `source_url` 证据链，可回溯

## 路线图

- **Phase 1（现在）** 巨潮单源跑通：采集→抽取→打分→App ✅ 本仓库
- **Phase 2** 加招标(公共资源交易中心)+投资备案 → 交叉验证真正生效；接 Expo 推送
- **Phase 3** 加新闻 RSS 预警 + 资质名单打底库；LLM 兜底抽取；按省份/行业扩展
```
