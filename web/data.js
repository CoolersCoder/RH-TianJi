// 访问门:没在 splash 输过密码的,弹回 splash。各 app 页都引了 data.js,故守卫集中放这。
// 注意:这是「软门」——挡住随手浏览,但不是真安全(密码在前端源码可见,数据本就公开只读)。
if (localStorage.getItem("xianji_auth") !== "1") {
  location.replace("splash.html");
}

// 先机 · 数据层：浏览器直连 Supabase REST(publishable key 只读，受 RLS 保护，可安全放前端)。
const SUPABASE_URL = "https://ajnwlvbrhytbipjgmbpv.supabase.co";
const SUPABASE_ANON = "sb_publishable_hUBM2xQ00HBk_obzou0ozQ_NQiEobvT";
const SB_HEADERS = { apikey: SUPABASE_ANON, Authorization: "Bearer " + SUPABASE_ANON };

async function sbGet(path) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, { headers: SB_HEADERS });
  if (!r.ok) throw new Error(`Supabase ${r.status}: ${await r.text()}`);
  return r.json();
}

// ── 查询 ────────────────────────────────────────────────────────────
function fetchLeads(filter = {}) {
  let q = "leads?select=*&order=intent_score.desc&limit=100";
  if (filter.industry) q += `&top_industry=eq.${encodeURIComponent(filter.industry)}`;
  if (filter.minScore) q += `&intent_score=gte.${filter.minScore}`;
  if (filter.sort === "latest") q = q.replace("order=intent_score.desc", "order=last_active.desc.nullslast");
  return sbGet(q);
}
async function fetchLeadBundle(companyKey) {
  const k = encodeURIComponent(companyKey);
  const [leads, signals] = await Promise.all([
    sbGet(`leads?company_key=eq.${k}&limit=1`),
    sbGet(`signals?company_key=eq.${k}&select=source_type,event_type,title,source_url,amount_wan,location_city,industry,published_at&order=published_at.desc.nullslast`),
  ]);
  return { lead: leads[0], signals };
}

// ── 展示映射 ─────────────────────────────────────────────────────────
// 意向分热度：≥70 朱砂/高置信 · ≥40 黄铜/待验证 · 其余 岩/前置观察
function scoreMeta(score) {
  if (score >= 70) return { color: "primary", status: "高置信", pill: "bg-primary-soft text-primary" };
  if (score >= 40) return { color: "brass", status: "待验证", pill: "bg-brass-soft text-brass" };
  return { color: "rock", status: "前置观察", pill: "bg-surface-variant text-rock" };
}

// 签名元素「信源印证条」：独立来源越多亮起越多；≥3 盖朱砂"先"印章
function sourceBar(distinct) {
  const lit = Math.max(0, Math.min(5, distinct || 0));
  let dots = "";
  for (let i = 0; i < 5; i++)
    dots += `<div class="w-1.5 h-1.5 ${i < lit ? "bg-jade" : "bg-surface-variant"} rounded-sm"></div>`;
  const seal = lit >= 3
    ? `<div class="w-4 h-4 ml-1 rounded-full bg-primary flex items-center justify-center text-white shadow-sm"><span class="text-[8px] font-bold leading-none">先</span></div>`
    : "";
  return `<div class="flex items-center gap-1">${dots}${seal}</div>`;
}

const SOURCE_LABEL = {
  listed_announce: { t: "上市公告", icon: "description" },
  eia:             { t: "环评公示", icon: "eco" },
  tender:          { t: "招标",     icon: "gavel" },
  invest_record:   { t: "投资备案", icon: "verified" },
  news:            { t: "新闻",     icon: "newspaper" },
  qualification:   { t: "资质",     icon: "workspace_premium" },
  gov_project:     { t: "政府项目", icon: "account_balance" },
};
function industryIcon(ind) {
  if (ind === "新能源") return "factory";
  if (ind === "新材料") return "science";
  if (ind === "医药") return "medical_services";
  return "business";
}
function yi(wan) { return wan ? `${(wan / 10000).toFixed(wan % 10000 ? 1 : 0)}亿` : null; }

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  if (days <= 0) return "今天";
  if (days === 1) return "昨天";
  if (days < 30) return `${days}天前`;
  return dateStr;
}

