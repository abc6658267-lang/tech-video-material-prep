#!/usr/bin/env python3
"""书评系列正文合成：Muse 镜头 + 顶部固定书名 + 双语字幕 + 代码层（光尘/颗粒/光点）+ 人声与 Muse 声音混音
用法: python3 make_body.py body.json
"""
import json, os, sys, re, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CFG = os.path.abspath(sys.argv[1]); D = os.path.dirname(CFG)
cfg = json.load(open(CFG, encoding="utf-8"))
W, H = cfg.get("size", [1080, 1440]); FPS = 30
WORK = os.path.join(D, "_body_work"); os.makedirs(WORK, exist_ok=True)
random.seed(11); np.random.seed(11)
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
def cjk(p, s): return ImageFont.truetype(p, s, index=2)
f_title, f_author = cjk(SANS_B, 84), cjk(SANS_B, 36)
f_sub, f_en = cjk(SERIF, 46), cjk(SANS_M, 25)

voice = os.path.join(D, cfg["voice"])
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
LEAD = cfg.get("lead", 0.35)            # 正文开头先从白光里出来，再开口
T_END = LEAD + dur(voice) + cfg.get("tail", 1.2)
N = int(round(T_END * FPS))
subs = [[zh, en, a + LEAD, b + LEAD] for zh, en, a, b in json.load(open(os.path.join(D, cfg["subs"]), encoding="utf-8"))]

# 镜头：start/end 是成片时间（相对正文语音），src 是素材入点
shots = cfg["shots"]
for s in shots:
    s["t0"] = (0 if s is shots[0] else s["start"] + LEAD); s["t1"] = (s["end"] + LEAD if s is not shots[-1] else T_END)
def load(path, src_in, length):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src_in:.3f}", "-i", path, "-t", f"{length + 0.6:.3f}", "-vf",
                          f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")
def ease_io(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def load_image(s, length):
    im = Image.open(os.path.join(D, s["file"])).convert("RGB")
    cx0, cy0, cx1, cy1 = s.get("crop", [0, 0, 1, 1])      # 先裁掉黑边/空白（0~1 比例）
    im = im.crop((int(cx0 * im.width), int(cy0 * im.height), int(cx1 * im.width), int(cy1 * im.height)))
    # move: [cx, cy, zoom] 起点 → 终点；zoom=1 表示刚好铺满 3:4
    a, b = s.get("move", [[0.5, 0.5, 1.0], [0.5, 0.5, 1.08]])
    base = min(im.width / W, im.height / H)              # 铺满时 1 个输出像素对应的原图像素
    n = int(round(length * FPS)) + 2
    class Lazy:   # 按需逐帧生成，避免一次把所有帧放进内存
        def __len__(self): return n
        def __getitem__(self, k):
            k = min(max(k, 0), n - 1)
            u = ease_io(k / max(n - 1, 1)) if s.get("ease", True) else k / max(n - 1, 1)
            cx, cy, z = [a[i] + (b[i] - a[i]) * u for i in range(3)]
            cw, ch = W * base / z, H * base / z
            x0 = min(max(cx * im.width - cw / 2, 0), im.width - cw); y0 = min(max(cy * im.height - ch / 2, 0), im.height - ch)
            return np.asarray(im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC))
    return Lazy()
for s in shots:
    if s["file"].lower().endswith(IMG_EXT):
        s["frames"] = load_image(s, s["t1"] - s["t0"] + s.get("xfade", 0) + 0.2); s["is_img"] = True
        print("image", s["file"], len(s["frames"])); continue
    s["frames"] = load(os.path.join(D, s["file"]), s.get("src_in", 0), s["t1"] - s["t0"] + s.get("xfade", 0))
    print("loaded", s["file"], len(s["frames"]))

def shot_frame(s, t):
    k = min(int((t - s["t0"]) * FPS * s.get("speed", 1.0)), len(s["frames"]) - 1)
    return s["frames"][max(k, 0)].astype(np.float32)

# 调色：统一暖调、轻微压高光
def grade(a):
    a = a * np.array(cfg.get("tint", [1.03, 1.0, 0.95]), np.float32)
    return 255 * (1 - np.exp(-a / 255 * 1.08)) / (1 - math.exp(-1.08))

