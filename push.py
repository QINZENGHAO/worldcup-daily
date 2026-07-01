import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")
today_date = now.strftime("%Y-%m-%d")
tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

def get_games(date):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date}&s=Soccer"
        r = requests.get(url, timeout=10).json()
        out = []
        for e in (r.get("events") or []):
            league = e.get("strLeague", "")
            if "World Cup" in league or "FIFA" in league:
                home = e.get("strHomeTeam", "")
                away = e.get("strAwayTeam", "")
                hs = e.get("intHomeScore")
                as_ = e.get("intAwayScore")
                t = e.get("strTime", "")
                if hs is not None and as_ is not None:
                    out.append(f"{home} {hs}-{as_} {away} [已结束]")
                else:
                    out.append(f"{home} vs {away} [{t}开踢]")
        return out
    except:
        return []

today_games = get_games(today_date)
tomorrow_games = get_games(tomorrow_date)
today_text = "\n".join(today_games) if today_games else "暂无赛事数据"
tomorrow_text = "\n".join(tomorrow_games) if tomorrow_games else "暂无赛事数据"

prompt = f"""你是专业世界杯分析师，现在是北京时间 {date_str}。

今日赛事数据：
{today_text}

明日赛事数据：
{tomorrow_text}

请生成一个完整的单页HTML世界杯数据看盘，要求：

【内容要求】
1. 页面顶部显示标题「2026世界杯数据看盘」和更新时间
2. 今日所有赛事卡片，每张卡片包含：
   - 比赛双方（带国旗emoji）和实时比分/倒计时
   - 三方胜率概率条（主胜/平局/客胜，带百分比）
   - 大小球分析（大2.5概率 vs 小2.5概率）
   - 冷门指数（★☆标注，1-5星）
   - 精推比分（最可能的3个比分）
   - 战意/轮换简评（2行以内）
3. 明日赛事预告（简版卡片）
4. 近期命中率统计（象牙海岸1-2挪威✓，法国3-0瑞典✓，德国1-1巴拉圭⚡冷门，荷兰1-1摩洛哥✓，巴西2-1日本✓）
5. 底部免责声明

【设计要求】
- 深色主题：背景 #0D0D0D，卡片 #141414，边框 #2A2A2A
- 金色强调色：#D2AA5A
- 成功绿：#2D9E5F，危险红：#E34948，警告橙：#eda100
- 卡片圆角12px，间距16px
- 胜率用彩色进度条（主队蓝#2a78d6，平局灰，客队金）
- 冷门高危场次加红色边框警示
- 完全响应式，手机和电脑都好看
- 页面宽度最大800px居中

【技术要求】
- 纯HTML+CSS+JS，不引用任何外部库
- 所有样式写在<style>标签内
- 页面底部JS显示实时北京时间时钟
- 无需任何外部字体或图标库

只输出完整HTML，从<!DOCTYPE html>开始，不要任何解释文字。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

html = response.choices[0].message.content
for tag in ["```html", "```HTML", "```"]:
    if tag in html:
        parts = html.split(tag)
        if len(parts) >= 3:
            html = parts[1]
        elif len(parts) == 2:
            html = parts[1]
        break

html = html.strip()
if not html.startswith("<!"):
    idx = html.find("<!DOCTYPE")
    if idx > 0:
        html = html[idx:]

os.makedirs("output", exist_ok=True)
with open("output/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"看盘已生成，字符数：{len(html)}")
print(f"今日赛事：{today_text}")

title = f"⚽ 世界杯看盘更新 · {now.strftime('%m/%d %H:%M')}"
desp = f"""看盘已自动更新！

**今日赛事**
{today_text}

**明日赛事**
{tomorrow_text}

**查看完整看盘**
https://QINZENGHAO.github.io/worldcup-daily/

更新时间：{date_str} 北京时间"""

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": desp}
)
print(f"微信推送：{resp.status_code}")
