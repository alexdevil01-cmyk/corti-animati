"""Modello geometrico unico dell'edificio a tre portoni.

Tutte le misure sono in unità di griglia "u" (proporzioni). Per un edificio
storico realistico si può porre 1 u ≈ 1 m.

Sistema di riferimento:
  x  lungo la facciata, da sinistra (0) a destra (12), guardando dalla strada
  y  in profondità, dal filo strada (0) al retro (10)
  z  in altezza, da quota pavimento piano terra (0)
"""

# ---------------------------------------------------------------- parametri
W, D = 12.0, 10.0            # fronte, profondità (ingombro esterno)
T_EXT = 0.5                  # muri perimetrali e muri in comune
T_INT = 0.3                  # muri portanti interni (tra le campate)
SLAB = 0.3                   # spessore solai
PARAPET_TOP = 15.5           # sommità parapetto copertura

# quote di pavimento finito
LEVELS = {
    "PT": 0.0,
    "P1": 4.5,
    "P2": 8.1,
    "P3": 11.7,
    "COP": 14.5,             # estradosso solaio di copertura (terrazza)
}
LEVEL_ORDER = ["PT", "P1", "P2", "P3", "COP"]

# campate (luce netta tra i muri)
BAYS = {
    "SX": (T_EXT, 3.85),
    "C": (4.15, 7.85),
    "DX": (8.15, W - T_EXT),
}
BAY_AXIS = {k: (a + b) / 2 for k, (a, b) in BAYS.items()}  # 2.175 / 6.0 / 9.825
WALL_L = (3.85, 4.15)
WALL_R = (7.85, 8.15)
Y_IN0, Y_IN1 = T_EXT, D - T_EXT  # 0.5 .. 9.5

# ------------------------------------------------------------- aperture
# shape: 'portone' | 'rect' | 'arch'  (arch = rettangolo + semicerchio)
FRONT_OPENINGS = []
for k in ("SX", "C", "DX"):
    cx = BAY_AXIS[k]
    FRONT_OPENINGS.append(dict(id=f"PORT-{k}", lvl="PT", shape="portone",
                               a=cx - 1.0, b=cx + 1.0, z0=0.0, z1=3.6,
                               state="aperto" if k == "C" else "chiuso"))
    for lvl, z0 in (("P1", 5.4), ("P2", 9.0)):
        FRONT_OPENINGS.append(dict(id=f"F{lvl[1]}-{k}", lvl=lvl, shape="rect",
                                   a=cx - 0.55, b=cx + 0.55, z0=z0, z1=z0 + 2.0,
                                   tipo="A"))
    if k == "SX":
        FRONT_OPENINGS.append(dict(id=f"F3-{k}", lvl="P3", shape="rect",
                                   a=cx - 0.45, b=cx + 0.45, z0=12.3, z1=13.9,
                                   tipo="C"))
    else:
        FRONT_OPENINGS.append(dict(id=f"F3-{k}", lvl="P3", shape="arch",
                                   a=cx - 0.5, b=cx + 0.5, z0=12.3, z1=13.9,
                                   tipo="B"))

BACK_OPENINGS = [dict(id="ARCO-RETRO", lvl="PT", shape="arch",
                      a=5.55, b=6.45, z0=0.0, z1=2.6)]

def _door(a, lvl, h=2.6):
    z = LEVELS[lvl]
    return dict(lvl=lvl, shape="arch", a=a, b=a + 1.0, z0=z, z1=z + h)

WALL_L_OPENINGS = [_door(6.0, "PT"), _door(2.0, "P1"), _door(2.0, "P2"),
                   _door(2.0, "P3", 2.3)]
WALL_R_OPENINGS = [_door(1.0, "PT"), _door(2.0, "P1"), _door(1.0, "P2"),
                   _door(8.0, "P3", 2.3)]

# ------------------------------------------------------------- vuoti solai
# (livello del solaio forato) -> rettangoli x0,x1,y0,y1
VOIDS = {
    "P1": [(10.2, 11.5, 1.2, 8.7)],         # sopra la rampa PT -> P1
    "P2": [(4.15, 7.85, 5.3, 9.5)],         # sopra la scala imperiale
    "P3": [(10.2, 11.5, 2.0, 7.7)],         # sopra la rampa P2 -> P3
    "COP": [(10.5, 11.3, 8.5, 9.3)],        # botola
}