# 顶部固定标题层（和开场落定时完全一致）
def title_layer():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tt = f"《{cfg['title']}》"; ty = int(H * 0.085)
    d.text((W / 2, ty), tt, font=f_title, fill=(255, 255, 255, 255), anchor="mt", stroke_width=3, stroke_fill=(20, 20, 20, 235))
    d.text((W / 2, ty + 124), f"{cfg['author']}/著（书评）", font=f_author, fill=tuple(cfg.get("author_color", [214, 52, 40])) + (255,),
           anchor="mt", stroke_width=3, stroke_fill=(255, 255, 255, 235))
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2.putalpha(sh.point(lambda v: int(v * 0.6))); out.alpha_composite(s2, (0, 3)); out.alpha_composite(lay)
    return np.asarray(out).astype(np.float32)
TITLE = title_layer()
# 字幕层缓存
sub_cache = {}
SUB_Y = int(H * cfg.get("sub_y", 0.74))
def sub_layer(k):
    if k not in sub_cache:
        zh, en = subs[k][0], subs[k][1]
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.text((W / 2, SUB_Y), zh, font=f_sub, fill=(255, 252, 245, 255), anchor="mt", stroke_width=2, stroke_fill=(45, 35, 28, 200))
        d.text((W / 2, SUB_Y + 66), en, font=f_en, fill=(245, 240, 232, 245), anchor="mt", stroke_width=2, stroke_fill=(45, 35, 28, 190))
        sh = lay.split()[3].filter(ImageFilter.GaussianBlur(9))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s2.putalpha(sh.point(lambda v: min(255, int(v * 0.95)))); out.alpha_composite(s2, (0, 2)); out.alpha_composite(lay)
        sub_cache[k] = np.asarray(out).astype(np.float32)
    return sub_cache[k]
def over(base, lay, a=1.0):
    al = lay[..., 3:4] / 255 * a
    return base * (1 - al) + lay[..., :3] * al

# 代码层：漂浮光尘
class Mote:
    def __init__(s):
        s.x, s.y = random.uniform(0, W), random.uniform(0, H)
        s.r = random.choice([2, 2, 3, 3, 4, 6, 10]); s.vx, s.vy = random.uniform(-10, 10), random.uniform(-25, -5)
        s.a = random.uniform(0.25, 0.7) * (0.45 if s.r > 6 else 1); s.ph = random.uniform(0, 6.3)
motes = [Mote() for _ in range(70)]
spr = {}
def sprite(r):
    if r not in spr:
        z = r * 6; im = Image.new("L", (z, z), 0)
        ImageDraw.Draw(im).ellipse([z / 2 - r, z / 2 - r, z / 2 + r, z / 2 + r], fill=255)
        spr[r] = np.asarray(im.filter(ImageFilter.GaussianBlur(max(1, r * 0.6)))).astype(np.float32) / 255
    return spr[r]
def dust(t, strength):
    m = np.zeros((H, W), np.float32)
    for s in motes:
        x = int((s.x + s.vx * t + 12 * math.sin(t * 0.6 + s.ph)) % W); y = int((s.y + s.vy * t) % H)
        sp = sprite(s.r); h2 = sp.shape[0] // 2
        x0, y0 = max(x - h2, 0), max(y - h2, 0); x1, y1 = min(x + h2, W), min(y + h2, H)
        if x1 <= x0 or y1 <= y0: continue
        m[y0:y1, x0:x1] += sp[y0 - (y - h2):y1 - (y - h2), x0 - (x - h2):x1 - (x - h2)] * s.a * (0.7 + 0.3 * math.sin(t * 1.7 + s.ph))
    return np.clip(m * strength, 0, 1)[..., None]

