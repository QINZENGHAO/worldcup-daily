import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]
RAPIDAPI_KEY = os.environ["RAPIDAPI_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")
today = now.strftime("%Y-%m-%d")
tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com"
}

def get_wc_fixtures(date):
    games = []
    try:
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        r = requests.get(url, headers=HEADERS, params={"date": date}, timeout=15)
        data = r.json()
        print(f"API响应({date}): {str(data)[:200]}")
        matches = data.get("response", {})
        if isinstance(matches, list):
            items = matches
        elif isinstance(matches, dict):
            items = matches.get("matches", []) or matches.get("fixtures", []) or []
        else:
            items = []

        for m in items:
            league_name = (
                m.get("league", {}).get("name", "") or
                m.get("competition", {}).get("name", "") or
                m.get("tournament", {}).get("name", "") or ""
            )
            if not any(k in league_name for k in ["World Cup", "FIFA", "2026", "mundial"]):
                continue
            home = (m.get("home", {}) or m.get("homeTeam", {})).get("name", "")
            away = (m.get("away", {}) or m.get("awayTeam", {})).get("name", "")
            if not home or not away:
                continue
            score_h = (m.get("score", {}) or {}).get("home") or (m.get("goals", {}) or {}).get("home")
            score_a = (m.get("score", {}) or {}).get("away") or (m.get("goals", {}) or {}).get("away")
            status_raw = m.get("status", {})
            if isinstance(status_raw, dict):
                status_str = status_raw.get("long", "") or status_raw.get("short", "")
            else:
                status_str = str(status_raw)
            if score_h is not None and score_a is not None:
                status = "已结束"
                score = f"{score_h}-{score_a}"
            elif "progress" in status_str.lower() or "live" in status_str.lower():
                status = "进行中"
                score = f"{score_h or 0}-{score_a or 0}"
            else:
                status = "未开始"
                score = "vs"
            time_raw = m.get("time", "") or m.get("fixture", {}).get("date", "")[:16] or ""
            games.append({
                "home": home, "away": away,
                "score": score, "status": status,
                "time": time_raw, "league": league_name
            })
    except Exception as ex:
        print(f"API获取失败({date}): {ex}")
    return games

def get_wc_fixtures_backup(date):
    games = []
    try:
        url = "https://free-api-live-football-data.p.rapidapi.com/football-current-live"
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        print(f"备用API响应: {str(data)[:300]}")
        items = data.get("response", [])
        if isinstance(items, dict):
            items = items.get("matches", []) or []
        for m in (items or []):
            league_name = m.get("league", {}).get("name", "") or ""
            if any(k in league_name for k in ["World Cup", "FIFA", "2026"]):
                home = m.get("home", {}).get("name", "")
                away = m.get("away", {}).get("name", "")
                sh = m.get("score", {}).get("home")
                sa = m.get("score", {}).get("away")
                games.append({
                    "home": home, "away": away,
                    "score": f"{sh}-{sa}" if sh is not None else "vs",
                    "status": "进行中" if sh is not None else "未开始",
                    "time": "实时", "league": league_name
                })
    except Exception as ex:
        print(f"备用API失败: {ex}")
    return games

today_games = get_wc_fixtures(today)
tomorrow_games = get_wc_fixtures(tomorrow)

if not today_games:
    print("主API无数据，尝试备用接口...")
    today_games = get_wc_fixtures_backup(today)

if not today_games and not tomorrow_games:
    print("所有API无数据，使用赛程推断模式")

def games_to_text(games):
    if not games:
        return "API暂无数据，将基于2026世界杯真实赛程推断"
    lines = []
    for g in games:
        lines.append(
            f"{g['home']} {g['score']} {g['away']}"
            f" [{g['status']}]"
            f"{' ' + g['time'] if g['time'] else ''}"
        )
    return "\n".join(lines)

today_text = games_to_text(today_games)
tomorrow_text = games_to_text(tomorrow_games)

print(f"\n今日赛事:\n{today_text}")
print(f"\n明日赛事:\n{tomorrow_text}")