// 城市/省 → 省份(态势"省份分布"按省聚合用)。top_location 现在多为市级(常州/淮安/宁波)。
const CITY_PROV = (() => {
  const m = { 上海: "上海", 江苏: "江苏", 浙江: "浙江", 安徽: "安徽" };
  "南京 苏州 无锡 常州 南通 徐州 盐城 扬州 镇江 泰州 淮安 连云港 宿迁".split(" ").forEach(c => m[c] = "江苏");
  "杭州 宁波 温州 嘉兴 湖州 绍兴 金华 衢州 舟山 台州 丽水".split(" ").forEach(c => m[c] = "浙江");
  "合肥 芜湖 蚌埠 马鞍山 滁州 安庆 宣城 铜陵 六安 宿州 阜阳 亳州 池州 黄山 淮南 淮北".split(" ").forEach(c => m[c] = "安徽");
  return m;
})();
function provinceOf(loc) {
  if (!loc) return "未标注";
  if (CITY_PROV[loc]) return CITY_PROV[loc];          // 市级/省级直接命中
  for (const p of ["上海", "江苏", "浙江", "安徽"])     // 兼容旧格式 "江苏淮安"/"上海上海"
    if (loc.startsWith(p)) return p;
  return loc;
}

function chip(icon, text) {
  return `<span class="px-2.5 py-1 bg-surface-container-low text-rock text-[12px] rounded-md border-hairline inline-flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">${icon}</span>${text}</span>`;
}

// 紧凑行(搜索结果 / 热门企业 / 关注清单复用)：分数 + 衬线名 + 城市行业 + 状态胶囊
function compactRow(l) {
  const m = scoreMeta(l.intent_score);
  return `<div onclick="location.href='lead.html?key=${encodeURIComponent(l.company_key)}'"
    class="bg-surface border-hairline card-soft rounded-2xl flex items-center gap-3 p-4 cursor-pointer hover:-translate-y-px transition-transform">
    <span class="font-data-mono text-[22px] font-bold text-${m.color} w-9 text-center flex-shrink-0 leading-none">${l.intent_score}</span>
    <div class="flex-1 min-w-0">
      <div class="font-headline-sm font-semibold text-on-surface truncate">${l.company_name}</div>
      <div class="text-[12px] text-rock truncate">${[l.top_location, l.top_industry].filter(Boolean).join(" · ") || "—"}</div>
    </div>
    <span class="text-[11px] px-2.5 py-1 rounded-md ${m.pill} flex-shrink-0">${m.status}</span>
  </div>`;
}

// 信源类型 → 软底配色(对齐参考)
const SOURCE_TINT = {
  listed_announce: "bg-primary-soft text-primary",
  eia:             "bg-jade-soft text-jade",
  tender:          "bg-brass-soft text-brass",
  invest_record:   "bg-jade-soft text-jade",
  gov_project:     "bg-jade-soft text-jade",
  news:            "bg-surface-variant text-rock",
  qualification:   "bg-[#eae6f0] text-[#5a4a7a]",
};

// 按企业名搜索
function searchLeads(term) {
  return sbGet(`leads?company_name=ilike.*${encodeURIComponent(term)}*&order=intent_score.desc&limit=50`);
}

