"""Genera le tavole SVG del blueprint a partire da geometria.py."""
import base64
import math
import os
import sys

import geometria as G

OUT = os.path.join(os.path.dirname(__file__), "..", "tavole")
SW, SH = 1680, 1188                      # A3 orizzontale @ 4 px/mm

# palette blueprint
BG = "#173d6e"
GRID = "#2a5590"
INK = "#eaf3ff"
SOFT = "#9cc0ea"
POCHE = "#d6e7fb"
ACC = "#ffd36b"
FONT = "DejaVu Sans, Liberation Sans, sans-serif"
MONO = "DejaVu Sans Mono, Liberation Mono, monospace"

BOXES = G.build()


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


class View:
    """Mappa coordinate mondo (a, b) -> px. b cresce verso l'alto."""

    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, a, b):
        return self.ox + a * self.s, self.oy - b * self.s

    def rect(self, a0, a1, b0, b1, **st):
        x, y = self.p(min(a0, a1), max(b0, b1))
        return rect(x, y, abs(a1 - a0) * self.s, abs(b1 - b0) * self.s, **st)

    def line(self, a0, b0, a1, b1, **st):
        x0, y0 = self.p(a0, b0)
        x1, y1 = self.p(a1, b1)
        return line(x0, y0, x1, y1, **st)

    def text(self, a, b, t, **st):
        x, y = self.p(a, b)
        return text(x, y, t, **st)

    def poly(self, pts, **st):
        return path("M" + " L".join(f"{self.p(a, b)[0]:.1f},{self.p(a, b)[1]:.1f}" for a, b in pts) + " Z", **st)


def _st(st):
    out = []
    for k, v in st.items():
        out.append(f'{k.replace("_", "-")}="{v}"')
    return " ".join(out)


def rect(x, y, w, h, **st):
    st.setdefault("fill", "none")
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" {_st(st)}/>'


def line(x0, y0, x1, y1, **st):
    st.setdefault("stroke", INK)
    st.setdefault("stroke_width", 1)
    return f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" {_st(st)}/>'


def path(d, **st):
    st.setdefault("fill", "none")
    return f'<path d="{d}" {_st(st)}/>'


def text(x, y, t, size=12, anchor="start", fill=INK, weight="normal", family=FONT, rot=0, **st):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
    t = str(t).replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{fill}" font-weight="{weight}" font-family="{family}"{tr} {_st(st)}>{t}</text>')


# ------------------------------------------------------------------ quote
def dim_h(v, a0, a1, b, off, label=None, size=11):
    """Quota orizzontale tra a0 e a1 alla quota mondo b, spostata di off px."""
    x0, y = v.p(a0, b)
    x1, _ = v.p(a1, b)
    y += off
    o = [line(x0, y, x1, y, stroke=SOFT, stroke_width=0.8)]
    for x in (x0, x1):
        o.append(line(x, y - 5, x, y + 5, stroke=SOFT, stroke_width=0.8))
        o.append(line(x - 3.5, y + 3.5, x + 3.5, y - 3.5, stroke=INK, stroke_width=1.4))
    o.append(text((x0 + x1) / 2, y - 4, label or f(a1 - a0), size=size, anchor="middle", fill=INK, family=MONO))
    return "\n".join(o)


def dim_v(v, b0, b1, a, off, label=None, size=11):
    x, y0 = v.p(a, b0)
    _, y1 = v.p(a, b1)
    x += off
    o = [line(x, y0, x, y1, stroke=SOFT, stroke_width=0.8)]
    for y in (y0, y1):
        o.append(line(x - 5, y, x + 5, y, stroke=SOFT, stroke_width=0.8))
        o.append(line(x - 3.5, y + 3.5, x + 3.5, y - 3.5, stroke=INK, stroke_width=1.4))
    o.append(text(x - 4, (y0 + y1) / 2, label or f(b1 - b0), size=size, anchor="middle",
                  fill=INK, family=MONO, rot=-90))
    return "\n".join(o)


def dim_chain_h(v, stops, b, off, size=10):
    o = []
    for a0, a1 in zip(stops, stops[1:]):
        if a1 - a0 > 1e-6:
            o.append(dim_h(v, a0, a1, b, off, size=size))
    return "\n".join(o)


def dim_chain_v(v, stops, a, off, size=10):
    o = []
    for b0, b1 in zip(stops, stops[1:]):
        if b1 - b0 > 1e-6:
            o.append(dim_v(v, b0, b1, a, off, size=size))
    return "\n".join(o)


def level_mark(v, a, b, label, side=1):
    x, y = v.p(a, b)
    d = f"M{x:.1f},{y:.1f} l{-6 * side},-9 l{12 * side},0 Z"
    return (path(d, fill=ACC, stroke="none") +
            line(x, y, x + 60 * side, y, stroke=ACC, stroke_width=0.8) +
            text(x + 14 * side, y - 4, label, size=10, anchor="start" if side > 0 else "end",
                 fill=ACC, family=MONO))


def section_marker(v, a0, b0, a1, b1, name, arrow_dir):
    """Linea di sezione con frecce di vista. arrow_dir = (da, db) in mondo."""
    o = [v.line(a0, b0, a1, b1, stroke=ACC, stroke_width=1.2, stroke_dasharray="18 5 3 5")]
    for a, b in ((a0, b0), (a1, b1)):
        x, y = v.p(a, b)
        da, db = arrow_dir
        tx, ty = x + da * 22, y - db * 22
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{BG}" stroke="{ACC}" stroke-width="1.4"/>')
        o.append(text(x, y + 5, name, size=13, anchor="middle", fill=ACC, weight="bold"))
        o.append(line(x + da * 13, y - db * 13, tx, ty, stroke=ACC, stroke_width=2,
                      marker_end="url(#arrowA)"))
    return "\n".join(o)


# ----------------------------------------------------------- forme aperture
def portone_path(v, cx, w=2.0, hs=2.6, r_sh=0.25):
    """Arco mistilineo 'a spalle' dei portoni."""
    hw = w / 2
    rc = hw - r_sh
    s = v.s
    p = v.p
    x0, y0 = p(cx - hw, 0)
    xa, ya = p(cx - hw, hs)
    xb, yb = p(cx - rc, hs + r_sh)
    xc, yc = p(cx + rc, hs + r_sh)
    xd, yd = p(cx + hw, hs)
    xe, ye = p(cx + hw, 0)
    return (f"M{x0:.1f},{y0:.1f} L{xa:.1f},{ya:.1f} "
            f"A{r_sh * s:.1f},{r_sh * s:.1f} 0 0 1 {xb:.1f},{yb:.1f} "
            f"A{rc * s:.1f},{rc * s:.1f} 0 0 1 {xc:.1f},{yc:.1f} "
            f"A{r_sh * s:.1f},{r_sh * s:.1f} 0 0 1 {xd:.1f},{yd:.1f} L{xe:.1f},{ye:.1f}")


