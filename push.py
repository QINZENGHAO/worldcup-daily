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

def get_wc_games():
    try:
        today = now.strftime("%Y-%m-%d")
        tom = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        results = []
        for d in [today, tom]:
            url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={d}&s=Soccer"
            r = requests.get(url, timeout=10).json()
            for e in (r.get("events") or []):
                league = e.get("strLeague", "")
                if "World Cup" in league or "FIFA" in league:
                    home = e.get("strHomeTeam", "")
                    away = e.get("strAwayTeam", "")
                    hs = e.get("intHomeScore")
                    as_ = e.get("intAwayScore")
                    if hs is not None and as_ is not None:
                        results.append(f"[{d}] {home} {hs}–{as_} {away} 已结束")
                    else:
                        t = e.get("strTime", "")
                        results.append(f"[{d}] {home} vs {away} {t}开踢")
        return "\n".join(results) if results else None
    except Exception as ex:
        return None

games = get_wc_games()

if hour >= 16:
    task = "预测"
    games_text = f"今明两日真实世界杯赛事：\n{games}\n" if games else "（今日暂无赛事数据）\n"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

{games_text}
请严格基于以上真实赛事，给出明日预测：
1. 按信心指数从高到低排列
2. 每场给出开场/半场/全场比分推演
3. 冷门分析标注冷门指数
4. 结尾给出信心总览表格

只分析以上列出的真实比赛，不要编造比赛。格式简洁适合微信阅读。"""

else:
    task = "复盘"
    games_text = f"今日真实世界杯赛事：\n{games}\n" if games else "（今日暂无赛事数据）\n"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

{games_text}
请完成：
1. 逐场复盘今日已结束比赛，标注命中/偏差/冷门
2. 统计命中率
3. 明日赛事简要预测

只分析以上列出的真实比赛，不要编造数据。格式简洁适合微信阅读。"""

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

print(f"游戏数据: {games}")
print(f"推送状态: {resp.status_code}")
print(f"内容预览:\n{content[:300]}")
