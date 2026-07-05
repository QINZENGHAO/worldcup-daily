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
tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

def get_fixtures(league_id, season=2026):
    """拉取指定联赛今日赛事"""
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        params = {
            "league": league_id,
            "season": season,
            "date": today,
            "timezone": "Asia/Shanghai"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = r.json()
        fixtures = data.get("response", [])
        results = []
        for f in fixtures:
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            status = f["fixture"]["status"]["short"]
            home_score = f["goals"]["home"]
            away_score = f["goals"]["away"]
            time_str = f["fixture"]["date"][11:16]

            if status == "FT":
                results.append(f"{home} {home_score}–{away_score} {away} [已结束]")
            elif status in ["1H","2H","HT","ET","P"]:
                results.append(f"{home} {home_score}–{away_score} {away} [进行中]")
            else:
                results.append(f"{home} vs {away} [{time_str}开踢]")
        return results
    except Exception as ex:
        print(f"API错误: {ex}")
        return []

def get_odds(league_id, season=2026):
    """拉取指定联赛今日赔率"""
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/odds"
        params = {
            "league": league_id,
            "season": season,
            "date": today,
            "bookmaker": 6
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = r.json()
        odds_list = data.get("response", [])
        results = []
        for item in odds_list:
            fixture = item.get("fixture", {})
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            bets = item.get("bookmakers", [{}])[0].get("bets", [])
            odds_str = ""
            for bet in bets:
                if bet["name"] == "Match Winner":
                    vals = {v["value"]: v["odd"] for v in bet["values"]}
                    odds_str = f"欧赔 主{vals.get('Home','?')} 平{vals.get('Draw','?')} 客{vals.get('Away','?')}"
                if bet["name"] == "Asian Handicap":
                    vals = bet["values"][:2] if bet["values"] else []
                    if vals:
                        odds_str += f" | 亚盘 {vals[0].get('value','')}@{vals[0].get('odd','')} {vals[1].get('value','')}@{vals[1].get('odd','')}"
                if bet["name"] == "Goals Over/Under":
                    vals = {v["value"]: v["odd"] for v in bet["values"]}
                    odds_str += f" | 大小球 大2.5@{vals.get('Over 2.5','?')} 小2.5@{vals.get('Under 2.5','?')}"
            if home and away:
                results.append(f"{home} vs {away}: {odds_str}")
        return results
    except Exception as ex:
        print(f"赔率API错误: {ex}")
        return []

# 联赛ID配置
LEAGUES = {
    "世界杯": 1,
    "韩K联": 292,
    "韩K2联": 293,
    "英超": 39,
    "西甲": 140,
    "德甲": 78,
    "意甲": 135,
    "法甲": 61,
}

print(f"开始拉取数据：{date_str}")

all_fixtures = {}
all_odds = {}

for name, lid in LEAGUES.items():
    fixtures = get_fixtures(lid)
    if fixtures:
        all_fixtures[name] = fixtures
        odds = get_odds(lid)
        if odds:
            all_odds[name] = odds
        print(f"{name}: {len(fixtures)}场赛事")

if not all_fixtures:
    print("今日无赛事数据，尝试世界杯单独拉取")
    wc = get_fixtures(1, 2026)
    if wc:
        all_fixtures["世界杯"] = wc

fixtures_text = ""
odds_text = ""

for name, fixtures in all_fixtures.items():
    fixtures_text += f"\n【{name}】\n" + "\n".join(fixtures)

for name, odds in all_odds.items():
    odds_text += f"\n【{name}赔率】\n" + "\n".join(odds)

print(f"\n今日赛事：{fixtures_text}")
print(f"\n赔率数据：{odds_text[:500] if odds_text else '无'}")

prompt = f"""你是顶级足球盘口分析师，精通欧亚盘、大小球分析。现在北京时间 {date_str}。

【今日真实赛事数据】
{fixtures_text if fixtures_text else "暂无数据"}

【赔率数据】
{odds_text if odds_text else "暂无赔率数据"}

【本届世界杯已验证规律】
1. 水位接近1.00→比分偏小（已验证3次）
2. 弱队赔率<10→必须考虑进球
3. 平局预测成功率低，应谨慎
4. 防守型球队面对弱队已出线→可能大球爆发
5. 强队深度轮换→进球期望降至1–1.5球

请生成完整的专业盘口看盘HTML页面：

每场赛事必须包含：
1. 欧赔真实概率（去除庄家抽水反推）
2. 亚盘水位解读（强弱信号判断）
3. 大小球分析（盘口线+水位）
4. 五维度评分（进球期望/防守质量/水位/首轮数据/盘口线）
5. 精准比分三选（主推/次选/保险+概率%）
6. 冷门指数（★☆标注）
7. 综合verdict

HTML设计：
- 背景#080B0F，卡片#0D1117，金色#F0B429
- 文字#E6EDF3，绿#3FB950，红#F85149，蓝#58A6FF
- 每场卡片含胜率进度条（动画）
- 大小球双色条
- 比分矩阵热力图
- 冷门高危（≥3星）红色左边框
- 实时时钟
- 完全响应式
- 零外部依赖

只输出完整HTML，<!DOCTYPE html>开始，无任何解释。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": prompt}],
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

print(f"✅ 看盘生成成功，字符数：{len(html)}")