def arch_path(v, a, b, z0, z1, closed=True):
    r = (b - a) / 2
    zt = z1 - r
    x0, y0 = v.p(a, z0)
    xa, ya = v.p(a, zt)
    xb, yb = v.p(b, zt)
    xe, ye = v.p(b, z0)
    d = (f"M{x0:.1f},{y0:.1f} L{xa:.1f},{ya:.1f} A{r * v.s:.1f},{r * v.s:.1f} 0 0 1 {xb:.1f},{yb:.1f} "
         f"L{xe:.1f},{ye:.1f}")
    return d + (" Z" if closed else "")


def louvers(v, a, b, z0, z1, step=0.13, frame=True, sw=0.8):
    o = []
    if frame:
        o.append(v.rect(a, b, z0, z1, stroke=INK, stroke_width=1.3))
        if b - a > 0.8:
            o.append(v.line((a + b) / 2, z0, (a + b) / 2, z1, stroke=INK, stroke_width=1))
    z = z0 + step
    while z < z1 - step / 2:
        o.append(v.line(a + 0.06, z, b - 0.06, z, stroke=SOFT, stroke_width=sw))
        z += step
    return "\n".join(o)


def draw_opening_elev(v, o, detail=1.0):
    """Disegna un'apertura di facciata in prospetto."""
    out = []
    if o["shape"] == "portone":
        cx = (o["a"] + o["b"]) / 2
        d = portone_path(v, cx)
        # cornice in pietra
        out.append(path(portone_path(v, cx, w=2.36, hs=2.6, r_sh=0.3), stroke=SOFT, stroke_width=1))
        if o["state"] == "aperto":
            out.append(path(d + " Z", fill="#0c2547", stroke=INK, stroke_width=1.8))
            # ante aperte viste di taglio + fondo androne
            for a in (o["a"] + 0.05, o["b"] - 0.17):
                out.append(v.rect(a, a + 0.12, 0, 2.85, fill="#2b5c99", stroke=INK, stroke_width=0.8))
            out.append(path(arch_path(v, 5.55, 6.45, 0, 2.6), stroke=SOFT, stroke_width=0.8,
                            stroke_dasharray="4 3"))
        else:
            out.append(path(d + " Z", fill="#214c86", stroke=INK, stroke_width=1.8))
            out.append(v.line(cx, 0, cx, 3.6, stroke=INK, stroke_width=1.2))
            for side in (-1, 1):
                a0 = cx + side * 0.15
                a1 = cx + side * 0.85
                for z0, z1 in ((0.3, 1.2), (1.4, 2.4)):
                    out.append(v.rect(min(a0, a1), max(a0, a1), z0, z1, stroke=SOFT, stroke_width=0.9))
            out.append(v.line(o["a"], 2.6, o["b"], 2.6, stroke=SOFT, stroke_width=0.8))
    elif o["shape"] == "rect":
        out.append(v.rect(o["a"] - 0.1, o["b"] + 0.1, o["z0"] - 0.12, o["z1"] + 0.1, stroke=SOFT, stroke_width=0.9))
        out.append(v.rect(o["a"] - 0.15, o["b"] + 0.15, o["z0"] - 0.16, o["z0"] - 0.04,
                          fill=BG, stroke=INK, stroke_width=1))  # davanzale
        out.append(louvers(v, o["a"], o["b"], o["z0"], o["z1"]))
    elif o["shape"] == "arch":
        r = (o["b"] - o["a"]) / 2
        zt = o["z1"] - r
        out.append(path(arch_path(v, o["a"] - 0.1, o["b"] + 0.1, o["z0"] - 0.1, o["z1"] + 0.1),
                        stroke=SOFT, stroke_width=0.9))
        out.append(path(arch_path(v, o["a"], o["b"], o["z0"], o["z1"]), fill="#0f2b52", stroke=INK, stroke_width=1.6))
        # telaio vetrato
        out.append(v.line((o["a"] + o["b"]) / 2, o["z0"], (o["a"] + o["b"]) / 2, o["z1"], stroke=SOFT, stroke_width=0.8))
        out.append(v.line(o["a"], zt, o["b"], zt, stroke=SOFT, stroke_width=0.8))
        out.append(v.rect(o["a"] - 0.15, o["b"] + 0.15, o["z0"] - 0.16, o["z0"] - 0.04, fill=BG, stroke=INK, stroke_width=1))
        # persiane piccole aperte
        out.append(louvers(v, o["a"] - 0.52, o["a"] - 0.02, o["z0"], zt, step=0.12))
        out.append(louvers(v, o["b"] + 0.02, o["b"] + 0.52, o["z0"], zt, step=0.12))
    return "\n".join(out)


# ----------------------------------------------------------------- foglio
def defs():
    return f"""<defs>
<pattern id="grid" width="21" height="21" patternUnits="userSpaceOnUse">
<path d="M21 0 L0 0 0 21" fill="none" stroke="{GRID}" stroke-width="0.5"/></pattern>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<line x1="0" y1="0" x2="0" y2="7" stroke="{SOFT}" stroke-width="0.7"/></pattern>
<pattern id="earth" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<line x1="0" y1="0" x2="0" y2="10" stroke="{SOFT}" stroke-width="0.6"/></pattern>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 Z" fill="{INK}"/></marker>
<marker id="arrowA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 Z" fill="{ACC}"/></marker>
</defs>"""


