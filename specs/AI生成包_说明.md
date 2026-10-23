# 说明 · AI 生成视频（AI意识视频，给 Grok）

你负责用 Gemini（Gemini App 或 Google Flow 都可以）生成下面 11 条视频，再把每条按镜头裁开，打包交回。会员有两个，不用省着用。

## 这次的新做法：一条视频里放几个镜头

每条视频 10 秒（Gemini 只能出 8 秒也行），里面按顺序放 2～3 个**硬切**的镜头。提示词已经写好，直接复制下面的英文。

## 规则

- 横屏 16:9。
- 画面里不能有文字、字幕、水印、品牌标志。出现了就重新生成。
- 镜头之间必须是硬切（画面直接换），不能有淡入淡出、溶解之类的转场。生成出来是转场的，就重新生成；实在不行，就把每个镜头单独生成一条（会员够用）。
- 分辨率不用管。生成一次满意就用，不用挑。

## 生成后怎么裁

1. 看画面在哪里突然换掉，那就是切点。按切点把视频裁开，**不要按提示词里的秒数硬裁**。
2. 每个镜头在切点前后各去掉约 2 帧（0.1 秒），避免带到上一个镜头的残影。
3. 命名：A01-1.mp4、A01-2.mp4、A01-3.mp4……（编号-第几个镜头）。
4. 原始整段也保留，放进「原片」文件夹，命名 A01.mp4、A02.mp4……
5. 如果生成出来的镜头数和要求的不一样（比如要 3 个只出了 2 个），按实际镜头裁，在「说明.txt」里写一句。

## G01 · 夜里和手机聊天（3 个镜头 → 裁成 G01-1、G01-2、G01-3）

```
A 10-second cinematic video made of 3 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-3s): At night, a young adult lies in bed chatting with an AI assistant on a smartphone, face softly lit by the screen, cozy dark bedroom. Shot 2 (3-7s): Close-up of the same person's face lit by the phone, expression softening into a sympathetic look. Shot 3 (7-10s): An adult sitting on a sofa smiling while typing on a smartphone, warm living room light. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G02 · 研究者讨论（2 个镜头 → 裁成 G02-1、G02-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): Three researchers in a university office discussing in front of a whiteboard covered with brain diagrams, natural light. Shot 2 (5-10s): Close-up of a hand drawing a simple brain diagram on a whiteboard with a marker. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G03 · 蝙蝠（3 个镜头 → 裁成 G03-1、G03-2、G03-3）

```
A 10-second cinematic video made of 3 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-3s): Thousands of bats flying out of a cave entrance at dusk, orange sky, wide shot. Shot 2 (3-7s): A single bat flying in the dark, with translucent glowing sound wave rings radiating from it to visualize echolocation. Shot 3 (7-10s): Close-up of a small fruit bat hanging upside down, blinking, soft light. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G04 · 小脑在干活（2 个镜头 → 裁成 G04-1、G04-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A person casually reaches for a coffee cup without looking while reading, the hand grabs it precisely, close-up. Shot 2 (5-10s): A person walking down stairs smoothly while looking at a phone, slow motion, side view. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G05 · 照镜子（2 个镜头 → 裁成 G05-1、G05-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A person standing in front of a bathroom mirror, tears on the face, we see both the person and the reflection, moody light. Shot 2 (5-10s): Close-up of the mirror surface showing the crying reflection, shallow depth of field. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G06 · 布娃娃和鹦鹉（2 个镜头 → 裁成 G06-1、G06-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A small child in a bedroom earnestly talking to a teddy bear, warm afternoon light. Shot 2 (5-10s): Close-up of a grey parrot tilting its head curiously, bright studio background. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G07 · 蛋白质结构（2 个镜头 → 裁成 G07-1、G07-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A glowing 3D protein structure made of colorful ribbons and helices slowly rotating in dark space, scientific visualization. Shot 2 (5-10s): Macro of protein ribbons folding into a compact shape, blue and gold tones, dark background. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G08 · 真的会疼的生命（3 个镜头 → 裁成 G08-1、G08-2、G08-3）

```
A 10-second cinematic video made of 3 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-3s): A shy dog in an animal shelter looking up at the camera, soft light. Shot 2 (3-7s): A volunteer gently helping an elderly person walk in a sunny park. Shot 3 (7-10s): A person kneeling to feed a thin stray cat on a city sidewalk. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G09 · 学术会议（2 个镜头 → 裁成 G09-1、G09-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A speaker on stage at an academic conference, seen as a silhouette against a large blank screen, audience in foreground. Shot 2 (5-10s): Wide shot of a lecture hall audience listening attentively, warm light. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G10 · 意识之谜（2 个镜头 → 裁成 G10-1、G10-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A translucent human silhouette whose head is filled with a swirling galaxy of stars and glowing neurons, dark background. Shot 2 (5-10s): Flying slowly through a vast network of glowing neurons that looks like a starry night sky. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## G11 · 放下手机（2 个镜头 → 裁成 G11-1、G11-2）

```
A 10-second cinematic video made of 2 separate shots joined by hard cuts, no transitions, no fades. Shot 1 (0-5s): A person puts a smartphone face down on a table, smiles to themselves and looks out the window, morning light. Shot 2 (5-10s): Close-up of a smartphone lying face down on a wooden table next to a cup of coffee. Consistent lighting and color grading across shots, photorealistic, slow smooth camera movement, no text, no subtitles, no logos, no watermarks.
```

## 交回

裁好的镜头（A01-1.mp4 …）+「原片」文件夹 +（如果有）「说明.txt」，打成 `AI意识_AI回传.zip`。

打包好后，用电脑上的 QQ 打开「我的手机」（我的Android手机 / 我的iPhone）对话，把这个压缩包发过去，发到我的手机 QQ 上。压缩包太大发不了，就分卷压缩成几个包分别发。

## 质量标准

差不多就行：有画面、好看、没有文字水印和品牌标志就过。分辨率不用检查，后期会统一增强。缺哪条就在交回包里写明缺什么，其余照常交回，不要因为一两条卡住。
