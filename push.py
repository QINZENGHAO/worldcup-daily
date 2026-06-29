import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

OR_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
hour = now.hour
date_str = now.strftime("%Y年%m月%d日")
tomorrow = (now + timedelta(days=1)).strftime("%Y年%m月%d日")

client = OpenAI(
    api_key=OR_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def get_wc_games():
    try:
        today = now.strftime("%Y-%m-%d")
        tom = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        results = []
        for d in [today, tom]:
            url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d}&s=Soccer"
            r = requests.get(url, timeout=10).json()
            for e in (r.get("events") or []):
                if "World Cup" in e.get("strLeague","") or "FIFA" in e.get("strLeague",""):
                    home = e.get("strHomeTeam","")
                    away = e.get("strAwayTeam","")
                    hs = e.get("intHomeScore")
                    as_ = e.get("intAwayScore")
                    if hs is not None and as_ is not None:
                        results.append(f"[{d}] {home} {hs}–{as_} {away} ✅已结束")
                    else:
                        t = e.get("strTime","")
                        results.append(f"[{d}] {home} vs {away} 🔜{t}开踢")
        return "\n".join(results) if results else None
    except:
        return None

games = get_wc_games()

if hour >= 16:
    task = "预测"
    games_text = f"以下是今明两日真实世界杯赛事数据：\n{games}" if games else ""
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。
{games_text}
请给出明日所有世界杯赛事的深度预测：
1. 按信心指数从高到低排列
2. 每场包含：开场/半场/全场比分推演、关键球员、战术分析
3. 冷门分析用★标注冷门指数
4. 结尾给出信心总览表格
格式简洁适合微信阅读，多用emoji，内容要专业有深度。"""
else:
    task = "复盘"
    games_text = f"以下是今日真实世界杯赛事数据：\n{games}" if games else ""
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。
{games_text}
请完成：
1. 逐场复盘今日比赛真实结果，标注✅命中/❌偏差/⚡冷门
2. 统计命中率与规律总结
3. 明日赛事简要预测
格式简洁适合微信阅读，多用emoji。"""

response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct:free",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=2000,
    extra_headers={
        "HTTP-Referer": "https://github.com/QINZENGHAO/worldcup-daily",
        "X-Title": "WorldCup Daily Push"
    }
)

content = response.choices[0].message.content
title = f"⚽ 世界杯{task} · {now.strftime('%m/%d %H:%M')}"

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": content}
)

print(f"推送状态: {resp.status_code}")
print(f"内容预览:\n{content[:300]}")