// 关注/跟进清单：免登录，存浏览器本地(localStorage)
const WATCH_KEY = "xianji_watch";
const STAGES = ["待联系", "已联系", "已对接", "已签约", "已搁置"];
function getWatch() { try { return JSON.parse(localStorage.getItem(WATCH_KEY)) || []; } catch (e) { return []; } }
function isWatched(k) { return getWatch().some(x => x.company_key === k); }
function toggleWatch(lead) {
  let w = getWatch();
  if (w.some(x => x.company_key === lead.company_key)) {
    w = w.filter(x => x.company_key !== lead.company_key);
  } else {
    w.unshift({
      company_key: lead.company_key, company_name: lead.company_name,
      intent_score: lead.intent_score, top_location: lead.top_location,
      top_industry: lead.top_industry, stage: "待联系",
    });
  }
  localStorage.setItem(WATCH_KEY, JSON.stringify(w));
  return isWatched(lead.company_key);
}
function setStage(k, stage) {
  const w = getWatch(), it = w.find(x => x.company_key === k);
  if (it) { it.stage = stage; localStorage.setItem(WATCH_KEY, JSON.stringify(w)); }
}

// 统一底部导航(各页复用，传入当前激活页) —— 4 tab，激活态朱砂红填充
function bottomNav(active) {
  const tabs = [
    ["index.html", "bar_chart", "线索"],
    ["situation.html", "show_chart", "态势"],
    ["follow.html", "bookmark", "关注"],
    ["settings.html", "person", "我"],
  ];
  return `<nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-[68px] px-4 bg-surface/90 backdrop-blur-xl border-t border-outline-variant" style="padding-bottom:env(safe-area-inset-bottom)">${
    tabs.map(([href, icon, label]) => {
      const on = href === active;
      return `<a class="flex flex-col items-center justify-center gap-1 w-16 ${on ? "text-primary" : "text-rock"}" href="${href}"><span class="material-symbols-outlined text-[24px]" ${on ? "style=\"font-variation-settings:'FILL' 1;\"" : ""}>${icon}</span><span class="text-[10px] tracking-wide ${on ? "font-semibold" : ""}">${label}</span></a>`;
    }).join("")
  }</nav>`;
}

// 一张线索卡 —— 左轨：分数+状态；右体：衬线公司名 / 印证摘要 / 行业·城市 + 金额 + 时间
function leadCardHTML(l) {
  const m = scoreMeta(l.intent_score);
  const distinct = l.distinct_sources || 0;
  const summary = l.summary || l.latest_title ||
    `${l.signal_count || 0} 条公开信号 · ${distinct} 个独立信源印证`;
  const amount = yi(l.max_amount_wan);
  const meta = [l.top_industry, l.top_location].filter(Boolean).join(" · ");
  const seal = distinct >= 3
    ? `<span class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-primary text-white text-[8px] font-bold flex-shrink-0" title="≥3 独立信源印证">先</span>`
    : "";
  return `
  <article onclick="location.href='lead.html?key=${encodeURIComponent(l.company_key)}'"
    class="bg-surface rounded-2xl border-hairline card-soft flex overflow-hidden cursor-pointer hover:-translate-y-px transition-transform">
    <div class="flex flex-col items-center justify-center w-[70px] flex-shrink-0 py-4 border-r-hairline">
      <span class="font-data-mono text-[30px] leading-none font-bold text-${m.color}">${l.intent_score}</span>
      <span class="text-[10px] mt-1.5 font-medium tracking-wide text-${m.color}">${m.status}</span>
    </div>
    <div class="flex-1 min-w-0 p-4 flex flex-col gap-2">
      <h3 class="font-headline-sm font-semibold text-on-surface truncate">${l.company_name}</h3>
      <p class="text-body-md text-rock leading-relaxed line-clamp-2">${summary}</p>
      <div class="flex items-center justify-between gap-2 mt-0.5">
        <div class="flex items-center gap-2 min-w-0">
          ${seal}<span class="text-[12px] text-rock truncate">${meta}</span>
          ${amount ? `<span class="px-2 py-0.5 rounded-md bg-brass-soft text-brass text-[11px] font-data-mono font-medium flex-shrink-0">投资${amount}</span>` : ""}
        </div>
        <span class="font-label-caps text-rock/70 whitespace-nowrap flex-shrink-0">${timeAgo(l.last_active)}</span>
      </div>
    </div>
  </article>`;
}