# ------------------------------------------------------------- scale
TREAD = 0.3
FLIGHTS = [
    # rampa unica PT -> P1 lungo il muro in comune destro, sale verso il retro
    dict(id="S1", nome="Rampa PT-P1", lvl="PT", x0=10.2, x1=11.5,
         y0=1.2, dir=+1, n=26, z0=0.0, z1=4.5),
    # scala imperiale P1 -> P2: rampa centrale
    dict(id="S2c", nome="Imperiale - rampa centrale", lvl="P1", x0=5.25, x1=6.75,
         y0=5.3, dir=+1, n=10, z0=4.5, z1=6.3),
    # ... e i due bracci di ritorno verso il fronte
    dict(id="S2s", nome="Imperiale - braccio sx", lvl="P1", x0=4.15, x1=5.15,
         y0=8.0, dir=-1, n=10, z0=6.3, z1=8.1),
    dict(id="S2d", nome="Imperiale - braccio dx", lvl="P1", x0=6.85, x1=7.85,
         y0=8.0, dir=-1, n=10, z0=6.3, z1=8.1),
    # rampa unica P2 -> P3 lungo il muro in comune destro
    dict(id="S3", nome="Rampa P2-P3", lvl="P2", x0=10.2, x1=11.5,
         y0=2.0, dir=+1, n=20, z0=8.1, z1=11.7),
]
LANDING_IMP = (4.15, 7.85, 8.0, 9.5, 6.3)  # pianerottolo intermedio (x0,x1,y0,y1,z)

# scala alla marinara verso la botola
LADDER = dict(x0=10.6, x1=11.2, y=9.42, z0=LEVELS["P3"], z1=LEVELS["COP"] + 0.9)

ROOMS = {
    "PT": [("SX", "BOTTEGA / MAGAZZINO", 2.17, 4.2),
           ("C", "ANDRONE", 6.0, 3.0),
           ("DX", "VANO SCALA", 9.1, 5.0)],
    "P1": [("SX", "AMBIENTE 1.1", 2.17, 6.0),
           ("C", "ATRIO SCALA IMPERIALE", 6.0, 2.6),
           ("DX", "BALLATOIO", 9.15, 5.5)],
    "P2": [("SX", "AMBIENTE 2.1", 2.17, 6.0),
           ("C", "PIANEROTTOLO D'ARRIVO", 6.0, 2.9),
           ("DX", "AMBIENTE 2.3", 9.15, 5.0)],
    "P3": [("SX", "AMBIENTE 3.1", 2.17, 5.0),
           ("C", "AMBIENTE 3.2", 6.0, 5.0),
           ("DX", "DISIMPEGNO", 9.15, 4.5)],
}


# ================================================================ BOX MODEL
def box(x0, x1, y0, y1, z0, z1, tag, **kw):
    d = dict(x0=min(x0, x1), x1=max(x0, x1), y0=min(y0, y1), y1=max(y0, y1),
             z0=min(z0, z1), z1=max(z0, z1), tag=tag)
    d.update(kw)
    return d


def _subtract_1d(lo, hi, holes):
    segs = [(lo, hi)]
    for a, b in holes:
        out = []
        for s, e in segs:
            if b <= s or a >= e:
                out.append((s, e))
                continue
            if a > s:
                out.append((s, a))
            if b < e:
                out.append((b, e))
        segs = out
    return [s for s in segs if s[1] - s[0] > 1e-6]


def rect_minus(u0, u1, v0, v1, holes):
    """Rettangolo (u,v) meno fori rettangolari -> lista di rettangoli."""
    cuts = {u0, u1}
    for a, b, c, d in holes:
        cuts.update(x for x in (a, b) if u0 < x < u1)
    cuts = sorted(cuts)
    raw = []
    for s, e in zip(cuts, cuts[1:]):
        m = (s + e) / 2
        hv = [(c, d) for a, b, c, d in holes if a <= m <= b]
        raw.append((s, e, tuple(_subtract_1d(v0, v1, hv))))
    merged = []
    for s, e, segs in raw:
        if merged and merged[-1][2] == segs and abs(merged[-1][1] - s) < 1e-9:
            merged[-1] = (merged[-1][0], e, segs)
        else:
            merged.append((s, e, segs))
    return [(s, e, a, b) for s, e, segs in merged for a, b in segs]


def wall_x(y0, y1, x0, x1, z0, z1, openings, tag="muro", name=""):
    """Muro parallelo alla facciata (asse u = x)."""
    holes = [(o["a"], o["b"], o["z0"], o["z1"]) for o in openings]
    return [box(a, b, y0, y1, c, d, tag, name=name)
            for a, b, c, d in rect_minus(x0, x1, z0, z1, holes)]


def wall_y(x0, x1, y0, y1, z0, z1, openings, tag="muro", name=""):
    """Muro ortogonale alla facciata (asse u = y)."""
    holes = [(o["a"], o["b"], o["z0"], o["z1"]) for o in openings]
    return [box(x0, x1, a, b, c, d, tag, name=name)
            for a, b, c, d in rect_minus(y0, y1, z0, z1, holes)]


def flight_steps(f):
    r = (f["z1"] - f["z0"]) / f["n"]
    steps = []
    for i in range(1, f["n"]):            # n-1 pedate, l'ultima alzata sbarca
        ya = f["y0"] + f["dir"] * (i - 1) * TREAD
        yb = f["y0"] + f["dir"] * i * TREAD
        top = f["z0"] + i * r
        steps.append(box(f["x0"], f["x1"], ya, yb, top - r - 0.15, top,
                         "gradino", flight=f["id"], lvl=f["lvl"], i=i))
    return steps


