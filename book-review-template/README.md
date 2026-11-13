# 书评系列视频模板

竖版 1080×1440（3:4）书评短视频，参考"今天分享的是…"类书评号。整条结构：

1. **钩子**：一段真实影视片段（宽银幕居中）+ 两句金句双语字幕 + 顶部黄色关键词
2. **快速翻篇**：`flip_covers/` 里 7 张书封全屏快闪，每张约 0.11 秒，带翻页声，压着手写体"今天分享 / Share today"
3. **落到本期书封**：配音读"今天分享的是，XX 的《XX》"，顶部逐字打出书名和红色作者行，结尾暖白漏光
4. **正文**：Muse 生成的图片（每张停 10～15 秒），代码做推拉/平移、光尘、颗粒、漏光、雨丝、光晕、花瓣、两团光等，顶部固定书名，下方中英双语字幕

成片只有人声和少量音效，背景音乐最后自己加。响度约 −11 LUFS。

## 依赖

- Python 3 + `numpy`、`Pillow`
- `ffmpeg` / `ffprobe`
- 系统字体 Noto CJK（Ubuntu：`apt install fonts-noto-cjk`），手写体已在 `assets/fonts/`（马善政楷书，SIL OFL 授权，可商用）
- MiniMax 国内版 API key，放在环境变量 `MINIMAX_API_KEY`（不要写进仓库）

## 每期流程

1. **稿子**：用户写，Claude 拆成每句 15 字以内的双语字幕。
2. **正文配音**：
   ```bash
   MINIMAX_API_KEY=... python3 make_voice.py "整段正文（带标点）" body_final.wav 1.05 0.6
   ```
   参数依次是语速 1.05、最长停顿 0.6 秒。按输出的 `body_final.wav.chunks.txt` 手写 `subs.json`：`[[中文, English, 开始秒, 结束秒], ...]`
3. **素材包**：
   - 实拍包：钩子片段 `hook.mp4` 和本期书封 `cover.jpg`
   - AI 图片包：正文图 4～5 张，3:4，不出正脸，唯美意境
4. **开场**：照着 `examples/*/opening_config.json` 改书名、作者、金句、关键词。翻篇书封会读同一目录下的 `flip_covers/`，可以复制本目录的那 7 张过去。
   ```bash
   MINIMAX_API_KEY=... python3 make_opening.py opening_config.json      # → opening.mp4
   ```
5. **正文**：照着 `examples/*/body.json` 写每张图的时间段、裁切和镜头运动。
   ```bash
   python3 make_body.py body.json      # → body.mp4
   ```
6. **拼接 + 统一响度**：
   ```bash
   ffmpeg -i opening.mp4 -i body.mp4 -filter_complex "[0:v]fps=30,format=yuv420p[v0];[1:v]fps=30,format=yuv420p[v1];[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 18 -c:a pcm_s16le tmp.mkv
   # 先测响度，再把 volume 调到约 −11 LUFS
   ffmpeg -i tmp.mkv -c:v copy -af "volume=1.3dB,aresample=176400,alimiter=limit=0.9:attack=0.5:release=40:level=false,aresample=44100" -c:a aac -b:a 256k -movflags +faststart final.mp4
   ```

## 配置要点

**opening_config.json**
- `title` / `title_en` / `author`：顶部书名、英文名、作者行（作者行显示为"作者/著（书评）"）
- `hook_clip` + `hook_lines` + `keyword`：钩子片段、两句金句、黄色关键词；`hook_clip` 留空就没有钩子，直接从翻篇开始
- `intro_line`：开场配音，如"今天分享的是，弗洛姆的《爱的艺术》"
- `flip_fullbleed: true`：书封铺满全屏；`landed_brush: false`：落到真书封后不再叠手写书名（真书封自带书名）
- 配音：`voice` 默认 `Chinese (Mandarin)_Gentleman`，`speed` 1.05

**body.json**
- `voice` / `subs`：正文配音和字幕；`lead` 是开头从白光里出来的时长，`tail` 是念完后停留的秒数
- `shots[]`：`file` 可以是视频或图片；`start` / `end` 是相对配音的秒数
  - 图片专用：`crop` 先裁掉黑边或空白（0～1 比例），`move` 设镜头运动的起点和终点 `[cx, cy, zoom]`，zoom=1 表示刚好铺满
  - 代码层：`dust`（光尘强度）、`rain`（雨丝）、`flare`（光晕位置）、`petals`（花瓣）、`lights`（两团相连的光）
  - `xfade` 设和上一镜叠化的秒数
- `leaks`：暖色漏光的时间点（相对配音的秒数），一般放在色调转换处

## 例子

- `examples/ep01_art_of_loving/`：《爱的艺术》
- `examples/ep02_courage_to_be_disliked/`：《被讨厌的勇气》，正文 7 张图

例子里只有配置和字幕，素材（片段、书封、Muse 图）不放进仓库。
