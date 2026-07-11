import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
ODDS_API_KEY = os.environ["ODDS_API_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y-%m-%d %H:%M")
today = now.strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

# 北单覆盖联赛
SPORTS = [
    "soccer_world_cup",
    "soccer_south_korea_k_league_1",
    "soccer_south_korea_k_league_2",
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_norway_eliteserien",
    "soccer_sweden_allsvenskan",
    "soccer_finland_veikkausliiga",
    "soccer_ireland_premier_division",
    "soccer_denmark_superliga",
    "soccer_belgium_first_div",
    "soccer_netherlands_eredivisie",
    "soccer_usa_mls",
    "soccer_japan_j_league",
    "soccer_brazil_campeonato",
]

SPORT_NAMES = {
    "soccer_world_cup": "世界杯",
    "soccer_south_korea_k_league_1": "韩K联",
    "soccer_south_korea_k_league_2": "韩K2联",
    "soccer_epl": "英超",
    "soccer_spain_la_liga": "西甲",
    "soccer_germany_bundesliga": "德甲",
    "soccer_italy_serie_a": "意甲",
    "soccer_france_ligue_one": "法甲",
    "soccer_norway_eliteserien": "挪超",
    "soccer_sweden_allsvenskan": "瑞典超",
    "soccer_finland_veikkausliiga": "芬超",
    "soccer_ireland_premier_division": "爱超",
    "soccer_denmark_superliga": "丹超",
    "soccer_belgium_first_div": "比甲",
    "soccer_netherlands_eredivisie": "荷甲",
    "soccer_usa_mls": "MLS",
    "soccer_japan_j_league": "日职联",
    "soccer_brazil_campeonato": "巴西甲",
}

def get_odds(sport):
    try:
        url = "https://api.the-odds-api.com/v4/sports/" + sport + "/odds/"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu,asia",
            "markets": "h2h,asian_handicap,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            print(sport + " 错误: " + str(r.status_code))
            return []
        data = r.json()
        results = []
        for game in data:
            home = game.get("home_team", "")
            away = game.get("away_team", "")
            commence = game.get("commence_time", "")
            try:
                utc_time = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                bj_time = utc_time.astimezone(tz)
                if bj_time.strftime("%Y-%m-%d") != today:
                    continue
                time_str = bj_time.strftime("%H:%M")
            except:
                continue

            h2h = ""
            asian = ""
            total = ""
            for bk in game.get("bookmakers", []):
                for market in bk.get("markets", []):
                    if market["key"] == "h2h" and not h2h:
                        vals = {o["name"]: o["price"] for o in market["outcomes"]}
                        h2h = "欧赔 主" + str(vals.get(home, "?")) + " 平" + str(vals.get("Draw", "?")) + " 客" + str(vals.get(away, "?"))
                    if market["key"] == "asian_handicap" and not asian:
                        outs = market["outcomes"][:2] if market["outcomes"] else []
                        if len(outs) >= 2:
                            asian = "亚盘 " + str(outs[0].get("point","")) + "@" + str(outs[0].get("price","")) + " / " + str(outs[1].get("point","")) + "@" + str(outs[1].get("price",""))
                    if market["key"] == "totals" and not total:
                        vals = {o["name"]: o["price"] for o in market["outcomes"]}
                        total = "大小球 大@" + str(vals.get("Over","?")) + " 小@" + str(vals.get("Under","?"))

            if home and (h2h or asian):
                line = time_str + " | " + home + " vs " + away
                if h2h: line += " | " + h2h
                if asian: line += " | " + asian
                if total: line += " | " + total
                results.append(line)
        return results
    except Exception as e:
        print(sport + " 异常: " + str(e))
        return []

print("开始拉取数据: " + date_str)
all_matches = []
total_games = 0

for sport in SPORTS:
    name = SPORT_NAMES.get(sport, sport)
    matches = get_odds(sport)
    if matches:
        all_matches.append("")
        all_matches.append("=== " + name + " ===")
        all_matches.extend(matches)
        total_games += len(matches)
        print(name + ": " + str(len(matches)) + "场")

print("今日总场次: " + str(total_games))
data_text = "\n".join(all_matches) if all_matches else "今日暂无赛事数据"
print("\n数据预览:\n" + data_text[:500])

# 已验证规律（48场）
rules = """
已验证核心规律（48场验证）：
1. 大小球66.7%最可靠，优先判断
2. 弱队欧赔<10必须考虑进球（100%验证）
3. 平局概率>30%且排名差距<5位→主推平局
4. 让球高赔率>3.5→极强警示，客队或平局
5. 强热门赔率<2.0面对弱队→大比分可能
6. 主场优势所有联赛均+15%
7. 变盘信号不可盲目跟随，实力才是根本
8. 亚盘水位>1.00→比分偏小
9. 欧战主场爆发力极强→优先押主队
10. 弱队进球可达1-3球，不只是1球
"""

msg = "你是顶级足球盘口分析师，精通欧亚盘水位解读。现在北京时间 " + date_str + "\n\n"
msg += "今日所有赛事完整盘口数据:\n" + data_text + "\n\n"
msg += rules + "\n\n"
msg += "请生成完整专业HTML足球北单看盘页面。\n\n"
msg += "每场比赛必须包含:\n"
msg += "1. 联赛标签+开赛时间\n"
msg += "2. 球队名称\n"
msg += "3. 欧赔真实概率（去除抽水后反推，公式：真实概率=1/赔率/总超额）\n"
msg += "4. 三方胜率彩色进度条（主队蓝/平局灰/客队金，CSS动画）\n"
msg += "5. 亚盘让球分析（让球方向+水位信号强弱）\n"
msg += "6. 大小球分析（盘口线+大小概率%）\n"
msg += "7. 精准比分三选: 主推/次选/保险（含概率%）\n"
msg += "8. 冷门指数（★☆1-5星）\n"
msg += "9. 一句话verdict总结\n\n"
msg += "页面设计要求:\n"
msg += "- 背景#080B0F 卡片#0D1117 边框#21262D\n"
msg += "- 金色#F0B429 绿#3FB950 红#F85149 蓝#58A6FF\n"
msg += "- 顶部: 标题「今日北单看盘」+ 实时北京时间（JS每秒刷新）\n"
msg += "- 顶部统计栏: 今日X场 / 平局推荐X场 / 大球推荐X场 / 冷门预警X场\n"
msg += "- 按联赛分组，每组有彩色联赛标题\n"
msg += "- 三方胜率进度条CSS动画（0.8s ease-out从0增长）\n"
msg += "- 冷门3星以上红色左边框3px\n"
msg += "- 世界杯场次金色左边框突出\n"
msg += "- 最大宽度960px居中\n"
msg += "- 手机完全响应式\n"
msg += "- 零外部依赖\n"
msg += "- 页面底部显示数据更新时间和API来源\n\n"
msg += "只输出完整HTML从<!DOCTYPE html>开始，无任何解释文字。"

print("\n开始生成AI分析...")
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": msg}],
    max_tokens=8000,
    temperature=0.1
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

os.makedirs("output", exist_ok=True)
with open("output/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("生成完成！字符数: " + str(len(html)))
print("今日分析场次: " + str(total_games))
