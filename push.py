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

# 拉取实时世界杯数据
def get_wc_data():
    try:
        resp = requests.get(
            "https://api.sofascore.com/api/v1/sport/football/scheduled-events/"
            + now.strftime("%Y-%m-%d"),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        events = resp.json().get("events", [])
        wc = [e for e in events if "World Cup" in e.get("tournament", {}).get("name", "")]
        lines = []
        for e in wc:
            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]
            status = e.get("status", {}).get("type", "")
            if status == "finished":
                hs = e["homeScore"]["current"]
                as_ = e["awayScore"]["current"]
                lines.append(f"{home} {hs}–{as_} {away} [已结束]")
            else:
                t = e.get("startTimestamp", 0)
                gt = datetime.fromtimestamp(t, tz).strftime("%H:%M")
                lines.append(f"{home} vs {away} [{gt}开踢]")
        return "\n".join(lines) if lines else "暂无世界杯赛事数据"
    except:
        return "数据获取失败，请根据实际情况分析"

games_info = get_wc_data()

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

if hour >= 16:
    task = "预测"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

以下是今明两日的真实世界杯赛事数据：
{games_info}

请严格基于以上真实赛事数据，给出明日赛事预测：
1. 按信心指数从高到低排列
2. 每场包含：开场/半场/全场比分推演
3. 冷门分析（用★标注冷门指数）
4. 结尾信心总览表格

⚠️ 只分析上面列出的真实比赛，不要编造比赛。格式简洁适合微信阅读。"""
else:
    task = "复盘"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

以下是今日真实世界杯赛事数据：
{games_info}

请严格基于以上真实数据：
1. 列出所有已结束比赛的真实结果
2. 逐场标注 ✅命中 / ❌偏差 / ⚡冷门
3. 统计命中率
4. 若有未开始的比赛，给出预测

⚠️ 只分析上面列出的真实比赛，不要编造数据。格式简洁适合微信阅读。"""

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

print(f"推送状态: {resp.status_code}")
print(f"赛事数据:\n{games_info}")
print(f"内容预览:\n{content[:300]}")
