import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
hour = now.hour
date_str = now.strftime("%Y年%m月%d日")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

def get_wc_games(date_str_api):
    """从thesportsdb拉取世界杯赛事"""
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date_str_api}&s=Soccer"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        events = data.get("events") or []
        
        wc_keywords = ["World Cup", "FIFA World Cup", "2026"]
        wc_games = []
        
        for e in events:
            league = e.get("strLeague", "")
            if any(k in league for k in wc_keywords):
                home = e.get("strHomeTeam", "")
                away = e.get("strAwayTeam", "")
                home_score = e.get("intHomeScore")
                away_score = e.get("intAwayScore")
                status = e.get("strStatus", "")
                time_str = e.get("strTime", "")
                
                if home_score is not None and away_score is not None:
                    wc_games.append(f"✅ {home} {home_score}–{away_score} {away} [已结束]")
                else:
                    # 转换时间到北京时间
                    try:
                        t = datetime.strptime(
                            e.get("dateEvent","") + " " + time_str,
                            "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=timezone.utc)
                        bj = t.astimezone(tz).strftime("%H:%M")
                    except:
                        bj = time_str
                    wc_games.append(f"🔜 {home} vs {away} [北京{bj}]")
        
        return wc_games
    except Exception as ex:
        return [f"数据获取失败: {ex}"]

# 拉取今天和明天的赛事
today_api = now.strftime("%Y-%m-%d")
tomorrow = now + timedelta(days=1)
tomorrow_api = tomorrow.strftime("%Y-%m-%d")

today_games = get_wc_games(today_api)
tomorrow_games = get_wc_games(tomorrow_api)

today_text = "\n".join(today_games) if today_games else "今日无世界杯赛事"
tomorrow_text = "\n".join(tomorrow_games) if tomorrow_games else "明日无世界杯赛事"

if hour >= 16:
    task = "预测"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

【今日赛事】
{today_text}

【明日赛事】
{tomorrow_text}

请基于以上真实数据，对明日赛事按信心指数从高到低给出预测：
1. 每场给出开场/半场/全场比分推演
2. 冷门分析用★☆标注（★越多风险越高）
3. 结尾给出信心总览表格

⚠️ 只分析上面列出的真实比赛，不要编造任何比赛或比分。
格式简洁，适合微信阅读，多用emoji。"""

else:
    task = "复盘"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

【今日赛事结果】
{today_text}

【明日赛事预告】
{tomorrow_text}

请完成：
1. 逐场复盘今日已结束比赛，标注 ✅命中 / ❌偏差 / ⚡冷门
2. 统计整体命中率
3. 对明日赛事给出简要预测

⚠️ 只分析上面列出的真实比赛，不要编造数据。
格式简洁，适合微信阅读，多用emoji。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=2000
)

content = response.choices[0].message.content
title = f"⚽ 世界杯{task} · {now.strftime('%m/%d %H:%M')}"

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": content}
)

print(f"今日赛事:\n{today_text}")
print(f"明日赛事:\n{tomorrow_text}")
print(f"推送状态: {resp.status_code}")
print(f"内容预览:\n{content[:300]}")
