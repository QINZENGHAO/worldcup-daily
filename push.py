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

if hour >= 16:
    task = "预测"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

请给出明日所有世界杯赛事预测，要求：
1. 按信心指数从高到低排列
2. 每场包含：开场/半场/全场比分推演
3. 每场包含冷门分析（冷门指数★标注）
4. 结尾给出信心总览表格

格式简洁，适合微信阅读，用emoji增加可读性。"""
else:
    task = "复盘"
    prompt = f"""你是专业世界杯分析师，今天是{date_str}。

请完成：
1. 列出昨日所有世界杯真实比赛结果
2. 逐场分析：✅命中 / ❌偏差 / ⚡冷门发生
3. 统计整体命中率
4. 今日若有赛事，给出预测

格式简洁，适合微信阅读，用emoji增加可读性。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
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
print(f"内容预览:\n{content[:300]}")
