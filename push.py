import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta
import json

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")
today = now.strftime("%Y-%m-%d")
tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

def fetch_wc_games(date):
    games = []
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date}&s=Soccer"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
        for e in (data.get("events") or []):
            league = e.get("strLeague", "")
            if any(k in league for k in ["World Cup", "FIFA", "2026"]):
                hs = e.get("intHomeScore")
                as_ = e.get("intAwayScore")
                status = "已结束" if (hs is not None and as_ is not None) else "未开始"
                score = f"{hs}-{as_}" if status == "已结束" else "vs"
                games.append({
                    "home": e.get("strHomeTeam",""),
                    "away": e.get("strAwayTeam",""),
                    "score": score,
                    "status": status,
                    "time": e.get("strTime",""),
                    "league": league
                })
    except Exception as ex:
        print(f"API获取失败: {ex}")
    return games

def fetch_backup_games(date):
    games = []
    try:
        url = f"https://api.football-data.org/v4/matches?dateFrom={date}&dateTo={date}"
        r = requests.get(url, timeout=10, headers={"X-Auth-Token": "placeholder"})
        if r.status_code == 200:
            for m in (r.json().get("matches") or []):
                if "World Cup" in m.get("competition", {}).get("name", ""):
                    home = m["homeTeam"]["name"]
                    away = m["awayTeam"]["name"]
                    score_h = m.get("score", {}).get("fullTime", {}).get("home")
                    score_a = m.get("score", {}).get("fullTime", {}).get("away")
                    score = f"{score_h}-{score_a}" if score_h is not None else "vs"
                    status = "已结束" if score_h is not None else "未开始"
                    games.append({
                        "home": home, "away": away,
                        "score": score, "status": status,
                        "time": m.get("utcDate","")[:16], "league": "FIFA World Cup"
                    })
    except:
        pass
    return games

today_games = fetch_wc_games(today)
tomorrow_games = fetch_wc_games(tomorrow)

if not today_games:
    today_games = fetch_backup_games(today)
if not tomorrow_games:
    tomorrow_games = fetch_backup_games(tomorrow)

def games_to_text(games):
    if not games:
        return "暂无赛事数据（API暂时无法获取）"
    lines = []
    for g in games:
        lines.append(f"{g['home']} {g['score']} {g['away']} [{g['status']}] {g['time']}")
    return "\n".join(lines)

today_text = games_to_text(today_games)
tomorrow_text = games_to_text(tomorrow_games)

print(f"今日赛事:\n{today_text}")
print(f"明日赛事:\n{tomorrow_text}")

prompt = f"""你是专业世界杯分析师，现在是北京时间 {date_str}。

【真实赛事数据】
今日 ({today}) 赛事：
{today_text}

明日 ({tomorrow}) 赛事：
{tomorrow_text}

近期命中战绩：
象牙海岸1-2挪威✅ | 法国3-0瑞典✅ | 德国1-1巴拉圭⚡冷门 | 荷兰1-1摩洛哥✅ | 巴西2-1日本✅

【任务】
基于以上真实赛事数据，生成完整的2026世界杯数据看盘HTML页面。
如果赛事数据为空，根据2026世界杯真实赛程推断今明两日应有哪些比赛并给出分析。

【每场赛事必须分析】
1. 双方胜率概率（主胜%/平局%/客胜%，三项合计100%）
2. 大小球概率（大2.5球%/小2.5球%）
3. 冷门指数（1-5星）
4. 精推比分3个（主推/次选/保险）
5. 战意轮换简评（2行）
6. 一句话verdict

【HTML设计规格 - 严格执行】

样式：
背景#0A0A0A，卡片#111111，边框#1E1E1E
金色#D2AA5A，文字#E8E0D4，次色#8A8A80
绿#2D9E5F，红#E34948，橙#BA7517，蓝#2a78d6

布局：
- 顶部导航：左侧「⚽ 2026世界杯看盘」标题，右侧实时时钟（JS每秒刷新）
- 统计行：今日场次/进行中/总冷门/命中率 四格卡片
- 今日赛事区
- 每场赛事卡片（规格见下）
- 明日预告区（简版）
- 近期战绩表
- 页脚

赛事卡片规格：
顶部：时间 + 状态badge（进行中红/即将开赛金/已结束灰）
中部：主队[国旗emoji][队名] 大号比分/VS 客队[国旗emoji][队名]
三条胜率进度条（蓝/灰/金，带动画从0增长，各自显示%）
大小球双色bar（绿色大球/红色小球，各显示概率%）
冷门指数：★实心☆空心，冷门高危（≥3星）整卡加红色左边框3px
精推比分：3个圆角badge（蓝主推/灰次选/绿保险）
战意轮换：绿点/红点 + 文字
底部verdict：彩色badge + 总结

技术：
- 最大宽度840px居中
- 卡片border-radius:14px，padding:20px，margin-bottom:12px
- hover时border-color变#D2AA5A，transition:0.2s
- 进度条CSS animation延迟0.3s从width:0增长
- 完全响应式，@media(max-width:640px)字体缩小
- 国旗emoji通过队名智能匹配（法国🇫🇷 英格兰🏴󠁧󠁢󠁥󠁮󠁧󠁿 德国🇩🇪 巴西🇧🇷 阿根廷🇦🇷 西班牙🇪🇸 葡萄牙🇵🇹 荷兰🇳🇱 比利时🇧🇪 美国🇺🇸 墨西哥🇲🇽 日本🇯🇵 挪威🇳🇴 瑞典🇸🇪 摩洛哥🇲🇦 塞内加尔🇸🇳 象牙海岸🇨🇮 刚果金🇨🇩 波黑🇧🇦 巴拉圭🇵🇾 厄瓜多尔🇪🇨 等）
- 不引用任何外部库

只输出完整HTML，从<!DOCTYPE html>开始到</html>结束，不含任何解释文字。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=8000,
    temperature=0.2
)

html = response.choices[0].message.content.strip()

for tag in ["```html", "```HTML", "```"]:
    if tag in html:
        parts = html.split(tag)
        html = parts[1].strip() if len(parts) >= 3 else parts[-1].strip()
        break

idx = html.find("<!DOCTYPE")
if idx > 0:
    html = html[idx:]
elif not html.startswith("<!"):
    idx2 = html.find("<html")
    if idx2 >= 0:
        html = html[idx2:]

os.makedirs("output", exist_ok=True)
with open("output/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 看盘生成成功，字符数：{len(html)}")

today_summary = today_text[:300] if today_text else "暂无数据"
tomorrow_summary = tomorrow_text[:200] if tomorrow_text else "暂无数据"

title = f"⚽ 世界杯看盘更新 · {now.strftime('%m/%d %H:%M')}"
desp = f"""## 看盘已自动更新

**更新时间：** {date_str}

**今日赛事**
{today_summary}

**明日预告**
{tomorrow_summary}

**查看完整看盘**
https://QINZENGHAO.github.io/worldcup-daily/

> 纯属推演，仅供参考娱乐"""

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": desp}
)
print(f"微信推送：{resp.status_code}")