# 代码层：两团光（独立而相连），用于"成熟的爱情"段
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def two_lights(t, a, cfgl):
    if a <= 0: return None
    cx, cy, sep = W * cfgl.get("cx", 0.5), H * cfgl.get("cy", 0.36), W * cfgl.get("sep", 0.11)
    br = 1 + 0.12 * math.sin(t * 2.0)
    pts = [(cx - sep + 6 * math.sin(t * 0.9), cy + 8 * math.sin(t * 1.1)), (cx + sep + 6 * math.sin(t * 0.8 + 1), cy + 8 * math.sin(t * 1.3 + 2))]
    g = np.zeros((H, W), np.float32)
    for (px, py) in pts:
        d2 = (xx - px) ** 2 + (yy - py) ** 2
        g += np.exp(-d2 / (2 * (26 * br) ** 2)) * 0.9 + np.exp(-d2 / (2 * 90 ** 2)) * 0.35
    # 两团光之间一根细细的光线
    (x0, y0), (x1, y1) = pts
    vx, vy = x1 - x0, y1 - y0; L2 = vx * vx + vy * vy
    u = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1)
    dd = np.sqrt((xx - (x0 + u * vx)) ** 2 + (yy - (y0 + u * vy)) ** 2)
    g += np.exp(-dd ** 2 / (2 * 2.2 ** 2)) * 0.55 * (0.6 + 0.4 * np.sin(u * 12 - t * 4))
    return np.clip(g * a, 0, 1)[..., None]

vign = np.clip(1 - 0.28 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2) - 0.5, 0, 1) ** 1.3, 0, 1)[..., None]
grain = [np.random.normal(0, 5.5, (H, W, 1)).astype(np.float32) for _ in range(5)]
warm = np.array([255, 226, 180], np.float32); leakc = np.array([255, 236, 205], np.float32)
ease = lambda x: (lambda y: y * y * (3 - 2 * y))(min(max(x, 0), 1))

vid = os.path.join(WORK, "video.mp4")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    cur = [s for s in shots if s["t0"] <= t < s["t1"] + s.get("xfade_out", 0)]
    s = [s for s in shots if s["t0"] <= t < s["t1"]] or [shots[-1]]
    s = s[0]; fr = shot_frame(s, t)
    # 叠化：下一镜提前 xfade 秒混入
    j = shots.index(s)
    if j + 1 < len(shots):
        nx = shots[j + 1]; xf = nx.get("xfade", 0)
        if xf and t > s["t1"] - xf:
            k = ease((t - (s["t1"] - xf)) / xf)
            nf = nx["frames"][min(int((t - (s["t1"] - xf)) * FPS), len(nx["frames"]) - 1)].astype(np.float32)
            fr = fr * (1 - k) + nf * k
    fr = grade(fr)
    # 代码层
    fr = fr + (warm - fr) * dust(t, s.get("dust", 0.55)) * 0.85
    if s.get("lights"):
        la = ease((t - s["t0"] - s["lights"].get("delay", 0.5)) / 0.8) * (1 - ease((t - s["t1"] + 0.3) / 0.3) if s is not shots[-1] else 1)
        g = two_lights(t, la, s["lights"])
        if g is not None: fr = fr + (np.array([255, 240, 205], np.float32) - fr) * g
    # 雨丝
    if s.get("rain"):
        rl = np.zeros((H, W), np.float32); rd = ImageDraw.Draw(Image.fromarray(rl))
        rimg = Image.new("L", (W, H), 0); rd = ImageDraw.Draw(rimg)
        rnd = random.Random(int(t * FPS))
        for _ in range(s["rain"].get("n", 90)):
            x = rnd.uniform(0, W); y = rnd.uniform(0, H); ln = rnd.uniform(25, 60)
            rd.line([(x, y), (x - ln * 0.12, y + ln)], fill=rnd.randint(40, 110), width=1)
        rm = np.asarray(rimg.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)[..., None] / 255
        fr = fr + (np.array([200, 215, 235], np.float32) - fr) * rm * s["rain"].get("a", 0.5)
    # 太阳光晕（慢慢呼吸）
    if s.get("flare"):
        fx, fy = s["flare"]["x"] * W, s["flare"]["y"] * H
        pulse = 0.85 + 0.15 * math.sin(t * 2.2)
        d2 = (xx - fx) ** 2 + (yy - fy) ** 2
        g = (np.exp(-d2 / (2 * 70 ** 2)) * 0.55 + np.exp(-d2 / (2 * 260 ** 2)) * 0.25) * pulse * s["flare"].get("a", 1.0)
        # 对角光斑
        for k_, (off, r_) in enumerate([(0.35, 22), (0.6, 14), (0.85, 34)]):
            px, py = fx + (W / 2 - fx) * off * 2, fy + (H / 2 - fy) * off * 2
            g += np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * r_ ** 2)) * 0.12 * pulse
        fr = fr + (np.array([255, 225, 180], np.float32) - fr) * np.clip(g, 0, 1)[..., None]
    # 飘落花瓣
    if s.get("petals"):
        pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pl)
        for q in range(s["petals"].get("n", 22)):
            rq = random.Random(q * 97 + 5)
            x = (rq.uniform(0, W) + 60 * math.sin(t * rq.uniform(0.5, 1.2) + q) + rq.uniform(20, 60) * t) % W
            y = (rq.uniform(0, H) + rq.uniform(40, 110) * t) % H
            sz = rq.uniform(5, 11); ang = t * rq.uniform(1, 3) + q
            pts = [(x + sz * math.cos(ang + a_) * (1 if i_ % 2 == 0 else 0.45), y + sz * math.sin(ang + a_) * (1 if i_ % 2 == 0 else 0.45))
                   for i_, a_ in enumerate(np.linspace(0, 2 * math.pi, 9)[:-1])]
            pd.polygon(pts, fill=(255, rq.randint(170, 205), rq.randint(185, 215), rq.randint(150, 220)))
        pl = pl.filter(ImageFilter.GaussianBlur(0.8)); pa = np.asarray(pl).astype(np.float32)
        fr = over(fr, pa)
    # 镜头切换处的暖色漏光
    for lt in cfg.get("leaks", []):
        lt = lt + LEAD; d_ = abs(t - lt)
        if d_ < 0.35:
            m = (1 - d_ / 0.35) ** 2 * np.exp(-(((xx - W * 0.9) / (W * 0.6)) ** 2 + ((yy - H * 0.2) / (H * 0.5)) ** 2))[..., None]
            fr = fr + (np.array([255, 190, 120], np.float32) - fr) * m * 0.8
    fr = fr * vign
    fr = over(fr, TITLE)
    for k, (zh, en, a, b) in enumerate(subs):
        end = subs[k + 1][2] if k + 1 < len(subs) else T_END - 0.3
        al = min(ease((t - a + 0.04) / 0.14), 1 - ease((t - end + 0.06) / 0.1))
        if al > 0: fr = over(fr, sub_layer(k), al)
    fr = fr + grain[i % 5]
    # 开头从暖白光里出来（接开场的漏光）
    if t < LEAD: m = 1 - ease(t / LEAD) ; fr = fr * (1 - m) + leakc * m
    if t > T_END - 0.25: fr = fr * (1 - ease((t - (T_END - 0.25)) / 0.25))
    p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()

