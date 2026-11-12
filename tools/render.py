"""Radici reel renderer: 'la serata come una mostra'.
Concept: the night told as a museum visit in four rooms, each a verb:
  INGRESSO entrare / SALA I guardare / SALA II condividere / SALA III ballare
Visual motif: concentric rings (tree rings of the Radici logo) used for
iris transitions and the end card. Captions styled as museum labels.
Usage: render.py PRE_DIR FONT_DIR OUT_VIDEO_NOAUDIO [preview_step]
"""
import sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PRE, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS, DUR = 1080, 1920, 30, 31.0
CREAM = (238, 228, 210)

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_io(p): p = clamp(p); return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def ease_out(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in(p): p = clamp(p); return p ** 3
def lerp(a, b, p): return a + (b - a) * p
def prog(t, a, b): return clamp((t - a) / (b - a))

class Reader:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.idx, self.frame = -1, None
    def get(self, src_t):
        target = min(self.n - 1, max(0, int(round(src_t * self.fps))))
        if target < self.idx:  # rewind (rare)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target); self.idx = target - 1
        while self.idx < target:
            ok, f = self.cap.read()
            if not ok: break
            self.frame = f; self.idx += 1
        return self.frame

readers = {}
def R(key):
    if key not in readers: readers[key] = Reader(f"{PRE}/{key}.mp4")
    return readers[key]

def view(img, z, cx, cy, dx=0.0, dy=0.0):
    """Crop a window of size W/z x H/z centred at normalised (cx,cy), output WxH."""
    z = max(z, 1.0)
    ww, hh = W / z, H / z
    x0 = clamp(cx * W - ww / 2, 0, W - ww); y0 = clamp(cy * H - hh / 2, 0, H - hh)
    M = np.float32([[z, 0, -x0 * z + dx], [0, z, -y0 * z + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def chroma(img, k):
    k = int(round(k))
    if k < 1: return img
    b, g, r = cv2.split(img)
    r = np.roll(r, k, axis=1); b = np.roll(b, -k, axis=1)
    return cv2.merge([b, g, r])

def pulse(t, start, end, period=0.5, amp=0.022, sharp=12):
    if not (start <= t < end): return 0.0
    ph = (t - start) % period
    return amp * math.exp(-ph * sharp)

# ---------------------------------------------------------------- grading
def make_lut(lift, gamma, gain, sat, warm, shadow_tint, hi_tint):
    x = np.arange(256) / 255.0
    s = x + 0.12 * np.sin(2 * np.pi * x) * -0.5 * 0  # placeholder
    base = np.clip(x, 0, 1)
    # filmic S-curve
    sc = 1 / (1 + np.exp(-(base - 0.5) * 5.2)); sc = (sc - sc.min()) / (sc.max() - sc.min())
    base = 0.55 * base + 0.45 * sc
    luts = []
    for ch in range(3):  # B,G,R
        y = lift + (1 - lift) * base ** gamma
        y = y * gain
        sh = (1 - x) ** 2 * shadow_tint[ch]
        hi = x ** 2 * hi_tint[ch]
        y = y + sh + hi + (warm * (x - 0.5) * (1 if ch == 2 else -1 if ch == 0 else 0.15))
        luts.append(np.clip(y * 255, 0, 255).astype(np.uint8))
    return np.stack(luts, 1).reshape(256, 1, 3), sat

LOOKS = {
    # name: lift, gamma, gain, sat, warm, shadow tint BGR, highlight tint BGR
    'ingresso': make_lut(0.035, 0.97, 1.00, 1.05, 0.03, (0.03, 0.02, -0.01), (-0.03, 0.0, 0.03)),
    'guardare': make_lut(0.03, 1.03, 1.02, 1.12, -0.01, (0.05, 0.01, 0.0), (-0.01, 0.0, 0.03)),
    'condividere': make_lut(0.04, 0.92, 1.0, 1.06, 0.05, (0.0, 0.015, 0.02), (-0.05, 0.0, 0.04)),
    'ballare': make_lut(0.025, 1.05, 1.05, 1.15, 0.03, (0.04, 0.0, 0.02), (-0.04, 0.0, 0.05)),
}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2)
VIGNETTE = np.clip(1 - 0.55 * rr ** 2.2, 0.35, 1)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [cv2.GaussianBlur(rng.normal(0, 7.5, (H, W)).astype(np.float32), (0, 0), 0.7) for _ in range(6)]

def grade(img, look, fi, desat=0.0, dark=0.0):
    lut, sat = LOOKS[look]
    img = cv2.LUT(img, lut)
    f = img.astype(np.float32)
    gray = f.mean(2, keepdims=True)
    s = sat * (1 - desat)
    f = gray + (f - gray) * s
    if desat > 0:  # warm sepia tone when desaturating
        f = f + desat * np.array([-10, 0, 12], np.float32)
    # halation: glow of bright areas, warm tint
    small = cv2.resize(img, (W // 6, H // 6), interpolation=cv2.INTER_AREA).astype(np.float32)
    lum = small.mean(2, keepdims=True)
    bright = np.clip((lum - 170) / 85, 0, 1) * small
    glow = cv2.GaussianBlur(bright, (0, 0), 10)
    glow = cv2.resize(glow, (W, H), interpolation=cv2.INTER_LINEAR) * np.array([0.25, 0.4, 0.75], np.float32)
    f = f + glow * 0.55
    f = f * VIGNETTE * (1 - dark)
    f = f + GRAIN[fi % len(GRAIN)][..., None] * (1 - 0.5 * dark)
    return np.clip(f, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- typography
def font(name, size): return ImageFont.truetype(f"{FONTS}/{name}", size)
F_LABEL = font('cg3.ttf', 40)      # SemiBold
F_WORD = font('cg1.ttf', 150)      # Medium Italic
F_WORD_S = font('cg1.ttf', 118)
F_TITLE = font('cg3.ttf', 132)
F_SUB = font('cg0.ttf', 62)        # Italic
F_DATE = font('cg2.ttf', 36)       # Medium

def tracked(draw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + tracking
    return x

def tracked_width(text, fnt, tracking): return sum(fnt.getlength(c) for c in text) + tracking * (len(text) - 1)

def composite(img, layer_rgba):
    """Alpha-composite a full-frame RGBA PIL layer with soft shadow onto BGR img."""
    a = np.asarray(layer_rgba, dtype=np.float32)
    alpha = a[..., 3:4] / 255.0
    if alpha.max() == 0: return img
    shadow = cv2.GaussianBlur(alpha, (0, 0), 9)[..., None] * 0.55
    f = img.astype(np.float32) * (1 - shadow)
    rgb = a[..., [2, 1, 0]]
    f = f * (1 - alpha) + rgb * alpha
    return np.clip(f, 0, 255).astype(np.uint8)

def museum_label(t, t_in, t_out, label, word, small=False):
    """Museum caption: tracked small-caps label, drawn rule, staggered italic word."""
    if not (t_in <= t < t_out): return None
    lt = t - t_in; out = 1 - ease_in(prog(t, t_out - 0.4, t_out))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, yl = 96, 1290
    a_lab = ease_out(prog(lt, 0.1, 0.5)) * out
    tracked(d, (x0, yl + (1 - a_lab) * 10), label, F_LABEL, CREAM + (int(220 * a_lab),), tracking=9)
    rule_w = 150 * ease_io(prog(lt, 0.0, 0.45))
    if rule_w > 1:
        d.rectangle([x0, yl + 64, x0 + rule_w * (0.4 + 0.6 * out), yl + 66], fill=CREAM + (int(230 * out),))
    fnt = F_WORD_S if small else F_WORD
    x = x0 - 4; yw = yl + 78
    for i, ch in enumerate(word):
        p = ease_out(prog(lt, 0.25 + i * 0.035, 0.75 + i * 0.035)) * out
        if p > 0:
            d.text((x, yw + (1 - p) * 34 - (1 - out) * 20), ch, font=fnt, fill=CREAM + (int(255 * p),))
        x += fnt.getlength(ch)
    return lay

def end_card(t, t0):
    lt = t - t0
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = W // 2, 860
    # concentric rings drawn as growing arcs, inner first (tree rings)
    for i, r in enumerate([70, 104, 142, 186, 236, 292]):
        p = ease_io(prog(lt, 0.05 + i * 0.09, 0.85 + i * 0.09))
        if p <= 0: continue
        a = int(170 * (1 - i * 0.11))
        start = -90 + i * 37
        d.arc([cx - r, cy - r, cx + r, cy + r], start, start + 360 * p, fill=CREAM + (a,), width=2 if i else 3)
    # title
    pt = ease_out(prog(lt, 0.55, 1.25))
    title = "RADICI"; tr = 22
    tw = tracked_width(title, F_TITLE, tr)
    tracked(d, (cx - tw / 2, 1210 + (1 - pt) * 24), title, F_TITLE, CREAM + (int(255 * pt),), tracking=tr)
    rw = 200 * ease_io(prog(lt, 0.8, 1.3))
    if rw > 1: d.rectangle([cx - rw / 2, 1378, cx + rw / 2, 1380], fill=CREAM + (220,))
    ps = ease_out(prog(lt, 0.95, 1.6))
    sub = "piccolo museo della natura"
    sw = F_SUB.getlength(sub)
    d.text((cx - sw / 2, 1400 + (1 - ps) * 16), sub, font=F_SUB, fill=CREAM + (int(255 * ps),))
    pd = ease_out(prog(lt, 1.25, 1.9))
    date = "28 · 11 · 2025"; dw = tracked_width(date, F_DATE, 8)
    tracked(d, (cx - dw / 2, 1500), date, F_DATE, CREAM + (int(200 * pd),), tracking=8)
    return lay

def ring_overlay(img, r, cx, cy, alpha, n=3, gap=26):
    if alpha <= 0.01 or r <= 2: return img
    over = img.copy()
    for i in range(n):
        rad = int(r - i * gap)
        if rad > 2: cv2.circle(over, (int(cx), int(cy)), rad, CREAM[::-1], 3 if i == 0 else 2, cv2.LINE_AA)
    return cv2.addWeighted(over, alpha, img, 1 - alpha, 0)

def iris(inner, outer, r, cx=W / 2, cy=H / 2, feather=18):
    mask = np.zeros((H, W), np.float32)
    cv2.circle(mask, (int(cx), int(cy)), max(0, int(r)), 1.0, -1, cv2.LINE_AA)
    mask = cv2.GaussianBlur(mask, (0, 0), feather)[..., None]
    return (inner.astype(np.float32) * mask + outer.astype(np.float32) * (1 - mask)).astype(np.uint8)

SCRIM = np.clip(1 - (((xx - 330) / 760) ** 2 + ((yy - 1430) / 300) ** 2), 0, 1) ** 1.3
SCRIM = cv2.GaussianBlur(SCRIM, (0, 0), 25)[..., None].astype(np.float32)

def scrim(img, a):
    if a <= 0: return img
    return (img.astype(np.float32) * (1 - 0.6 * a * SCRIM)).astype(np.uint8)

RMAX = math.hypot(W / 2, H / 2) + 60
BLACK = np.zeros((H, W, 3), np.uint8)

# ---------------------------------------------------------------- shots
LOGO = (0.43, 0.443)   # logo centre in stabilised sign frame (normalised)

def shot(key, t):
    """Return graded frame for shot key at output time t (before transitions)."""
    if key == 'A':   # sign, slow-motion, pull-out from logo rings
        src = 0.15 + 0.5 * t
        p = ease_io(prog(t, 0.2, 3.7))
        z = lerp(2.7, 1.06, p); cx = lerp(LOGO[0], 0.5, p); cy = lerp(LOGO[1], 0.5, p)
        return view(R('A60').get(src), z, cx, cy), 'ingresso'
    if key == 'B':   # museo sign, slow push toward the arrow
        u = t - 3.65; src = 0.55 * u
        z = lerp(1.04, 1.2, prog(t, 3.65, 7.8)) + 0.35 * ease_in(prog(t, 7.6, 8.2))
        return view(R('B60').get(src), z, 0.6, lerp(0.45, 0.4, prog(t, 3.65, 8.2))), 'ingresso'
    if key == 'C':   # projections
        src = 1.5 + (t - 7.8)
        z = 1.05 + 0.05 * prog(t, 7.8, 12) + pulse(t, 8, 16)
        img = view(R('C').get(src), z, 0.5, 0.42)
        return chroma(img, pulse(t, 8, 16, 2.0, 9, 10)), 'guardare'
    if key == 'D':   # purple projection
        src = 0.5 + (t - 12)
        z = 1.04 + 0.14 * (1 - ease_out(prog(t, 12, 12.45))) + pulse(t, 8, 16) + 0.05 * ease_in(prog(t, 15.3, 16))
        img = view(R('D').get(src), z, 0.5, 0.36)
        return chroma(img, pulse(t, 8, 16, 2.0, 9, 10) + 10 * (1 - prog(t, 12, 12.3))), 'guardare'
    if key == 'E':   # dinner
        src = 0.0 + (t - 16)
        z = lerp(1.02, 1.12, prog(t, 16, 20))
        return view(R('E').get(src), z, 0.5, 0.55), 'condividere'
    if key == 'F':   # crowd, speed ramp + accelerating push
        u = t - 20; src = 0.8 + u + 0.45 * u * u / 1.75
        z = 1.08 + 0.4 * ease_in(prog(t, 20, 21.75)) + pulse(t, 20, 21, 0.25, 0.01) + pulse(t, 21, 21.75, 0.125, 0.012)
        return view(R('F').get(src), z, 0.5, 0.5), 'ballare'
    if key == 'F2':  # crowd on the drop
        src = 3.4 + (t - 22)
        z = 1.06 + 0.16 * (1 - ease_out(prog(t, 22, 22.4))) + pulse(t, 22, 25)
        img = view(R('F').get(src), z, 0.5, 0.5)
        return chroma(img, pulse(t, 22, 25, 1.0, 8, 10)), 'ballare'
    if key == 'G1':  # DJ
        src = 0.9 * (t - 24)
        z = 1.1 + pulse(t, 22, 25) + 0.1 * (1 - ease_out(prog(t, 24, 24.3)))
        img = view(R('G').get(src), z, 0.55, 0.45)
        return chroma(img, pulse(t, 22, 25, 1.0, 8, 10)), 'ballare'
    if key == 'G2':  # DJ arms up, slow motion, then freeze
        src = 0.9 + min(t, 28) - 25
        src = 0.9 + (min(t, 28) - 25) * (1.3 / 3)
        z = lerp(1.06, 1.2, ease_io(prog(t, 25, 28))) + 0.06 * prog(t, 28, 31) + pulse(t, 25, 28, 1.0, 0.012, 6)
        return view(R('G60').get(src), z, 0.56, 0.42), 'ballare'
    raise KeyError(key)

def g(key, t, fi, **kw):
    img, look = shot(key, t)
    return grade(img, look, fi, **kw)

# ---------------------------------------------------------------- timeline
CAPTIONS = [
    (4.45, 7.65, "INGRESSO", "entrare", False),
    (8.25, 11.8, "SALA  I", "guardare", False),
    (16.55, 19.85, "SALA  II", "condividere", True),
    (22.2, 24.9, "SALA  III", "ballare", False),
]

def frame(t, fi):
    if t < 3.65:
        img = g('A', t, fi)
        r = RMAX * ease_out(prog(t, 0.0, 1.3))
        if t < 1.3:
            img = iris(img, BLACK, r)
            img = ring_overlay(img, r, W / 2, H / 2, 0.8 * (1 - prog(t, 0.9, 1.3)))
    elif t < 4.35:   # ring wipe A -> B
        p = ease_io(prog(t, 3.65, 4.35)); r = RMAX * p
        img = iris(g('B', t, fi), g('A', t, fi), r)
        img = ring_overlay(img, r, W / 2, H / 2, 0.9 * math.sin(math.pi * p))
    elif t < 7.85:
        img = g('B', t, fi)
    elif t < 8.15:   # whip up, following the arrow
        p = ease_io(prog(t, 7.85, 8.15))
        b = g('B', t, fi); c = g('C', t, fi)
        off = int(p * H)
        img = np.empty_like(b)
        img[:H - off] = b[off:]; img[H - off:] = c[:off]
        k = int(1 + 160 * math.sin(math.pi * p))
        img = cv2.blur(img, (1, k))
    elif t < 12.0:
        img = g('C', t, fi)
        if t > 11.93: img = cv2.addWeighted(img, 1, np.full_like(img, 255), 0.5 * prog(t, 11.93, 12.0), 0)
    elif t < 15.55:
        img = g('D', t, fi)
        wf = 1 - prog(t, 12.0, 12.18)
        if wf > 0: img = cv2.addWeighted(img, 1 - 0.8 * wf, np.full_like(img, 255), 0.8 * wf, 0)
    elif t < 16.0:   # iris close on D
        p = ease_in(prog(t, 15.55, 16.0)); r = RMAX * (1 - p)
        img = iris(g('D', t, fi), BLACK, r)
        img = ring_overlay(img, r, W / 2, H / 2, 0.85)
    elif t < 20.0:
        img = g('E', t, fi)
        if t < 16.6:  # iris open on dinner
            p = ease_out(prog(t, 16.0, 16.6)); r = RMAX * p
            img = iris(img, BLACK, r)
            img = ring_overlay(img, r, W / 2, H / 2, 0.85 * (1 - p))
    elif t < 21.75:
        img = g('F', t, fi)
        img = chroma(img, 6 * prog(t, 21.0, 21.75))
    elif t < 22.0:
        img = BLACK.copy()
    elif t < 24.0:
        img = g('F2', t, fi)
        wf = 1 - prog(t, 22.0, 22.25)
        if wf > 0: img = cv2.addWeighted(img, 1 - 0.85 * wf, np.full_like(img, 255), 0.85 * wf, 0)
    elif t < 25.0:
        img = g('G1', t, fi)
    elif t < 28.0:
        img = g('G2', t, fi)
    else:            # freeze + end card
        lt = t - 28
        img, look = shot('G2', t)
        blur = 1 + 14 * ease_io(prog(lt, 0.2, 1.4))
        img = cv2.GaussianBlur(img, (0, 0), blur)
        img = grade(img, look, fi, desat=0.85 * ease_io(prog(lt, 0.0, 1.0)), dark=0.6 * ease_io(prog(lt, 0.2, 1.4)))
        wf = 1 - prog(lt, 0.0, 0.3)
        if wf > 0: img = cv2.addWeighted(img, 1 - 0.7 * wf, np.full_like(img, 255), 0.7 * wf, 0)
        img = composite(img, end_card(t, 28.3))
        fo = prog(t, 30.3, 31.0)
        if fo > 0: img = (img.astype(np.float32) * (1 - fo)).astype(np.uint8)
    for (a, b, lab, word, small) in CAPTIONS:
        lay = museum_label(t, a, b, lab, word, small)
        if lay is not None:
            img = scrim(img, ease_io(prog(t, a, a + 0.4)) * (1 - ease_io(prog(t, b - 0.4, b))))
            img = composite(img, lay)
    return img

# ---------------------------------------------------------------- main
if __name__ == '__main__':
    if OUT.endswith('.jpg'):   # single-frame preview(s): OUT pattern with times in argv[4:]
        for ts in sys.argv[4:]:
            t = float(ts); readers.clear()
            cv2.imwrite(OUT.replace('.jpg', f'_{ts}.jpg'), cv2.resize(frame(t, 0), (W // 2, H // 2)))
        sys.exit()
    nframes = int(DUR * FPS)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15',
                          '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for fi in range(nframes):
        t = fi / FPS
        p.stdin.write(frame(t, fi).tobytes())
        if fi % 60 == 0: print(f"{t:5.1f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done")
