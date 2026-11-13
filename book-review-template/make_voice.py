#!/usr/bin/env python3
"""书评系列正文配音：MiniMax 合成 → 压短过长停顿 → 列出每段语音的起止时间（用来对字幕）
用法: MINIMAX_API_KEY=... python3 make_voice.py "整段正文（带标点）" out.wav [语速 1.05] [最长停顿秒 0.6]
输出 out.wav（44.1k 单声道）和 out.chunks.txt（每段语音的起止时间），
再按这些时间点手写 subs.json：[[中文, English, 开始秒, 结束秒], ...]
"""
import json, os, sys, urllib.request, subprocess, wave
import numpy as np

text, out = sys.argv[1], sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.05
MAXP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
VOICE = os.environ.get("VOICE", "Chinese (Mandarin)_Gentleman")

body = {"model": "speech-2.8-turbo", "text": text, "stream": False,
        "voice_setting": {"voice_id": VOICE, "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 44100, "bitrate": 128000, "format": "mp3", "channel": 1}}
req = urllib.request.Request("https://api.minimaxi.com/v1/t2a_v2", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + os.environ["MINIMAX_API_KEY"], "Content-Type": "application/json"})
d = json.load(urllib.request.urlopen(req, timeout=180))
if not (d.get("data") or {}).get("audio"): sys.exit("配音失败: " + str(d.get("base_resp")))
raw_mp3 = out + ".raw.mp3"; open(raw_mp3, "wb").write(bytes.fromhex(d["data"]["audio"]))
raw_wav = out + ".raw.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_mp3, "-ac", "1", "-ar", "44100", raw_wav], check=True)

w = wave.open(raw_wav); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = int(0.01 * sr)
def rms_db(y):
    n = len(y) // hop
    return 20 * np.log10(np.array([np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2)) for i in range(n)]) + 1e-9)
def runs(mask):
    r, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            r.append((i, j)); i = j
        else: i += 1
    return r
# 压短停顿：超过 MAXP 秒的静音从中间剪掉多余部分；去掉开头静音，结尾留 0.2 秒
db = rms_db(x); n = len(db); keep = np.ones(len(x), bool)
for a, b in runs(db < -38):
    if a == 0: keep[:max(0, b * hop - int(0.03 * sr))] = False; continue
    if b >= n: keep[a * hop + int(0.2 * sr):] = False; continue
    dd = (b - a) * 0.01
    if dd > MAXP:
        cut = dd - MAXP; mid = (a + b) / 2 * 0.01
        keep[int((mid - cut / 2) * sr):int((mid + cut / 2) * sr)] = False
y = x[keep]
o = wave.open(out, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes((y * 32767).astype(np.int16).tobytes()); o.close()
# 列出语音段（间隔 <0.12 秒的合并）
db = rms_db(y); sp = db >= -38; n = len(db); ch = []; i = 0
while i < n:
    if sp[i]:
        j = i
        while j < n and (sp[j] or (j + 12 < n and sp[j:j + 12].any())): j += 1
        if (j - i) > 8: ch.append((i * 0.01, j * 0.01))
        i = j
    else: i += 1
with open(out + ".chunks.txt", "w") as f:
    for a, b in ch: f.write(f"{a:.2f}\t{b:.2f}\n")
print(f"done {out}  {len(y) / sr:.2f}s  {len(ch)} 段语音，见 {out}.chunks.txt")
