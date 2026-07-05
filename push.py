import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
RAPIDAPI_KEY = os.environ["RAPIDAPI_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")
today = now.strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

LEAGUES = {
    "世界杯": (1, 2026),
    "韩K联": (292, 2026),
    "韩K2联": (293, 2026),
}

def get_fixtures(league_id, season):
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        params = {"league": league_id, "season": season, "date": today, "timezone": "Asia/Shanghai"}
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = r.json()
        results = []
        for f in data.get("response", []):
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            status = f["fixture"]["status"]["short"]
            hs = f["goals"]["home"]
            as_ = f["goals"]["away"]
            t = f["fixture"]["date"][11:16]
            if status == "FT":
                results.append(home + " " + str(hs) + "-" + str(as_) + " " + away + " [已结束]")
            elif status in ["1H","2H","HT"]:
                results.append(home + " " + str(hs) + "-" + str(as_) + " " + away + " [进行中]")
            else:
                results.append(home + " vs " + away + " [" + t + "开踢]")
        return results
    except Exception as ex:
        print("API错误: " + str(ex))
        return []

def get_odds(league_id, season):
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/odds"
        params = {"league": league_id, "season": season, "date": today, "bookmaker": 6}
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = r.json()
        results = []
        for item in data.get("response", []):
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            bets = item.get("bookmakers", [{}])[0].get("bets", []) if item.get("bookmakers") else []
            parts = []
            for bet in bets:
                if bet["name"] == "Match Winner":
                    vals = {v["value"]: v["odd"] for v in bet["values"]}
                    parts.append("欧赔 主" + str(vals.get("Home","?")) + " 平" + str(vals.get("Draw","?")) + " 客" + str(vals.get("Away","?")))
                if bet["name"] == "Goals Over/Under":
                    vals = {v["value"]: v["odd"] for v in bet["values"]}
                    parts.append("大2.5@" + str(vals.get("Over 2.5","?")) + " 小2.5@" + str(vals.get("Under 2.5","?")))
            if home and away and parts:
                results.append(home + " vs " + away + ": " + " | ".join(parts))
        return results
    except Exception as ex:
        print("赔率错误: " + str(ex))
        return []

all_fixtures = {}
all_odds = {}

for name, (lid, season) in LEAGUES.items():
    fx = get_fixtures(lid, season)
    if fx:
        all_fixtures[name] = fx
        print(name + ": " + str(len(fx)) + "场")
        od = get_odds(lid, season)
        if od:
            all_odds[name] = od

fixtures_text = ""
for name, fx in all_fixtures.items():
    fixtures_text += "\n[" + name + "]\n" + "\n".join(fx)

odds_text = ""
for name, od in all_odds.items():
    odds_text += "\n[" + name + "赔率]\n" + "\n".join(od)

if not fixtures_text:
    fixtures_text = "今日暂无赛事数据"
if not odds_text:
    odds_text = "今日暂无赔率数据"

print("赛事数据:" + fixtures_text[:300])
print("赔率数据:" + odds_text[:300])

analysis_prompt = "你是顶级足球盘口分析师。现在北京时间 " + date_str + "。\n\n"
analysis_prompt += "今日赛事:\n" + fixtures_text + "\n\n"
analysis_prompt += "赔率数据:\n" + odds_text + "\n\n"
analysis_prompt += "已验证规律:\n"
analysis_prompt += "1.水位接近1.00则比分偏小\n"
analysis_prompt += "2.弱队赔率小于10必须考虑进球\n"
analysis_prompt += "3.防守型球队面对弱队可能大球爆发\n"
analysis_prompt += "4.强队深度轮换进球期望降至1.5球以下\n\n"
analysis_prompt += "请生成完整专业盘口看盘HTML页面，每场包含:\n"
analysis_prompt += "1.欧赔真实概率(去除抽水)\n"
analysis_prompt += "2.亚盘水位信号解读\n"
analysis_prompt += "3.大小球分析\n"
analysis_prompt += "4.精准比分三选(主推/次选/保险+概率)\n"
analysis_prompt += "5.冷门指数(星级)\n"
analysis_prompt += "6.综合verdict一句话\n\n"
analysis_prompt += "HTML设计要求:\n"
analysis_prompt += "背景#080B0F 卡片#0D1117 金色#F0B429\n"
analysis_prompt += "文字#E6EDF3 绿#3FB950 红#F85149\n"
analysis_prompt += "胜率进度条动画 大小球双色条\n"
analysis_prompt += "冷门高危红色左边框 实时时钟\n"
analysis_prompt += "完全响应式 零外部依赖\n"
analysis_prompt += "只输出完整HTML从DOCTYPE开始无任何解释"

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": analysis_prompt}],
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
elif not html.startswith("<!"):
    idx2 = html.find("<html")
    if idx2 >= 0:
        html = html[idx2:]

os.makedirs("output", exist_ok=True)
with open("output/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("生成成功，字符数:" + str(len(html)))
