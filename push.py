import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

prompt = f"""你是专业世界杯分析师，现在是北京时间 {date_str}。

请生成一个完整的2026世界杯数据看盘HTML页面。

【今日及近期赛事数据（请基于真实世界杯赛程）】
根据2026美加墨世界杯小组赛赛程，列出今日和明日真实赛事，给出分析。

近期命中战绩：
- 象牙海岸 1-2 挪威 ✅命中
- 法国 3-0 瑞典 ✅命中  
- 德国 1-1 巴拉圭 ⚡冷门
- 荷兰 1-1 摩洛哥 ✅命中
- 巴西 2-1 日本 ✅命中
- 英格兰 vs 刚果(金)（今日预测：英格兰3-0，大球）
- 比利时 vs 塞内加尔（今日预测：1-1平局，小球，冷门警示）
- 美国 vs 波黑（今日预测：美国2-0）

【页面设计要求 - 必须严格执行】

配色方案：
- 页面背景：#0A0A0A
- 卡片背景：#111111
- 边框：#1E1E1E
- 金色主色：#D2AA5A
- 文字主色：#E8E0D4
- 文字次色：#8A8A80
- 成功绿：#2D9E5F
- 危险红：#E34948
- 警告橙：#BA7517
- 蓝色：#2a78d6

布局结构（严格按此顺序）：
1. 顶部导航栏：logo+标题左对齐，实时时钟右对齐，金色下边框
2. 统计概览行：4个数据卡（今日场次/进行中/本届冷门数/命中率）
3. 今日赛事区块标题
4. 每场赛事大卡片（见下方规格）
5. 明日预告区块（小卡片列表）
6. 近期战绩复盘表
7. 底部免责声明

赛事卡片规格（每张必须包含）：
- 顶部：开赛时间（北京时间）+ 状态badge（进行中/即将开赛/已结束）
- 中部：主队国旗emoji + 队名 | 比分或VS | 客队国旗emoji + 队名
- 胜率概率：三条彩色进度条（主胜蓝/平局灰/客胜金），带百分比数字
- 大小球分析：左右两个方块（大球概率%/小球概率%），用不同颜色区分
- 冷门指数：★★★☆☆样式（实心空心星），红色背景badge
- 精推比分：3个推荐比分（主推/次选/保险），带置信度标注
- 战意轮换：2行简短文字，绿点/红点标注
- 底部verdict条：彩色badge + 一句话总结

冷门高危场次（比利时vs塞内加尔）：整张卡片左边框用红色3px solid

技术规格：
- 最大宽度820px，水平居中
- 卡片圆角14px，内边距20px
- 卡片间距12px
- 所有transition: 0.2s
- 卡片hover时边框变亮（border-color变为#D2AA5A）
- 完全响应式（手机<768px单列，字体适当缩小）
- 顶部实时时钟用JS每秒更新
- 进度条用CSS animation从0增长到目标宽度（0.8s ease-out）
- 无需引用任何外部CSS库或字体

只输出完整HTML，从<!DOCTYPE html>开始到</html>结束，不要任何解释。"""

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=8000,
    temperature=0.3
)

html = response.choices[0].message.content.strip()

for tag in ["```html", "```HTML", "```"]:
    if tag in html:
        parts = html.split(tag)
        if len(parts) >= 3:
            html = parts[1].strip()
            break
        elif len(parts) == 2:
            html = parts[1].strip()
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

title = f"⚽ 世界杯看盘已更新 · {now.strftime('%m/%d %H:%M')}"
desp = f"""## 看盘已自动更新

**更新时间：** {date_str} 北京时间

**今日重点赛事：**
- 00:00 🏴󠁧󠁢󠁥󠁮󠁧󠁿 英格兰 vs 🇨🇩 刚果(金) → 精推 3-0 大球
- 04:00 🇧🇪 比利时 vs 🇸🇳 塞内加尔 → ⚠️冷门警示 小球
- 08:00 🇺🇸 美国 vs 🇧🇦 波黑 → 精推 2-0

**查看完整看盘：**
https://QINZENGHAO.github.io/worldcup-daily/

> 纯属推演，仅供参考娱乐"""

resp = requests.post(
    f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
    data={"title": title, "desp": desp}
)
print(f"微信推送：{resp.status_code}")