# ---------- 声音：人声 −11 LUFS，Muse 声音统一后比人声低 10 dB，切换处淡入淡出 ----------
def lufs(pth):
    e = subprocess.run(["ffmpeg", "-i", pth, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); return float(v[-1]) if v else -70
L = cfg.get("lufs", -11)
amb = []
for k, s in enumerate(shots):
    if s.get("is_img"): continue
    a = os.path.join(WORK, f"amb{k}.wav"); ln = s["t1"] - s["t0"] + 0.3
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s.get("src_in", 0)), "-i", os.path.join(D, s["file"]), "-t", f"{ln:.3f}",
                    "-ac", "2", "-ar", "44100", "-af", f"afade=t=in:d=0.15,afade=t=out:st={max(ln - 0.3, 0):.3f}:d=0.3", a], check=True)
    g = (L - 10) - lufs(a); g = min(g, 24)
    b = os.path.join(WORK, f"amb{k}g.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"volume={g:.2f}dB,adelay={int(max(s['t0'] - 0.15, 0) * 1000)}:all=1", b], check=True)
    amb.append(b)
vg = L - lufs(voice)
ins = ["-i", vid, "-i", voice] + sum([["-i", a] for a in amb], [])
fc = f"[1:a]volume={vg:.2f}dB,aresample=44100,aformat=channel_layouts=stereo,adelay={int(LEAD * 1000)}:all=1[v];"
fc += "[v]" + "".join(f"[{k + 2}:a]" for k in range(len(amb))) + (f"amix=inputs={len(amb) + 1}:normalize=0:duration=longest," if amb else "") + f"apad,atrim=0:{T_END:.3f},afade=t=out:st={T_END - 0.25:.3f}:d=0.25,alimiter=limit=0.92:level=false[a]"
OUT = os.path.join(D, cfg.get("output", "body.mp4"))
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-shortest", OUT], check=True)
print("done", OUT, f"{T_END:.2f}s")
