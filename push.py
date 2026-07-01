import os
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta

SF_API_KEY = os.environ["SF_API_KEY"]
SERVER_CHAN_KEY = os.environ["SERVER_CHAN_KEY"]

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
date_str = now.strftime("%Y年%m月%d日 %H:%M")
today = now.strftime("%Y-%m-%d")
tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
weekday = now.strftime("%A")

client = OpenAI(
    api_key=SF_API_KEY,
    base_url="https://api.siliconflow.cn/v1"
)

prompt = f"""你是2026世界杯专业分析师，现在是北京时间 {date_str}，今天是{weekday}。

【2026美加墨世界杯背景】
小组赛阶段：2026年6月11日至7月2日
32支球队分8组，每组4队，共48场小组赛
淘汰赛：2026年7月4日开始

【你的任务】
根据2026世界杯真实赛程，推断今日({today})和明日({tomorrow})北京时间应有哪些比赛，给出完整分析。

已知近期真实战绩（供参考）：
- 6月30日：巴西2-1日本，德国1-1巴拉圭，荷兰1-1摩洛哥
- 7月1日：象牙海岸1-2挪威，法国3-0瑞典，墨西哥vs厄瓜多尔
- 7月2日应有：英格兰vs刚果(金)，比利时vs塞内加尔，美国vs波黑

近期命中战绩：
象牙海岸1-2挪威✅ 法国3-0瑞典✅ 德国1-1巴拉圭⚡冷门 荷兰1-1摩洛哥✅ 巴西2-1日本✅

【生成完整HTML看盘页面】

每场赛事必须包含真实分析：
1. 双方胜率（主胜X%/平局X%/客胜X%，合计100%，基于真实实力）
2. 大小球（大2.5球X%/小2.5球X%）
3. 冷门指数（1-5颗★，基于实力差距）
4. 精推比分3个（主推/次选/保险，真实合理比分）
5. 战意轮换简评（2行，绿点正面/红点风险）
6. verdict一句话总结

HTML设计规格（严格执行）：

配色：
- 页面背景：#0A0A0A
- 卡片背景：#131313
- 卡片边框：#242424
- 金色主色：#D2AA5A
- 文字主色：#E8E0D4
- 文字次色：#888882
- 绿色：#2D9E5F
- 红色：#E34948
- 橙色：#BA7517
- 蓝色：#2a78d6

完整页面结构：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026世界杯数据看盘</title>
<style>
/* 在此写所有CSS */
</style>
</head>
<body>
<!-- 1. 顶部导航：左"⚽ 2026世界杯看盘"，右实时时钟 -->
<!-- 2. 统计行：4个数据卡（今日场次/进行中/本届冷门数/累计命中率67%） -->
<!-- 3. 今日赛事标题 -->
<!-- 4. 每场赛事卡片（详见规格） -->
<!-- 5. 明日预告（简版卡片） -->
<!-- 6. 近期战绩复盘 -->
<!-- 7. 页脚 -->
<script>
// 实时时钟
// 进度条动画
</script>
</body>
</html>
```

赛事卡片完整规格：