def flight_end(f):
    return f["y0"] + f["dir"] * (f["n"] - 1) * TREAD


def build():
    B = []
    # fondazione / solaio controterra
    B.append(box(0, W, 0, D, -0.3, 0, "solaio", lvl="PT"))
    # muri perimetrali
    B += wall_x(0, T_EXT, 0, W, 0, PARAPET_TOP, FRONT_OPENINGS, "muro", "facciata")
    B += wall_x(D - T_EXT, D, 0, W, 0, PARAPET_TOP, BACK_OPENINGS, "muro", "retro")
    B += wall_y(0, T_EXT, Y_IN0, Y_IN1, 0, PARAPET_TOP, [], "muro", "comune-sx")
    B += wall_y(W - T_EXT, W, Y_IN0, Y_IN1, 0, PARAPET_TOP, [], "muro", "comune-dx")
    # muri portanti interni
    zr = LEVELS["COP"] - SLAB
    B += wall_y(*WALL_L, Y_IN0, Y_IN1, 0, zr, WALL_L_OPENINGS, "muro", "interno-sx")
    B += wall_y(*WALL_R, Y_IN0, Y_IN1, 0, zr, WALL_R_OPENINGS, "muro", "interno-dx")
    # solai (per campata, con i vuoti)
    for lvl in ("P1", "P2", "P3", "COP"):
        z = LEVELS[lvl]
        for k, (bx0, bx1) in BAYS.items():
            holes = [v for v in VOIDS.get(lvl, []) if v[0] < bx1 and v[1] > bx0]
            for a, b, c, d in rect_minus(bx0, bx1, Y_IN0, Y_IN1, holes):
                B.append(box(a, b, c, d, z - SLAB, z, "solaio", lvl=lvl))
    # scale
    for f in FLIGHTS:
        B += flight_steps(f)
    x0, x1, y0, y1, z = LANDING_IMP
    B.append(box(x0, x1, y0, y1, z - 0.3, z, "pianerottolo", lvl="P1"))
    # parapetti / ringhiere
    B.append(box(10.15, 10.2, 1.2, 8.7, LEVELS["P1"], LEVELS["P1"] + 1.0, "ringhiera", lvl="P1"))
    B.append(box(5.15, 6.85, 5.3, 5.35, LEVELS["P2"], LEVELS["P2"] + 1.0, "ringhiera", lvl="P2"))
    B.append(box(10.15, 10.2, 2.0, 7.7, LEVELS["P3"], LEVELS["P3"] + 1.0, "ringhiera", lvl="P3"))
    # scala alla marinara
    L = LADDER
    for xx in (L["x0"], L["x1"] - 0.05):
        B.append(box(xx, xx + 0.05, L["y"], L["y"] + 0.05, L["z0"], L["z1"], "scala-pioli", lvl="P3"))
    z = L["z0"] + 0.3
    while z < L["z1"] - 0.1:
        B.append(box(L["x0"], L["x1"], L["y"], L["y"] + 0.04, z, z + 0.04, "scala-pioli", lvl="P3"))
        z += 0.3
    # elementi di facciata: marcapiani e cornicione
    for lvl in ("P1", "P2", "P3"):
        z = LEVELS[lvl]
        B.append(box(0, W, -0.12, 0, z - 0.3, z, "marcapiano"))
    B.append(box(0, W, -0.3, 0, LEVELS["COP"] - 0.3, LEVELS["COP"] + 0.15, "cornicione"))
    # portoni
    for o in FRONT_OPENINGS:
        if o["shape"] != "portone":
            continue
        if o["state"] == "chiuso":
            B.append(box(o["a"], o["b"], 0.2, 0.3, 0, 2.85, "portone-chiuso"))
        else:   # due ante aperte verso l'interno
            B.append(box(o["a"], o["a"] + 0.06, 0.5, 1.5, 0, 2.85, "portone-aperto"))
            B.append(box(o["b"] - 0.06, o["b"], 0.5, 1.5, 0, 2.85, "portone-aperto"))
    # persiane
    for o in FRONT_OPENINGS:
        if o["shape"] == "rect":   # persiane lunghe chiuse, a filo esterno
            B.append(box(o["a"], o["b"], -0.05, 0.0, o["z0"], o["z1"], "persiana"))
        elif o["shape"] == "arch":  # persiane piccole aperte, ribaltate sul muro
            zt = o["z1"] - (o["b"] - o["a"]) / 2
            B.append(box(o["a"] - 0.5, o["a"], -0.05, 0.0, o["z0"], zt, "persiana"))
            B.append(box(o["b"], o["b"] + 0.5, -0.05, 0.0, o["z0"], zt, "persiana"))
    return B


if __name__ == "__main__":
    bs = build()
    print(len(bs), "box")
