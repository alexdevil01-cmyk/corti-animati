"""Score for the Radici reel. 120 BPM, 31 s.
Structure (seconds):
  0-4    INGRESSO a  : pads + bells, filter slowly opening
  4-8    INGRESSO b  : + heartbeat sub, riser 6-8 into the drop
  8-16   SALA I/II   : full groove (guardare)
  16-20  SALA II     : breakdown, filtered, no kick (condividere)
  20-21.75 build     : snare roll + riser, 21.75-22 silence
  22-25  SALA III    : full drop (ballare)
  25-28  half-time   : slow-motion climax
  28-31  coda        : impact + sustained chord, reverb tail
"""
import numpy as np, wave, sys
from scipy import signal

SR = 48000; BEAT = 0.5; DUR = 31.0
N = int(DUR * SR)
rng = np.random.default_rng(7)
T = lambda d: np.arange(int(d * SR)) / SR

def stem(): return np.zeros((N, 2))
pads, bass, drums, bells, fx = stem(), stem(), stem(), stem(), stem()

def add(buf, start, sig, g=1.0, pan=0.0):
    if sig.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        sig = np.stack([sig * l, sig * r], 1) * 1.414
    i = int(start * SR); j = min(N, i + len(sig))
    if j > i: buf[i:j] += sig[: j - i] * g

hz = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------- instruments ----------
def pad(freqs, d):
    tt = T(d); out = np.zeros((len(tt), 2))
    for f in freqs:
        for det, ch in ((-0.004, 0), (0.004, 1), (0.0, 0), (0.0, 1)):
            ph = rng.uniform(0, 6.28)
            s = signal.sawtooth(2 * np.pi * f * (1 + det) * tt + ph)
            out[:, ch] += s
    env = np.minimum(1, tt / 0.6) * np.minimum(1, (d - tt) / 0.5)
    b, a = signal.butter(2, 1800 / (SR / 2))
    out = signal.lfilter(b, a, out, axis=0)
    return out * env[:, None] / (len(freqs) * 2)

def bell(f, d=1.6):
    tt = T(d)
    s = np.sin(2 * np.pi * f * tt + 1.2 * np.sin(2 * np.pi * f * 3.5 * tt) * np.exp(-tt * 6))
    s += 0.3 * np.sin(2 * np.pi * f * 2 * tt)
    return s * np.exp(-tt * 3.2) * np.minimum(1, tt / 0.004)

def kick(big=False):
    tt = T(0.5 if big else 0.32)
    f = 46 + 110 * np.exp(-tt * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * (5 if big else 9))
    click = rng.standard_normal(len(tt)) * np.exp(-tt * 400) * 0.25
    return np.tanh(1.6 * (s + click))

def hat(d=0.06, open_=False):
    tt = T(0.25 if open_ else d)
    x = rng.standard_normal(len(tt))
    b, a = signal.butter(2, 7000 / (SR / 2), 'high'); x = signal.lfilter(b, a, x)
    return x * np.exp(-tt * (14 if open_ else 80)) * 0.5

def clap():
    tt = T(0.25); x = rng.standard_normal(len(tt))
    b, a = signal.butter(2, [900 / (SR / 2), 4000 / (SR / 2)], 'band'); x = signal.lfilter(b, a, x)
    env = np.exp(-tt * 22) + 0.6 * np.exp(-np.maximum(0, tt - 0.012) * 60) * (tt > 0.012)
    return x * env * 1.4

def snare(g=1.0):
    tt = T(0.16); x = rng.standard_normal(len(tt))
    b, a = signal.butter(2, [1500 / (SR / 2), 9000 / (SR / 2)], 'band'); x = signal.lfilter(b, a, x)
    tone = np.sin(2 * np.pi * 190 * tt) * 0.5
    return (x + tone) * np.exp(-tt * 30) * g

def bassnote(f, d):
    tt = T(d)
    s = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * signal.square(2 * np.pi * f * tt)
    return np.tanh(1.3 * s) * np.minimum(1, tt / 0.008) * np.minimum(1, (d - tt) / 0.03)

def riser(d):
    tt = T(d); x = rng.standard_normal(len(tt))
    out = np.zeros_like(x); chunk = 2400; zi = None
    for i in range(0, len(x), chunk):
        p = i / len(x); fc = 300 * (40 ** p)
        sos = signal.butter(2, [fc * 0.7 / (SR / 2), min(0.95, fc * 1.4 / (SR / 2))], 'band', output='sos')
        if zi is None: zi = signal.sosfilt_zi(sos) * 0
        out[i:i + chunk], zi = signal.sosfilt(sos, x[i:i + chunk], zi=zi)
    sweep = np.sin(2 * np.pi * np.cumsum(200 * (8 ** (tt / d))) / SR) * 0.15
    return (out * 2 + sweep) * (tt / d) ** 2

def impact():
    tt = T(2.5)
    boom = np.sin(2 * np.pi * np.cumsum(35 + 60 * np.exp(-tt * 8)) / SR) * np.exp(-tt * 1.6)
    x = rng.standard_normal(len(tt)); b, a = signal.butter(2, 5000 / (SR / 2), 'high')
    crash = signal.lfilter(b, a, x) * np.exp(-tt * 2.2) * 0.35
    return np.tanh(1.4 * boom) + crash

# ---------- harmony ----------
CH = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 52, 55, 59, 64], [55, 59, 62, 64, 67]]  # Am9 Fmaj9 Cmaj7 G6
ROOT = [33, 29, 36, 31]
BELL_LINE = [76, 72, 71, 67, 69, 64, 67, 71]

