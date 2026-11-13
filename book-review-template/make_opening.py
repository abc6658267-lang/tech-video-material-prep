#!/usr/bin/env python3
"""书评系列固定开场 v2
结构：①钩子镜头（Muse 电影感片段 + 金句双语字幕 + 黄色关键词）
      ②快速翻书封（flip_covers/ 里的图）→ 落到本期书封，"今天分享的是，XX的《XX》"
      ③结尾漏光，接正片
用法: MINIMAX_API_KEY=... python3 make_opening.py config.json
"""
import json, os, sys, math, re, random, subprocess, urllib.request, wave, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CFG_PATH = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "config.json")
D = os.path.dirname(CFG_PATH)
HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(CFG_PATH, encoding="utf-8"))
W, H = cfg.get("size", [1080, 1440]); FPS = 30
WORK = os.path.join(D, "_work"); os.makedirs(WORK, exist_ok=True)
random.seed(5); np.random.seed(5)

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
BRUSH = os.path.join(HERE, "assets/fonts/MaShanZheng-Regular.ttf")
def cjk(p, s): return ImageFont.truetype(p, s, index=2)
def ttf(p, s): return ImageFont.truetype(p, s)

title, author = cfg["title"], cfg["author"]
title_en = cfg.get("title_en", "")
HAS_HOOK = bool(cfg.get("hook_clip"))
hook_lines = cfg.get("hook_lines", []) if HAS_HOOK else []         # [[中文, English], ...]
keyword = cfg.get("keyword", "")
intro_line = cfg.get("intro_line", "今天分享的是，{author}的《{title}》").format(author=author, title=title)