def sheet(num, title, subtitle, body):
    tb_w, tb_h = 520, 118
    tx, ty = SW - 24 - tb_w, SH - 24 - tb_h
    tb = [
        rect(tx, ty, tb_w, tb_h, fill=BG, stroke=INK, stroke_width=1.5),
        line(tx, ty + 40, tx + tb_w, ty + 40, stroke=INK),
        line(tx + 400, ty, tx + 400, ty + tb_h, stroke=INK),
        text(tx + 12, ty + 27, "EDIFICIO A TRE PORTONI — BLUEPRINT", size=16, weight="bold"),
        text(tx + 12, ty + 64, title, size=15, weight="bold", fill=ACC),
        text(tx + 12, ty + 86, subtitle, size=11, fill=SOFT),
        text(tx + 12, ty + 106, "Misure in unità di griglia u (proporzioni) — 1 u ≈ 1 m consigliato",
             size=10, fill=SOFT, family=MONO),
        text(tx + 460, ty + 26, "TAV.", size=11, anchor="middle", fill=SOFT),
        text(tx + 460, ty + 90, f"{num:02d}", size=44, anchor="middle", weight="bold"),
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}">
{defs()}
<rect width="{SW}" height="{SH}" fill="{BG}"/>
<rect width="{SW}" height="{SH}" fill="url(#grid)"/>
<rect x="12" y="12" width="{SW - 24}" height="{SH - 24}" fill="none" stroke="{INK}" stroke-width="2"/>
<rect x="18" y="18" width="{SW - 36}" height="{SH - 36}" fill="none" stroke="{INK}" stroke-width="0.6"/>
{body}
{''.join(tb)}
</svg>"""


def caption(x, y, title, scale_note=""):
    return (text(x, y, title, size=17, weight="bold") +
            line(x, y + 6, x + max(260, len(title) * 10), y + 6, stroke=INK, stroke_width=1.5) +
            (text(x, y + 22, scale_note, size=10, fill=SOFT, family=MONO) if scale_note else ""))


def scale_bar(v, a, b, n=5):
    o = []
    for i in range(n):
        o.append(v.rect(a + i, a + i + 1, b, b + 0.12, fill=INK if i % 2 == 0 else BG, stroke=INK, stroke_width=0.8))
        o.append(v.text(a + i, b - 0.35, str(i), size=9, anchor="middle", family=MONO))
    o.append(v.text(a + n, b - 0.35, f"{n} u", size=9, anchor="middle", family=MONO))
    return "\n".join(o)


# ================================================================== PIANTA
def plan(v, lvl, show_cuts=False):
    z = G.LEVELS[lvl]
    zcut = z + 1.2
    nxt = G.LEVEL_ORDER[G.LEVEL_ORDER.index(lvl) + 1]
    ztop = G.LEVELS[nxt]
    o = []
    # sfondo pianta (pavimento)
    o.append(v.rect(0, G.W, 0, G.D, fill="#1b4479", stroke="none"))
    # vuoti del solaio a questo livello -> si vede il piano sotto
    for x0, x1, y0, y1 in G.VOIDS.get(lvl, []):
        o.append(v.rect(x0, x1, y0, y1, fill="#10305a", stroke=SOFT, stroke_width=0.8, stroke_dasharray="6 4"))
    # gradini e pianerottoli
    for b in BOXES:
        if b["tag"] not in ("gradino", "pianerottolo"):
            continue
        if b["tag"] == "pianerottolo":
            top = b["z1"]
            if z < top < ztop:
                dashed = top > zcut
                o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], fill="#1f4c86" if not dashed else "none",
                                stroke=INK, stroke_width=1, **({"stroke_dasharray": "5 3"} if dashed else {})))
            continue
        top = b["z1"]
        own = b["lvl"] == lvl
        below_in_void = top <= z + 1e-6 and any(
            x0 <= b["x0"] + 1e-6 and b["x1"] <= x1 + 1e-6 and y0 - 1e-6 <= b["y0"] and b["y1"] <= y1 + 1e-6
            for x0, x1, y0, y1 in G.VOIDS.get(lvl, []))
        if own and top <= zcut:
            o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], fill="#1f4c86", stroke=INK, stroke_width=0.9))
        elif own:
            o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], stroke=SOFT, stroke_width=0.7, stroke_dasharray="4 3"))
        elif below_in_void:
            o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], stroke=SOFT, stroke_width=0.5, opacity=0.7))
    # linea di taglio sulle rampe in salita
    for fl in G.FLIGHTS:
        if fl["lvl"] != lvl:
            continue
        r = (fl["z1"] - fl["z0"]) / fl["n"]
        k = (zcut - fl["z0"]) / r
        if 0 < k < fl["n"] - 1:
            yc = fl["y0"] + fl["dir"] * k * G.TREAD
            xa, xb = fl["x0"], fl["x1"]
            o.append(v.poly([(xa, yc - 0.1), (xa + (xb - xa) * 0.45, yc - 0.1), (xa + (xb - xa) * 0.52, yc + 0.15),
                             (xa + (xb - xa) * 0.58, yc - 0.35), (xa + (xb - xa) * 0.62, yc - 0.1), (xb, yc - 0.1),
                             (xb, yc - 0.1)], stroke=INK, stroke_width=1.2))
    # frecce di salita
    for fl in G.FLIGHTS:
        if fl["lvl"] != lvl:
            continue
        xm = (fl["x0"] + fl["x1"]) / 2
        ye = G.flight_end(fl)
        y_start = fl["y0"] + fl["dir"] * 0.15
        o.append(v.line(xm, y_start, xm, ye - fl["dir"] * 0.15, stroke=ACC, stroke_width=1.3,
                        marker_end="url(#arrowA)"))
        o.append(f'<circle cx="{v.p(xm, y_start)[0]:.1f}" cy="{v.p(xm, y_start)[1]:.1f}" r="3" fill="{ACC}"/>')
    # ringhiere
    for b in BOXES:
        if b["tag"] == "ringhiera" and b.get("lvl") == lvl:
            o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], fill=INK, stroke=INK, stroke_width=0.8))
    # scala a pioli / botola
    if lvl == "P3":
        L = G.LADDER
        o.append(v.rect(L["x0"], L["x1"], L["y"] - 0.05, L["y"] + 0.05, fill=ACC, stroke="none"))
        x0, x1, y0, y1 = G.VOIDS["COP"][0]
        o.append(v.rect(x0, x1, y0, y1, stroke=ACC, stroke_width=1.2, stroke_dasharray="5 3"))
        o.append(v.line(x0, y0, x1, y1, stroke=ACC, stroke_width=0.8, stroke_dasharray="5 3"))
        o.append(v.line(x0, y1, x1, y0, stroke=ACC, stroke_width=0.8, stroke_dasharray="5 3"))
        o.append(v.text(9.7, 8.3, "BOTOLA (sopra)", size=10, anchor="middle", fill=ACC))
        o.append(v.text(9.7, 7.95, "scala alla marinara", size=9, anchor="middle", fill=ACC))
    # portoni (ante)
    if lvl == "PT":
        for op in G.FRONT_OPENINGS:
            if op["shape"] != "portone":
                continue
            if op["state"] == "chiuso":
                o.append(v.rect(op["a"], op["b"], 0.2, 0.3, fill=SOFT, stroke=INK, stroke_width=0.8))
            else:
                for a, sgn in ((op["a"], 1), (op["b"], -1)):
                    o.append(v.rect(a, a + sgn * 0.06, 0.5, 1.5, fill=INK, stroke=INK, stroke_width=0.8))
                    x0, y0 = v.p(a, 1.5)
                    x1, y1 = v.p(a + sgn * 1.0, 0.5)
                    o.append(path(f"M{x0:.1f},{y0:.1f} A{v.s:.1f},{v.s:.1f} 0 0 {1 if sgn > 0 else 0} {x1:.1f},{y1:.1f}",
                                  stroke=SOFT, stroke_width=0.7, stroke_dasharray="3 3"))
    # muri tagliati (poché)
    for b in BOXES:
        if b["tag"] == "muro" and b["z0"] < zcut < b["z1"]:
            o.append(v.rect(b["x0"], b["x1"], b["y0"], b["y1"], fill=POCHE, stroke="none"))
    # contorno muri: perimetro esterno e muri in comune
    o.append(v.line(0, 0, 0, G.D, stroke=INK, stroke_width=1.6))
    o.append(v.line(G.W, 0, G.W, G.D, stroke=INK, stroke_width=1.6))
    # finestre in pianta
    for op in G.FRONT_OPENINGS:
        if op["lvl"] != lvl or op["shape"] == "portone":
            continue
        o.append(v.line(op["a"], 0.22, op["b"], 0.22, stroke=INK, stroke_width=0.8))
        o.append(v.line(op["a"], 0.30, op["b"], 0.30, stroke=INK, stroke_width=0.8))
        o.append(v.line(op["a"], 0.0, op["b"], 0.0, stroke=INK, stroke_width=0.8))
        if op["shape"] == "arch":   # persiane piccole aperte
            o.append(v.rect(op["a"] - 0.5, op["a"], -0.06, 0, fill=SOFT, stroke="none"))
            o.append(v.rect(op["b"], op["b"] + 0.5, -0.06, 0, fill=SOFT, stroke="none"))
        else:
            o.append(v.rect(op["a"], op["b"], -0.06, 0, fill=SOFT, stroke="none"))
    # muri in comune: tratteggio "edificio adiacente"
    for a0, a1 in ((-0.9, 0), (G.W, G.W + 0.9)):
        o.append(v.rect(a0, a1, 0, G.D, fill="url(#hatch)", stroke=SOFT, stroke_width=0.6, stroke_dasharray="4 4"))
    o.append(v.text(-0.45, G.D / 2, "EDIFICIO ADIACENTE", size=9, anchor="middle", fill=SOFT, rot=-90))
    o.append(v.text(G.W + 0.45, G.D / 2, "EDIFICIO ADIACENTE", size=9, anchor="middle", fill=SOFT, rot=-90))
    # etichette ambienti
    for bay, name, a, b in G.ROOMS[lvl]:
        o.append(v.text(a, b, name, size=11, anchor="middle", weight="bold"))
        bx0, bx1 = G.BAYS[bay]
        o.append(v.text(a, b - 0.38, f"luce {f(bx1 - bx0)} u", size=9, anchor="middle",
                        fill=SOFT, family=MONO))
    # quote altimetriche
    o.append(v.text(0.75, 0.9, f"+{f(z)}", size=10, fill=ACC, family=MONO))
    # vuoti: etichetta
    labels = {"P1": (10.85, 5.0, "VUOTO"), "P2": (6.0, 7.6, "VUOTO SCALA"), "P3": (10.85, 5.0, "VUOTO")}
    if lvl in labels:
        a, b, t = labels[lvl]
        o.append(v.text(a, b, t, size=9, anchor="middle", fill=SOFT, rot=-90 if lvl != "P2" else 0))
    # quote planimetriche
    o.append(dim_chain_h(v, [0, 0.5, 3.85, 4.15, 7.85, 8.15, 11.5, 12], 0, 34, size=9))
    o.append(dim_h(v, 0, G.W, 0, 62))
    stops = sorted({0.0, G.W} | {round(x, 3) for op in G.FRONT_OPENINGS if op["lvl"] == lvl for x in (op["a"], op["b"])})
    o.append(dim_chain_h(v, stops, G.D, -14, size=8) if False else "")
    o.append(dim_chain_v(v, [0, 0.5, 9.5, 10], G.W, 62, size=9))
    o.append(dim_v(v, 0, G.D, G.W, 90))
    # fronte strada
    x, y = v.p(G.W / 2, 0)
    o.append(text(x, y + 132, "▼  FRONTE STRADA  ▼", size=11, anchor="middle", fill=SOFT, weight="bold"))
    # marcatori di sezione
    if show_cuts:
        o.append(section_marker(v, 6.0, -1.9, 6.0, G.D + 0.9, "A", (-1, 0)))
        o.append(section_marker(v, 10.6, -1.9, 10.6, G.D + 0.9, "B", (-1, 0)))
        o.append(section_marker(v, -1.4, 7.5, G.W + 2.2, 7.5, "C", (0, 1)))
    return "\n".join(o)


# ============================================================== PROSPETTO
def elevation(v):
    o = []
    # edifici adiacenti (fantasma)
    for a0, a1 in ((-2.6, 0), (G.W, G.W + 2.6)):
        o.append(v.rect(a0, a1, 0, G.PARAPET_TOP, fill="url(#hatch)", stroke=SOFT, stroke_width=0.6,
                        stroke_dasharray="5 4", opacity=0.6))
    o.append(v.text(-1.3, 7.5, "EDIFICIO ADIACENTE UGUALE", size=10, anchor="middle", fill=SOFT, rot=-90))
    o.append(v.text(G.W + 1.3, 7.5, "EDIFICIO ADIACENTE UGUALE", size=10, anchor="middle", fill=SOFT, rot=-90))
    # sagoma
    o.append(v.rect(0, G.W, 0, G.PARAPET_TOP, fill="#1d4880", stroke=INK, stroke_width=2))
    # basamento (zoccolo)
    o.append(v.rect(0, G.W, 0, 0.6, fill="url(#hatch)", stroke=INK, stroke_width=1))
    # marcapiani
    for lvl in ("P1", "P2", "P3"):
        zz = G.LEVELS[lvl]
        o.append(v.rect(0, G.W, zz - 0.3, zz, fill="#2a5a98", stroke=INK, stroke_width=1))
    # cornicione + parapetto
    zc = G.LEVELS["COP"]
    o.append(v.rect(-0.15, G.W + 0.15, zc - 0.3, zc + 0.15, fill="#2a5a98", stroke=INK, stroke_width=1.3))
    o.append(v.rect(0, G.W, G.PARAPET_TOP - 0.15, G.PARAPET_TOP, fill="#2a5a98", stroke=INK, stroke_width=1))
    # lesene sulle linee dei muri interni (scansione delle campate)
    for xm in (4.0, 8.0):
        o.append(v.line(xm, 0.6, xm, zc - 0.3, stroke=SOFT, stroke_width=0.6, stroke_dasharray="2 5"))
    # aperture
    for op in G.FRONT_OPENINGS:
        o.append(draw_opening_elev(v, op))
    # linea di terra
    o.append(v.rect(-3.2, G.W + 3.2, -0.5, 0, fill="url(#earth)", stroke="none"))
    o.append(v.line(-3.2, 0, G.W + 3.2, 0, stroke=INK, stroke_width=2.5))
    # quote
    stops = [0.0] + [x for op in G.FRONT_OPENINGS if op["lvl"] == "PT" for x in (op["a"], op["b"])] + [G.W]
    o.append(dim_chain_h(v, stops, 0, 40, size=9))
    o.append(dim_h(v, 0, G.W, 0, 68))
    stops = [0, 0.5, 4.0, 8.0, 11.5, 12]
    zs = [0, 3.6, 4.5, 5.4, 7.4, 8.1, 9.0, 11.0, 11.7, 12.3, 13.9, 14.5, 15.5]
    o.append(dim_chain_v(v, zs, -2.6, -18, size=8))
    o.append(dim_chain_v(v, [0, 4.5, 8.1, 11.7, 14.5, 15.5], G.W + 2.6, 22, size=9))
    o.append(dim_v(v, 0, G.PARAPET_TOP, G.W + 2.6, 50))
    for lvl in ("PT", "P1", "P2", "P3", "COP"):
        o.append(level_mark(v, G.W + 2.6, G.LEVELS[lvl], f"{lvl} +{f(G.LEVELS[lvl])}", side=1))
    # richiami
    callouts = [
        (2.175, 1.8, -3.4, 2.2, "PORTONE CHIUSO"),
        (6.0, 1.5, 6.0, -2.5, "PORTONE D'INGRESSO APRIBILE"),
        (9.825, 1.8, G.W + 3.4, 1.2, "PORTONE CHIUSO"),
        (2.175, 10.0, -3.4, 10.4, "PERSIANE LUNGHE (tipo A)"),
        (6.5, 13.0, 6.5, 16.9, "FINESTRE AD ARCO + PERSIANE PICCOLE (tipo B)"),
        (2.175, 13.1, -3.4, 13.7, "PERSIANA LUNGA (tipo C)"),
    ]
    for a, b, ta, tb, t in callouts:
        o.append(v.line(a, b, ta, tb, stroke=ACC, stroke_width=0.8))
        o.append(f'<circle cx="{v.p(a, b)[0]:.1f}" cy="{v.p(a, b)[1]:.1f}" r="2.5" fill="{ACC}"/>')
        anchor = "end" if ta < 0 else ("start" if ta > G.W else "middle")
        dy = -5 if tb > b else 14
        x, y = v.p(ta, tb)
        o.append(text(x + (-4 if anchor == "end" else 4 if anchor == "start" else 0), y + dy, t,
                      size=10, anchor=anchor, fill=ACC, weight="bold"))
    return "\n".join(o)


# ================================================================ SEZIONI
def section(v, axis, c, lim, look_neg, title_side=None):
    """axis='x': piano x=c, asse orizzontale = y (fronte a sinistra).
       axis='y': piano y=c, asse orizzontale = x.
       lim: limite della profondità visibile oltre il taglio."""
    o = []
    hz = "y" if axis == "x" else "x"

    def h(b, k):
        return b[f"{hz}{k}"]

    def depth_ok(b):
        lo, hi = b[f"{axis}0"], b[f"{axis}1"]
        if look_neg:
            return hi <= c + 1e-6 and lo >= lim - 1e-6
        return lo >= c - 1e-6 and hi <= lim + 1e-6

    extent = G.D if axis == "x" else G.W
    o.append(v.rect(0, extent, 0, G.PARAPET_TOP, fill="#1b4479", stroke="none"))
    # elementi in vista oltre il taglio
    beyond_tags = ("gradino", "pianerottolo", "ringhiera", "scala-pioli", "portone-aperto", "portone-chiuso")
    for b in BOXES:
        if b["tag"] == "ringhiera" and depth_ok(b):
            o.append(v.rect(h(b, 0), h(b, 1), b["z0"], b["z1"], stroke=INK, stroke_width=1))
            o.append(v.line(h(b, 0), b["z1"] - 0.08, h(b, 1), b["z1"] - 0.08, stroke=INK, stroke_width=0.6))
            continue
        if b["tag"] in beyond_tags and depth_ok(b):
            o.append(v.rect(h(b, 0), h(b, 1), b["z0"], b["z1"], fill="#23518c", stroke=SOFT, stroke_width=0.7))
    # aperture nei muri paralleli al piano, in vista
    if axis == "x":
        wall = G.WALL_L if (look_neg and lim <= 4.2) else G.WALL_R
        ops = G.WALL_L_OPENINGS if wall == G.WALL_L else G.WALL_R_OPENINGS
    else:
        ops = G.BACK_OPENINGS
    for op in ops:
        o.append(path(arch_path(v, op["a"], op["b"], op["z0"], op["z1"]), fill="#10305a",
                      stroke=SOFT, stroke_width=0.9))
    # ingombro solai/muri in vista (linee di livello)
    for lvl in ("P1", "P2", "P3", "COP"):
        zz = G.LEVELS[lvl]
        o.append(v.line(0, zz - G.SLAB, extent, zz - G.SLAB, stroke=SOFT, stroke_width=0.4, stroke_dasharray="2 4"))
    # elementi tagliati
    for b in BOXES:
        if b[f"{axis}0"] < c < b[f"{axis}1"]:
            if b["tag"] in ("muro", "solaio", "pianerottolo", "gradino", "marcapiano", "cornicione"):
                o.append(v.rect(h(b, 0), h(b, 1), b["z0"], b["z1"], fill=POCHE, stroke="none"))
            elif b["tag"] in ("persiana", "portone-chiuso", "portone-aperto", "ringhiera", "scala-pioli"):
                o.append(v.rect(h(b, 0), h(b, 1), b["z0"], b["z1"], fill=INK, stroke="none"))
    # terreno
    o.append(v.rect(-1.5 if axis == "x" else -1.2, extent + 1.2, -0.9, -0.3, fill="url(#earth)", stroke="none"))
    o.append(v.line(-1.5 if axis == "x" else -1.2, 0, extent + 1.2, 0, stroke=INK, stroke_width=1.5))
    # edifici adiacenti nelle sezioni trasversali
    if axis == "y":
        for a0, a1 in ((-1.2, 0), (G.W, G.W + 1.2)):
            o.append(v.rect(a0, a1, 0, G.PARAPET_TOP, fill="url(#hatch)", stroke=SOFT, stroke_width=0.6,
                            stroke_dasharray="4 4", opacity=0.6))
    # quote
    o.append(dim_chain_v(v, [0, 4.2, 4.5, 7.8, 8.1, 11.4, 11.7, 14.2, 14.5, 15.5], extent, 26, size=8))
    for lvl in ("PT", "P1", "P2", "P3", "COP"):
        o.append(level_mark(v, 0, G.LEVELS[lvl], f"+{f(G.LEVELS[lvl])}", side=-1))
    if axis == "x":
        o.append(dim_chain_h(v, [0, 0.5, 9.5, 10], 0, 30, size=9))
        x, y = v.p(0, 0)
        o.append(text(x, y + 60, "FRONTE", size=10, anchor="middle", fill=SOFT))
        x, y = v.p(G.D, 0)
        o.append(text(x, y + 60, "RETRO", size=10, anchor="middle", fill=SOFT))
    else:
        o.append(dim_chain_h(v, [0, 0.5, 3.85, 4.15, 7.85, 8.15, 11.5, 12], 0, 30, size=8))
    return "\n".join(o)


def stair_notes(v, axis):
    o = []
    if axis == "A":
        o.append(v.text(6.6, 5.0, "rampa centrale 10 alzate", size=9, anchor="middle", fill=ACC))
        o.append(v.text(8.75, 6.75, "pianerottolo +6.3", size=9, anchor="middle", fill=ACC))
        o.append(v.text(6.6, 7.2, "braccio sx in vista (10 alz.)", size=9, anchor="middle", fill=ACC))
    if axis == "B":
        o.append(v.text(5.0, 1.0, "rampa PT→P1 · 26 alzate", size=9, anchor="middle", fill=ACC))
        o.append(v.text(4.9, 9.3, "rampa P2→P3 · 20 alzate", size=9, anchor="middle", fill=ACC))
        o.append(v.text(8.6, 15.1, "botola", size=9, anchor="middle", fill=ACC))
    return "\n".join(o)


# ================================================================ TAVOLE
def tav_piante(num, levels):
    body = []
    s = 50
    for i, lvl in enumerate(levels):
        ox = 140 + i * 800
        oy = 720
        v = View(ox, oy, s)
        names = {"PT": "PIANTA PIANO TERRA", "P1": "PIANTA PIANO PRIMO",
                 "P2": "PIANTA PIANO SECONDO", "P3": "PIANTA PIANO TERZO"}
        body.append(caption(ox - 60, 80, f"{names[lvl]}  (quota +{f(G.LEVELS[lvl])})",
                            "piano di taglio a +1.2 u dal pavimento"))
        body.append(plan(v, lvl, show_cuts=(lvl == "PT")))
        body.append(scale_bar(v, 0, -3.3))
    body.append(legend(60, 1010))
    titles = {("PT", "P1"): ("PIANTE: PIANO TERRA E PIANO PRIMO", "Androne, vano scala, attacco della scala imperiale"),
              ("P2", "P3"): ("PIANTE: PIANO SECONDO E PIANO TERZO", "Arrivo dei bracci, rampa per il terzo piano, botola")}
    t, st = titles[tuple(levels)]
    return sheet(num, t, st, "\n".join(body))


def legend(x, y):
    items = [
        ("poche", "muratura tagliata"),
        ("void", "vuoto nel solaio (doppia altezza)"),
        ("step", "gradini sotto il piano di taglio"),
        ("dash", "elementi sopra il piano di taglio"),
        ("arrow", "senso di salita delle rampe"),
        ("hatch", "edificio adiacente (muro in comune)"),
    ]
    o = [text(x, y, "LEGENDA", size=13, weight="bold")]
    for i, (k, t) in enumerate(items):
        cx = x + (i % 3) * 300
        cy = y + 22 + (i // 3) * 26
        if k == "poche":
            o.append(rect(cx, cy, 30, 14, fill=POCHE))
        elif k == "void":
            o.append(rect(cx, cy, 30, 14, fill="#10305a", stroke=SOFT, stroke_dasharray="6 4"))
        elif k == "step":
            o.append(rect(cx, cy, 30, 14, fill="#1f4c86", stroke=INK))
            o.append(line(cx + 10, cy, cx + 10, cy + 14))
            o.append(line(cx + 20, cy, cx + 20, cy + 14))
        elif k == "dash":
            o.append(rect(cx, cy, 30, 14, stroke=SOFT, stroke_dasharray="4 3"))
        elif k == "arrow":
            o.append(line(cx, cy + 7, cx + 30, cy + 7, stroke=ACC, stroke_width=1.3, marker_end="url(#arrowA)"))
        elif k == "hatch":
            o.append(rect(cx, cy, 30, 14, fill="url(#hatch)", stroke=SOFT, stroke_dasharray="4 4"))
        o.append(text(cx + 40, cy + 11, t, size=11))
    return "\n".join(o)


def tav_prospetto_sezC(num):
    body = []
    s = 40
    v = View(330, 990, s)
    body.append(caption(80, 150, "PROSPETTO PRINCIPALE (FRONTE STRADA)", "vista frontale · facciata continua con gli edifici adiacenti"))
    body.append(elevation(v))
    body.append(scale_bar(v, 0, -2.3))
    v2 = View(1120, 990, s)
    body.append(caption(1080, 150, "SEZIONE C-C (TRASVERSALE)", "taglio a y = 7.5 u · vista verso il retro"))
    body.append(section(v2, "y", 7.5, 9.5, look_neg=False))
    notes = [(9.2, 2.2, "rampa PT→P1"), (6.0, 5.3, "rampa centrale"), (4.65, 7.0, "braccio"),
             (7.35, 7.0, "braccio"), (9.2, 10.4, "rampa P2→P3"), (6.0, 1.3, "arco sul fondo")]
    for a, b, t in notes:
        body.append(v2.text(a, b, t, size=9, anchor="middle", fill=ACC))
    return sheet(num, "PROSPETTO PRINCIPALE E SEZIONE TRASVERSALE C-C",
                 "Tre portoni al piano terra, persiane lunghe ai piani 1-2, finestre ad arco al piano 3", "\n".join(body))


def tav_copertura_sezioni(num):
    body = []
    s = 34
    v = View(100, 600, s)
    body.append(caption(70, 80, "PIANTA DELLA COPERTURA", "tetto piano praticabile (terrazza) con parapetto h 1.0 u"))
    o = [v.rect(-0.9, 0, 0, G.D, fill="url(#hatch)", stroke=SOFT, stroke_dasharray="4 4"),
         v.rect(G.W, G.W + 0.9, 0, G.D, fill="url(#hatch)", stroke=SOFT, stroke_dasharray="4 4"),
         v.rect(0, G.W, 0, G.D, fill=POCHE, stroke=INK, stroke_width=1.5),
         v.rect(0.5, 11.5, 0.5, 9.5, fill="#1f4c86", stroke=INK, stroke_width=1)]
    x0, x1, y0, y1 = G.VOIDS["COP"][0]
    o.append(v.rect(x0, x1, y0, y1, fill="#0c2547", stroke=ACC, stroke_width=1.5))
    o.append(v.line(x0, y0, x1, y1, stroke=ACC))
    o.append(v.line(x0, y1, x1, y0, stroke=ACC))
    o.append(v.text(9.9, 8.85, "BOTOLA 0.8×0.8", size=10, anchor="end", fill=ACC, weight="bold"))
    o.append(v.text(6.0, 5.0, "TERRAZZA PRATICABILE", size=12, anchor="middle", weight="bold"))
    o.append(v.text(6.0, 4.55, "pendenza verso pluviali ≈ 1-2%", size=9, anchor="middle", fill=SOFT, family=MONO))
    o.append(v.text(6.0, 0.15, "parapetto", size=9, anchor="middle", fill=BG))
    o.append(dim_h(v, 0, G.W, 0, 34))
    o.append(dim_v(v, 0, G.D, G.W, 32))
    x, y = v.p(G.W / 2, 0)
    o.append(text(x, y + 66, "▼  FRONTE STRADA  ▼", size=11, anchor="middle", fill=SOFT, weight="bold"))
    body += o
    body.append(scale_bar(v, 0, -2.6))
    s = 40
    va = View(690, 960, s)
    body.append(caption(620, 80, "SEZIONE A-A", "taglio a x = 6.0 u (campata centrale) · scala imperiale"))
    body.append(section(va, "x", 6.0, 4.15, look_neg=True))
    body.append(stair_notes(va, "A"))
    vb = View(1235, 960, s)
    body.append(caption(1170, 80, "SEZIONE B-B", "taglio a x = 10.6 u (campata destra) · rampe e botola"))
    body.append(section(vb, "x", 10.6, 8.15, look_neg=True))
    body.append(stair_notes(vb, "B"))
    return sheet(num, "COPERTURA E SEZIONI LONGITUDINALI A-A, B-B",
                 "Scala imperiale (A-A) · rampe sovrapposte e botola (B-B)", "\n".join(body))


def tav_dettagli(num, iso_files):
    body = []
    body.append(caption(60, 80, "ASSONOMETRIE DI RIFERIMENTO", "render del modello geometrico (modello/edificio.obj)"))
    x = 50
    for fn, lab in iso_files:
        if os.path.exists(fn):
            with open(fn, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode()
            body.append(f'<image x="{x}" y="110" width="520" height="560" href="data:image/png;base64,{b64}"/>')
        body.append(rect(x, 110, 520, 560, stroke=SOFT, stroke_width=0.8))
        body.append(text(x + 10, 690, lab, size=11, fill=SOFT))
        x += 540
    # dettagli in scala maggiore
    s = 60
    vx = 1150
    body.append(caption(vx, 80, "DETTAGLI APERTURE", "scala maggiore · misure in u"))
    vp = View(vx + 40, 420, s)
    op = dict(shape="portone", a=-1.0, b=1.0, z0=0, z1=3.6, state="chiuso")
    shifted = lambda d, dx: dict(d, a=d["a"] + dx, b=d["b"] + dx)
    body.append(draw_opening_elev(vp, shifted(op, 1.2)))
    body.append(vp.line(-0.2, 0, 2.6, 0, stroke=INK, stroke_width=2))
    body.append(dim_h(vp, 0.2, 2.2, 0, 22, size=9))
    body.append(dim_v(vp, 0, 2.6, 2.2, 22, size=9))
    body.append(dim_v(vp, 0, 3.6, 2.2, 48, size=9))
    body.append(vp.text(1.2, 4.25, "PORTONE · arco mistilineo a spalle", size=11, anchor="middle", weight="bold", fill=ACC))
    body.append(vp.text(1.2, 3.95, "spalle r 0.25 · calotta r 0.75", size=9, anchor="middle", fill=SOFT, family=MONO))
    vw = View(vx + 300, 420, s)
    body.append(draw_opening_elev(vw, dict(shape="rect", a=0.5, b=1.6, z0=0.8, z1=2.8)))
    body.append(dim_h(vw, 0.5, 1.6, 0.6, 26, size=9))
    body.append(dim_v(vw, 0.8, 2.8, 1.6, 24, size=9))
    body.append(vw.text(1.05, 4.25, "TIPO A · persiana lunga", size=11, anchor="middle", weight="bold", fill=ACC))
    body.append(vw.text(1.05, 3.95, "piani 1 e 2 · davanzale +0.9", size=9, anchor="middle", fill=SOFT, family=MONO))
    vb = View(vx + 40, 700, s)
    body.append(draw_opening_elev(vb, dict(shape="arch", a=1.0, b=2.0, z0=0.3, z1=1.9)))
    body.append(dim_h(vb, 1.0, 2.0, 0.1, 20, size=9))
    body.append(dim_v(vb, 0.3, 1.9, 2.5, 18, size=9))
    body.append(vb.text(1.5, 2.65, "TIPO B · arco + persiane piccole aperte", size=11, anchor="middle", weight="bold", fill=ACC))
    body.append(vb.text(1.5, 2.35, "piano 3 · ante 0.5 × 1.1", size=9, anchor="middle", fill=SOFT, family=MONO))
    vc = View(vx + 330, 700, s)
    body.append(draw_opening_elev(vc, dict(shape="rect", a=0.5, b=1.4, z0=0.3, z1=1.9)))
    body.append(dim_h(vc, 0.5, 1.4, 0.1, 20, size=9))
    body.append(vc.text(0.95, 2.65, "TIPO C · persiana lunga", size=11, anchor="middle", weight="bold", fill=ACC))
    body.append(vc.text(0.95, 2.35, "piano 3, campata sx", size=9, anchor="middle", fill=SOFT, family=MONO))
    # schema scala imperiale
    body.append(schema_imperiale(60, 740))
    body.append(note_box(640, 740))
    return sheet(num, "ASSONOMETRIE, DETTAGLI E NOTE", "Riferimenti per la modellazione 3D", "\n".join(body))


def schema_imperiale(x, y):
    s = 48
    v = View(x + 40, y + 360, s)
    o = [caption(x, y + 10, "SCHEMA SCALA IMPERIALE (P1 → P2)", "pianta della sola campata centrale")]
    ox = 4.15
    tr = lambda a: a - ox
    o.append(v.rect(0, 3.7, 0, 9.0 - 3.8, fill="#1b4479", stroke=SOFT, stroke_width=0.6))
    for fl in G.FLIGHTS:
        if not fl["id"].startswith("S2"):
            continue
        for st in G.flight_steps(fl):
            o.append(v.rect(tr(st["x0"]), tr(st["x1"]), st["y0"] - 3.8, st["y1"] - 3.8, fill="#1f4c86", stroke=INK, stroke_width=0.9))
        xm = tr((fl["x0"] + fl["x1"]) / 2)
        ye = G.flight_end(fl)
        o.append(v.line(xm, fl["y0"] - 3.8 + fl["dir"] * 0.1, xm, ye - 3.8 - fl["dir"] * 0.1, stroke=ACC,
                        stroke_width=1.4, marker_end="url(#arrowA)"))
    x0, x1, y0, y1, zl = G.LANDING_IMP
    o.append(v.rect(tr(x0), tr(x1), y0 - 3.8, y1 - 3.8, fill="#2a5a98", stroke=INK, stroke_width=1))
    o.append(v.text(1.85, y0 - 3.8 + 0.6, "PIANEROTTOLO +6.3", size=10, anchor="middle", weight="bold"))
    o.append(v.text(1.85, 0.8, "partenza da P1 (+4.5)", size=10, anchor="middle", fill=ACC))
    o.append(v.text(0.5, 0.35, "arrivo P2", size=9, anchor="middle", fill=ACC))
    o.append(v.text(3.2, 0.35, "arrivo P2", size=9, anchor="middle", fill=ACC))
    o.append(dim_chain_h(v, [0, 1.0, 1.1, 2.6, 2.7, 3.7], 0, 34, size=8))
    o.append(dim_v(v, 1.5, 4.2, 3.7, 26, size=9))
    o.append(dim_v(v, 4.2, 5.7, 3.7, 26, size=9))
    tx = x + 300
    for i, t in enumerate(["1 rampa centrale larga 1.5 u", "10 alzate da 0.18 u, pedata 0.30 u",
                           "pianerottolo a metà altezza", "si divide in 2 bracci da 1.0 u",
                           "i bracci tornano verso il fronte", "10 alzate ciascuno fino a P2",
                           "corrimano lungo ogni braccio"]):
        o.append(text(tx, y + 70 + i * 22, "• " + t, size=11))
    return "\n".join(o)


def note_box(x, y):
    o = [caption(x, y + 10, "NOTE DI INTERPRETAZIONE DELLO SCHIZZO")]
    notes = [
        "1. Edificio in linea: i muri sx/dx sono in comune con edifici uguali. Sono ciechi.",
        "2. Facciata unica su strada; il prospetto posteriore ha solo l'arco dell'androne.",
        "3. PT: 3 portoni ad arco mistilineo; apribile solo il centrale (androne).",
        "4. Rampa PT→P1 dritta lungo il muro in comune dx, sale verso il retro.",
        "5. P1→P2: scala imperiale nella campata centrale (rampa unica che si divide).",
        "6. P2→P3: rampa dritta sovrapposta alla prima (non disegnata nello schizzo, ipotesi).",
        "7. P3: piano più basso (2.8 u). Arrivo alla copertura con scala alla marinara e botola.",
        "8. Porte interne ad arco a tutto sesto, luce 1.0 u (come gli archi dello schizzo).",
        "9. P3 campata sx: persiana lunga come indicato dalla freccia dello schizzo.",
        "10. Misure proporzionali in u: scegliere 1 u ≈ 1 m per un edificio realistico.",
    ]
    for i, t in enumerate(notes):
        o.append(text(x, y + 52 + i * 22, t, size=11))
    return "\n".join(o)


def main():
    os.makedirs(OUT, exist_ok=True)
    iso = [(os.path.join(OUT, "_iso_esterno.png"), "Esterno: facciata su strada (edifici adiacenti omessi)"),
           (os.path.join(OUT, "_iso_spaccato.png"), "Spaccato: taglio a metà profondità (y = 4.6 u), facciata rimossa")]
    sheets = {
        "tav01_prospetto_sezione-C.svg": tav_prospetto_sezC(1),
        "tav02_piante_PT_P1.svg": tav_piante(2, ["PT", "P1"]),
        "tav03_piante_P2_P3.svg": tav_piante(3, ["P2", "P3"]),
        "tav04_copertura_sezioni-A-B.svg": tav_copertura_sezioni(4),
        "tav05_assonometrie_dettagli.svg": tav_dettagli(5, iso),
    }
    for name, svg in sheets.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("scritto", name)


if __name__ == "__main__":
    main()