for bar in range(14):
    t0 = bar * 2.0; c = CH[bar % 4]
    if not (21.75 <= t0 < 22): add(pads, t0, pad([hz(m) for m in c], 2.05), 0.55)

# bells: sparse in intro/breakdown, arp in grooves
for k in range(56):
    t = k * BEAT
    if t >= 28: break
    if t < 8 or 16 <= t < 20:
        if k % 2 == 0: add(bells, t, bell(hz(BELL_LINE[(k // 2) % 8])), 0.22, pan=0.4 * np.sin(k))
    elif 8 <= t < 16 or 22 <= t < 25:
        c = CH[int(t // 2) % 4]
        for s in range(2):
            m = c[(k * 2 + s) % len(c)] + (12 if t >= 22 else 0)
            add(bells, t + s * 0.25, bell(hz(m), 0.6), 0.11, pan=0.5 if s else -0.5)

# heartbeat 4-8
for t in np.arange(4, 8, 1.0):
    k = kick(); b, a = signal.butter(2, 180 / (SR / 2)); k = signal.lfilter(b, a, k)
    add(drums, t, k, 0.7); add(drums, t + 0.18, k, 0.4)

def groove(t_start, t_end, half=False):
    for t in np.arange(t_start, t_end - 1e-6, BEAT):
        k = int(round(t / BEAT))
        if not half or k % 2 == 0: add(drums, t, kick(), 0.85)
        if (k % 2 == 1) if not half else (k % 4 == 2): add(drums, t, clap(), 0.45)
        add(drums, t + BEAT / 2, hat(open_=(t >= 22)), 0.32 if t >= 22 else 0.26, pan=0.2)
        add(drums, t + BEAT / 4, hat(0.03), 0.1, pan=-0.3)
        rt = ROOT[int(t // 2) % 4]
        for off, oct_ in ((0.25, 0), (0.375, 12)) if not half else ((0.0, 0),):
            add(bass, t + off * (2 * BEAT), bassnote(hz(rt + oct_ + 12), 0.2 if not half else 0.9), 0.3)

groove(8, 16); groove(22, 25); groove(25, 28, half=True)

# breakdown hats + soft bass
for t in np.arange(16, 20, BEAT / 2):
    add(drums, t, hat(0.03), 0.08, pan=np.sin(t * 3) * 0.6)
for t in np.arange(16, 20, 2.0):
    add(bass, t, bassnote(hz(ROOT[int(t // 2) % 4] + 12), 1.9), 0.18)

# build snare roll 20-21.75
for t in np.arange(20, 21, 0.25): add(drums, t, snare(), 0.25 + 0.15 * (t - 20))
for t in np.arange(21, 21.75, 0.125): add(drums, t, snare(), 0.4 + 0.3 * (t - 21))

# fx
add(fx, 6.0, riser(2.0), 0.35)
add(fx, 20.0, riser(1.75), 0.4)
for t, g in ((8, 0.55), (22, 0.7), (28, 0.8)): add(fx, t, impact(), g)
add(fx, 12, impact()[:, ] * 0.5, 0.25)
# coda chord
add(pads, 28, pad([hz(m) for m in CH[0] + [81]], 3.0), 0.8)
add(bells, 28, bell(hz(76), 3.0), 0.3); add(bells, 28.5, bell(hz(71), 2.5), 0.2)

# ---------- automation ----------
def tv_lowpass(x, cutoff_fn):
    out = np.zeros_like(x); chunk = 1200; zi = None
    for i in range(0, len(x), chunk):
        fc = cutoff_fn(i / SR)
        sos = signal.butter(2, min(0.95, fc / (SR / 2)), output='sos')
        if zi is None: zi = np.zeros((sos.shape[0], 2, x.shape[1]))
        out[i:i + chunk], zi = signal.sosfilt(sos, x[i:i + chunk], axis=0, zi=zi)
    return out

def cutoff(t):
    if t < 4: return 400 * (8 ** (t / 4))          # opening intro filter
    if t < 8: return 3200 + 6000 * ((t - 4) / 4)
    if 16 <= t < 20: return 700                      # breakdown
    if 20 <= t < 22: return 700 * (25 ** ((t - 20) / 2))
    return 20000

music_bus = pads * 0.9 + bells
music_bus = tv_lowpass(music_bus, cutoff)
bass = tv_lowpass(bass, lambda t: 300 if 16 <= t < 20 else 20000)

tt = np.arange(N) / SR
pump = np.ones(N)
grooving = ((tt >= 8) & (tt < 16)) | ((tt >= 22) & (tt < 25))
pump[grooving] = 1 - 0.45 * np.exp(-((tt[grooving] % BEAT)) * 10)
music_bus *= pump[:, None]; bass *= (0.6 + 0.4 * pump)[:, None]

mix = music_bus + bass + drums + fx * 0.9
# drop gap: silence 21.75-22
gap = (tt >= 21.75) & (tt < 22); mix[gap] *= 0.0
# reverb (send) via convolution with decaying stereo noise
ir_t = T(2.2)
ir = np.stack([rng.standard_normal(len(ir_t)), rng.standard_normal(len(ir_t))], 1) * np.exp(-ir_t * 3)[:, None]
ir /= np.abs(ir).sum(0)
send = music_bus * 0.6 + drums * 0.08 + fx * 0.2
wet = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], 1) * 6
mix = mix + wet * 0.35
fade = np.clip((DUR - tt) / 2.5, 0, 1) ** 1.5
mix *= fade[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6) * 0.9

x = (mix * 32767).astype(np.int16)
w = wave.open(sys.argv[1], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(x.tobytes()); w.close()
print("ok", DUR)
