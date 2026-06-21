"""上海市生态环境局 环评公示 采集 —— 免费、境外可达的独立第二信源。

企业新建/扩建项目动工前必做环评并公示(受理 → 拟审批 → 审批三阶段),是比招标
更早的落地意向信号,且与巨潮(上市公告)互相独立 → 触发交叉验证(高置信 + 印章)。

数据来源:link.sthj.sh.gov.cn 公示列表(hpsl_list_login.jsp)。
  ✅ 实测:**境外出口 IP 直连可达、无登录墙、无限频**(URL 里的 login 是文件名,不是登录要求),
     这正是它优于 ccgp/ggzy 的地方——免费 GitHub Actions(境外)就能稳定跑,不需要境内 IP/代理。
  解析结构若日后改版需微调正则。命中限频/异常时安全返回、不抛错。

source_type='eia',event_type 显式给 '环评公示'(见 score.EVENT_WEIGHTS)。
首期仅上海;江苏/浙江站点可达但版块路径不同,后续补。
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import config
import polite
from config import INDUSTRY_KEYWORDS

# 行业相关性闸:EIA 是全行业的,只留命中新能源/新材料的(滤掉医院/学校/市政道路等非招商目标)
_IND_KWS = tuple({k for kws in INDUSTRY_KEYWORDS.values() for k in kws})


def _relevant(text: str) -> bool:
    return any(k in text for k in _IND_KWS)

BASE = "https://link.sthj.sh.gov.cn/shhj/fa/cms/shhj"
LIST_URL = f"{BASE}/hpsl_list_login.jsp"
PDF_URL = f"{BASE}/hpgs_pdf_login.jsp?fileName="

# 公示阶段:1=受理信息公示(最早/领先信号) 2=拟审批公示
GONGSHI_TYPES = (1, 2)
# 申报类型:1=环境影响报告书 2=环境影响报告表
APPROV_TYPES = (1, 2)

_ROW = re.compile(r'<tr height="79">(.*?)</tr>', re.S)
_TITLE = re.compile(r'title="([^"]*)"')
_PDF = re.compile(r"openPdf\('([^']+)'\)")
_DATE = re.compile(r"(20\d{2})-(\d{1,2})-(\d{1,2})")


def _parse(html: str):
    """每行结构:项目名称(td title + openPdf) | 建设单位(td title) | 公示时间(起~止)。"""
    for row in _ROW.finditer(html):
        block = row.group(1)
        titles = _TITLE.findall(block)
        if len(titles) < 3:
            continue
        project, company, date_range = (titles[0].strip(), titles[1].strip(), titles[2].strip())
        if not company:
            continue
        dm = _DATE.search(date_range)          # 取公示开始日作为发布日
        pub = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else None
        pm = _PDF.search(block)
        url = (PDF_URL + pm.group(1)) if pm else f"{LIST_URL}?applyItem=1"
        yield project, company, pub, url


def search(lookback_days: int, max_pages: int):
    """拉上海环评受理/拟审批公示,yield 与 cninfo 对齐的 dict。"""
    cutoff = date.today() - timedelta(days=lookback_days)
    with polite.client("https://sthj.sh.gov.cn/", timeout=25.0) as cli:
        for gs in GONGSHI_TYPES:
            for ap in APPROV_TYPES:
                for page in range(1, max_pages + 1):
                    params = {"applyItem": 1, "gongshiType": gs, "approvType": ap, "pageNo": page}
                    try:
                        r = cli.get(LIST_URL, params=params)
                        html = r.text
                    except Exception as e:  # noqa: BLE001
                        print(f"[eia] 上海 gs{gs}/ap{ap} p{page} 失败: {e}")
                        break
                    if r.status_code != 200 or "访问过于频繁" in html or "频繁访问" in html:
                        print("[eia] 上海 被限频/异常,跳过")
                        return
                    rows = list(_parse(html))
                    if not rows:
                        break
                    for project, company, pub, url in rows:
                        if not _relevant(project + company):   # 只收新能源/新材料相关
                            continue
                        if pub:
                            try:
                                if date.fromisoformat(pub) < cutoff:
                                    continue
                            except ValueError:
                                pass
                        yield {
                            "source_type": "eia",
                            "company_name_raw": company,
                            "title": project,
                            "source_url": url,
                            "published_at": pub,
                            "province": "上海",
                            "event_type": "环评公示",   # 显式事件类型(项目级,见 score.py)
                        }
                    polite.nap(config)