# ---------- 配音 ----------
def tts(text, out):
    if os.path.exists(out) and not cfg.get("force_tts"): return
    key = os.environ.get("MINIMAX_API_KEY") or cfg.get("api_key")
    body = {"model": cfg.get("model", "speech-2.8-turbo"), "text": text, "stream": False,
            "voice_setting": {"voice_id": cfg.get("voice", "Chinese (Mandarin)_Gentleman"),
                              "speed": cfg.get("speed", 1.0), "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 44100, "bitrate": 128000, "format": "mp3", "channel": 1}}
    req = urllib.request.Request("https://api.minimaxi.com/v1/t2a_v2", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    if not (d.get("data") or {}).get("audio"): sys.exit("配音失败: " + str(d.get("base_resp")))
    audio = bytes.fromhex(d["data"]["audio"]); open(out, "wb").write(audio)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def trimmed(src, out):   # 去掉首尾静音，方便精确排时间
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", "44100", "-ac", "1", out], check=True)

hook_wavs = []
for k, (zh, en) in enumerate(hook_lines):
    raw = os.path.join(WORK, f"hook{k}.mp3"); tts(zh, raw)
    wv = os.path.join(WORK, f"hook{k}.wav"); trimmed(raw, wv); hook_wavs.append(wv)
intro_raw = os.path.join(WORK, "intro.mp3"); tts(intro_line, intro_raw)
intro_wav = os.path.join(WORK, "intro.wav"); trimmed(intro_raw, intro_wav)

# ---------- 时间轴 ----------
LEAD, GAP = 0.25, 0.18
line_t = []; t = LEAD
for wv in hook_wavs:
    d_ = dur(wv); line_t.append((t, t + d_)); t += d_ + GAP
T1 = (t + cfg.get("hook_tail", 0.15)) if HAS_HOOK else 0.0              # 钩子结束、开始翻书
FLIP_DT = cfg.get("flip_interval", 0.11)
pool = sorted(glob.glob(os.path.join(D, cfg.get("flip_dir", "flip_covers"), "*.*")))[: cfg.get("flip_count", 6)]
T_LAND = T1 + FLIP_DT * len(pool)               # 落到本期书封
T_INTRO = T1 + 0.05
intro_d = dur(intro_wav)
T_END = max(T_LAND + 1.5, T_INTRO + intro_d + 0.55)
LEAK = cfg.get("end_leak", 0.4)
N = int(round(T_END * FPS))

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def tw(f, s): b = f.getbbox(s); return b[2] - b[0]

# ---------- 钩子镜头 ----------
ASPECT = cfg.get("hook_aspect", 2.0)
HC = int(W / ASPECT) // 2 * 2
hook_path = os.path.join(D, cfg.get("hook_clip") or "")
raw = b"" if not HAS_HOOK else subprocess.run(["ffmpeg", "-v", "error", "-i", hook_path, "-vf",
                      f"scale={W}:{HC}:force_original_aspect_ratio=increase,crop={W}:{HC},fps={FPS}",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
hook_frames = None if not HAS_HOOK else np.frombuffer(raw, np.uint8).reshape(-1, HC, W, 3)
HOOK_CY = int(H * cfg.get("hook_center", 0.46))
hook_top = HOOK_CY - HC // 2

f_sub = cjk(SERIF, 46); f_sub_en = cjk(SANS_M, 25)
f_kw = cjk(SANS_B, 96)
f_title = cjk(SANS_B, 84); f_author = cjk(SANS_B, 36)
f_brush = ttf(BRUSH, 70); f_brush_en = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", 26) \
    if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf") else f_sub_en

def text_layer(items):
    """items: [(xy, text, font, rgb, alpha, anchor, stroke)] -> 带柔和阴影的透明层"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for xy, s, f, rgb, a, anc, st in items:
        if a <= 0: continue
        sw, sc = (st if isinstance(st, tuple) else (st, (20, 20, 20)))
        d.text(xy, s, font=f, fill=rgb + (int(255 * a),), anchor=anc,
               stroke_width=sw, stroke_fill=sc + (int(235 * a),) if sw else None)
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.putalpha(sh.point(lambda v: int(v * 0.65)))
    o2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o2.alpha_composite(out, (0, 3)); o2.alpha_composite(lay)
    return o2

def render_hook(t):
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    fi = min(int(t * FPS), len(hook_frames) - 1)
    clip = Image.fromarray(hook_frames[fi])
    # 退出：最后 0.3 秒推近 + 虚化 + 变暗
    ex = ease_io((t - (T1 - 0.3)) / 0.3)
    if ex > 0:
        s = 1 + 0.12 * ex
        cw, ch = int(W / s), int(HC / s)
        clip = clip.crop(((W - cw) // 2, (HC - ch) // 2, (W - cw) // 2 + cw, (HC - ch) // 2 + ch)).resize((W, HC))
        clip = clip.filter(ImageFilter.GaussianBlur(14 * ex))
    a_in = ease_io(t / 0.3) * (1 - ex)
    clip = Image.eval(clip, lambda v, a=a_in: int(v * a))
    fr.paste(clip, (0, hook_top))
    items = []
    sub_y = hook_top + HC + 42
    for (zh, en), (a, b) in zip(hook_lines, line_t):
        end = b + GAP if (a, b) != line_t[-1] else T1
        al = min(ease_out((t - a + 0.05) / 0.15), 1 - ease_out((t - end + 0.08) / 0.1)) * (1 - ex)
        if al > 0:
            items += [((W / 2, sub_y), zh, f_sub, (245, 240, 230), al, "mt", 0),
                      ((W / 2, sub_y + 66), en, f_sub_en, (215, 210, 200), al * 0.9, "mt", 0)]
    if keyword:
        ka_t = line_t[min(cfg.get("keyword_line", len(line_t) - 1), len(line_t) - 1)][0] + 0.15
        ka = ease_out((t - ka_t) / 0.35) * (1 - ex)
        items.append(((W / 2, hook_top - 150 - 18 * (1 - ka)), keyword, f_kw, (255, 210, 30), ka, "mt", 0))
    fr.alpha_composite(text_layer(items))
    return fr

# ---------- 翻书 ----------
FULL = cfg.get("flip_fullbleed", False)
def fit_cover(p):
    im = Image.open(p).convert("RGB")
    if FULL:   # 铺满全屏：按 3:4 裁切填满
        r = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
        x, y = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((x, y, x + W, y + H))
    cw = int(W * cfg.get("cover_width", 0.62)); ch = int(cw * im.height / im.width)
    if ch > H * 0.6: ch = int(H * 0.6); cw = int(ch * im.width / im.height)
    return im.resize((cw, ch), Image.LANCZOS)
target = fit_cover(os.path.join(D, cfg["cover"]))
flips = [fit_cover(p) for p in pool]
paper = np.full((H, W, 3), (241, 239, 235), np.float32) + np.random.normal(0, 3, (H, W, 1))
paper = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8))
COV_CY = int(H * 0.52)
ghost_cache = {}
def ghost(im):   # 背后放大的虚影
    k = id(im)
    if k not in ghost_cache:
        g = im.resize((int(W * 1.25), int(W * 1.25 * im.height / im.width))).filter(ImageFilter.GaussianBlur(30))
        bgc = paper.copy(); bgc.paste(g, ((W - g.width) // 2, (H - g.height) // 2))
        ghost_cache[k] = Image.blend(paper, bgc, 0.22)
    return ghost_cache[k]
shadow_cache = {}
def shadow_for(size):
    if size not in shadow_cache:
        pad = 60; s = Image.new("L", (size[0] + pad * 2, size[1] + pad * 2), 0)
        ImageDraw.Draw(s).rectangle([pad, pad + 10, pad + size[0], pad + size[1] + 10], fill=95)
        shadow_cache[size] = (s.filter(ImageFilter.GaussianBlur(22)), pad)
    return shadow_cache[size]

def render_flip(t):
    tl = t - T1
    landed = t >= T_LAND
    if landed: cov, k_in = target, (t - T_LAND)
    else:
        idx = int(tl / FLIP_DT); cov = flips[idx]; k_in = tl - idx * FLIP_DT
    if FULL:
        pop = 1 + 0.04 * (1 - ease_out(k_in / (0.1 if not landed else 0.5)))
        c = cov if pop == 1 else cov.resize((int(W * pop), int(H * pop)))
        fr = c.crop(((c.width - W) // 2, (c.height - H) // 2, (c.width - W) // 2 + W, (c.height - H) // 2 + H)).convert("RGBA")
        if not landed and k_in < 0.04:   # 翻页一瞬的横向动感模糊
            fr = fr.filter(ImageFilter.BoxBlur(6))
        y = 0; c = cov
    else:
        fr = ghost(cov).convert("RGBA")
    if not FULL:
        pop = 1 + (0.035 if not landed else 0.05) * (1 - ease_out(k_in / (0.08 if not landed else 0.35)))
        c = cov if pop == 1 else cov.resize((int(cov.width * pop), int(cov.height * pop)))
        x = (W - c.width) // 2 - int((1 - ease_out(k_in / 0.06)) * 50 if not landed else 0)
        y = COV_CY - c.height // 2
        sh, pad = shadow_for(c.size)
        sl = Image.new("RGBA", sh.size, (0, 0, 0, 0)); sl.putalpha(sh)
        fr.alpha_composite(sl, (x - pad, y - pad))
        fr.paste(c, (x, y))
        ImageDraw.Draw(fr).rectangle([x, y, x + c.width - 1, y + c.height - 1], outline=(150, 150, 150), width=2)
    cov_bottom = y + c.height
    items = []
    # 手写字：翻书时"今天分享"，落定后换成书名
    by = int(H * 0.80) if FULL else COV_CY + int(target.height * 0.33)
    if not landed:
        items += [((W / 2, by), "今天分享", f_brush, (35, 35, 35), 1, "mm", (3, (255, 255, 255))),
                  ((W / 2, by + 52), "Share today", f_brush_en, (60, 60, 60), 0.9, "mm", (2, (255, 255, 255)))]
    elif cfg.get("landed_brush", True):
        a = ease_out((t - T_LAND - 0.15) / 0.4)
        items += [((W / 2, by + 8 * (1 - a)), title, f_brush, (35, 35, 35), a, "mm", (3, (255, 255, 255)))]
        if title_en: items.append(((W / 2, by + 52), title_en, f_brush_en, (60, 60, 60), a * 0.9, "mm", (2, (255, 255, 255))))
    # 顶部书名逐字 + 红色作者（和正片顶部标题位置一致）
    if landed:
        tt = f"《{title}》"; x0 = (W - tw(f_title, tt)) / 2; ty = int(H * 0.085); xx = x0
        for j, ch_ in enumerate(tt):
            a = ease_out((t - T_LAND - 0.05 - j * 0.06) / 0.18)
            items.append(((xx, ty + 8 * (1 - a)), ch_, f_title, (255, 255, 255), a, "la", 3))
            xx += tw(f_title, ch_) + 2
        aa = ease_out((t - T_LAND - 0.1 - len(tt) * 0.06) / 0.3)
        items.append(((W / 2, ty + 124), f"{author}/著（书评）", f_author, tuple(cfg.get("author_color", [214, 52, 40])), aa, "mt", (3, (255, 255, 255))))
    fr.alpha_composite(text_layer(items))
    return fr

# ---------- 逐帧 ----------
yy, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
leak_shape = np.exp(-(((xx_ - W * 0.15) / (W * 0.9)) ** 2 + ((yy - H * 0.3) / (H * 0.7)) ** 2))[..., None]
leak_col = np.array([255, 236, 205], np.float32)
grain = [np.random.normal(0, 5, (H, W, 1)).astype(np.float32) for _ in range(4)]
vid = os.path.join(WORK, "video.mp4")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                      "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    fr = render_hook(t) if t < T1 else render_flip(t)
    arr = np.asarray(fr.convert("RGB")).astype(np.float32) + grain[i % 4]
    if not HAS_HOOK and t < 0.12: arr *= t / 0.12   # 无钩子时开头极短淡入
    lk = ease_io((t - (T_END - LEAK)) / LEAK)
    if lk > 0:   # 漂白漏光，接正片
        m = np.clip(leak_shape * 1.6 * lk + 0.75 * lk ** 2, 0, 1)
        arr = arr * (1 - m) + leak_col * m
    p.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()

# ---------- 声音 ----------
SR = 44100
def write_wav(path, x):
    x = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
def read_wav(path):
    with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
voice = np.zeros(int(T_END * SR) + SR)
for wv, (a, b) in zip(hook_wavs, line_t):
    x = read_wav(wv); s = int(a * SR); voice[s:s + len(x)] += x
x = read_wav(intro_wav); s = int(T_INTRO * SR); voice[s:s + len(x)] += x
voice = voice[: int(T_END * SR)]
# 翻页沙沙声：每张书封一下
sfx = np.zeros_like(voice)
for k in range(len(pool) + 1):
    n = int(0.07 * SR); tt_ = np.arange(n) / SR
    burst = np.random.normal(0, 1, n); burst = np.convolve(burst, np.ones(3) / 3, "same") - np.convolve(burst, np.ones(40) / 40, "same")
    burst *= np.minimum(tt_ / 0.004, 1) * np.exp(-tt_ / 0.02) * random.uniform(0.6, 1.0)
    s = int((T1 + k * FLIP_DT) * SR); sfx[s:s + n] += burst
vpath, spath = os.path.join(WORK, "voice_mix.wav"), os.path.join(WORK, "sfx.wav")
write_wav(vpath, voice / max(np.abs(voice).max(), 1e-6) * 0.7)
write_wav(spath, sfx / max(np.abs(sfx).max(), 1e-6) * 0.7)

def lufs_of(pth):
    e = subprocess.run(["ffmpeg", "-i", pth, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
L = cfg.get("lufs", -11)
vg = L - lufs_of(vpath); sg = (L - 3) - lufs_of(spath)
ins = ["-i", vid, "-i", vpath, "-i", spath]
fc = f"[1:a]volume={vg:.2f}dB,aformat=channel_layouts=stereo[v];[2:a]volume={sg:.2f}dB,aformat=channel_layouts=stereo[s];"
mix = "[v][s]"; n_in = 2
# 钩子片段原声（Muse 自带声音），比人声低 10 dB
has_a = HAS_HOOK and subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", hook_path],
                       capture_output=True, text=True).stdout.strip()
if has_a and cfg.get("hook_audio", True):
    hp = os.path.join(WORK, "hook_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", hook_path, "-t", f"{T1:.3f}", "-ac", "1", "-ar", "44100",
                    "-af", f"afade=t=out:st={max(T1 - 0.3, 0):.3f}:d=0.3", hp], check=True)
    hg = (L - 10) - lufs_of(hp)
    ins += ["-i", hp]; fc += f"[3:a]volume={hg:.2f}dB,aformat=channel_layouts=stereo[h];"; mix += "[h]"; n_in = 3
fc += f"{mix}amix=inputs={n_in}:normalize=0:duration=first,alimiter=limit=0.92:level=false[a]"
OUT = os.path.join(D, cfg.get("output", "opening.mp4"))
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", OUT], check=True)
print(f"done {OUT}  {T_END:.2f}s  hook {T1:.2f}s  land {T_LAND:.2f}s")