flag_map = {
    "France":"🇫🇷","England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Germany":"🇩🇪","Brazil":"🇧🇷",
    "Argentina":"🇦🇷","Spain":"🇪🇸","Portugal":"🇵🇹","Netherlands":"🇳🇱",
    "Belgium":"🇧🇪","USA":"🇺🇸","Mexico":"🇲🇽","Japan":"🇯🇵",
    "Norway":"🇳🇴","Sweden":"🇸🇪","Morocco":"🇲🇦","Senegal":"🇸🇳",
    "Ivory Coast":"🇨🇮","Congo DR":"🇨🇩","Bosnia":"🇧🇦","Paraguay":"🇵🇾",
    "Ecuador":"🇪🇨","Croatia":"🇭🇷","Switzerland":"🇨🇭","Austria":"🇦🇹",
    "Algeria":"🇩🇿","Colombia":"🇨🇴","Ghana":"🇬🇭","Canada":"🇨🇦",
    "Australia":"🇦🇺","South Africa":"🇿🇦","Jordan":"🇯🇴","Uruguay":"🇺🇾",
    "Turkey":"🇹🇷","South Korea":"🇰🇷","Iraq":"🇮🇶","Cape Verde":"🇨🇻",
    "New Zealand":"🇳🇿","Egypt":"🇪🇬","Iran":"🇮🇷","Uzbekistan":"🇺🇿",
    "Ghana":"🇬🇭","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","法国":"🇫🇷","德国":"🇩🇪",
    "巴西":"🇧🇷","阿根廷":"🇦🇷","西班牙":"🇪🇸","葡萄牙":"🇵🇹",
    "荷兰":"🇳🇱","比利时":"🇧🇪","美国":"🇺🇸","墨西哥":"🇲🇽",
    "日本":"🇯🇵","挪威":"🇳🇴","瑞典":"🇸🇪","摩洛哥":"🇲🇦",
    "塞内加尔":"🇸🇳","象牙海岸":"🇨🇮","刚果(金)":"🇨🇩","波黑":"🇧🇦",
    "巴拉圭":"🇵🇾","厄瓜多尔":"🇪🇨","克罗地亚":"🇭🇷","瑞士":"🇨🇭",
    "奥地利":"🇦🇹","阿尔及利亚":"🇩🇿","哥伦比亚":"🇨🇴","加纳":"🇬🇭",
    "加拿大":"🇨🇦","澳大利亚":"🇦🇺","南非":"🇿🇦","约旦":"🇯🇴",
    "乌拉圭":"🇺🇾","土耳其":"🇹🇷","韩国":"🇰🇷","伊拉克":"🇮🇶",
    "佛得角":"🇨🇻","新西兰":"🇳🇿","埃及":"🇪🇬","伊朗":"🇮🇷",
    "乌兹别克斯坦":"🇺🇿"
}

prompt = f"""你是2026世界杯专业分析师，现在是北京时间 {date_str}。

【真实赛事数据】
今日 ({today})：
{today_text}

明日 ({tomorrow})：
{tomorrow_text}

近期命中战绩：
- 象牙海岸1-2挪威 ✅
- 法国3-0瑞典 ✅
- 德国1-1巴拉圭 ⚡冷门
- 荷兰1-1摩洛哥 ✅
- 巴西2-1日本 ✅
- 英格兰3-0刚果(金) ✅
- 美国2-0波黑 ✅

【任务】
基于以上真实数据，生成完整的2026世界杯数据看盘HTML页面。
若API数据为空，根据2026世界杯真实赛程推断今明两日赛事并分析。

每场赛事必须给出：
1. 双方胜率概率（主胜%/平局%/客胜%，合计100%）
2. 大小球（大2.5球%/小2.5球%）
3. 冷门指数（1-5★）
4. 精推比分（主推/次选/保险）
5. 战意轮换简评
6. 一句话verdict

国旗对照：{str(flag_map)}

【HTML规格】
配色：背景#0A0A0A 卡片#111111 边框#1E1E1E
金色#D2AA5A 文字#E8E0D4 次色#8A8A80
绿#2D9E5F 红#E34948 橙#BA7517 蓝#2a78d6

布局：
1. 顶部导航（左标题+右实时时钟）
2. 统计四格（今日场次/进行中/冷门数/命中率）
3. 今日赛事大卡片
4. 明日预告小卡片
5. 近期战绩表
6. 页脚免责

每张赛事卡片：
- 顶部时间+状态badge
- 主队emoji+名 大号比分/VS 客队名+emoji
- 三条胜率进度条（蓝主胜/灰平局/金客胜）含动画
- 大小球双色条（绿大球/红小球）
- 冷门星级★☆☆
- 精推比分3个badge
- 战意轮换2行（●绿/●红）
- verdict条

冷门≥3★的卡片左边框3px红色
进行中的卡片左边框3px绿色

技术要求：
- 最大宽度840px居中
- border-radius:14px padding:20px
- hover border-color:#D2AA5A transition:0.2s
- 进度条CSS animation 0.8s ease-out
- 响应式@media(max-width:640px)
- 实时时钟JS每秒刷新
- 无外部依赖

只输出完整HTML，<!DOCTYPE html>开始，</html>结束，无任何解释。"""

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
        html = (parts[1] if len(parts) >= 3 else parts[-1]).strip()
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

title = f"⚽ 世界杯看盘更新 · {now.strftime('%m/%d %H:%M')}"
desp = f"""## 看盘已自动更新

**更新时间：** {date_str}

**今日赛事**
{today_text[:400]}

**明日预告**
{tomorrow_text[:200]}

**查看完整看盘**
https://QINZENGHAO.github.io/worldcup-daily/

> 纯属推演，仅供参考娱乐"""

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": desp}
)
print(f"微信推送：{resp.status_code}")
