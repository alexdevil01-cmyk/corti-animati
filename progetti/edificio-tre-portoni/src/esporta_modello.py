"""Esporta il modello a blocchi in OBJ/MTL (Y-up, 1 u = 1 unità) e in JSON."""
import json
import os

import geometria as G

OUT = os.path.join(os.path.dirname(__file__), "..", "modello")
COLORS = {
    "muro": (0.86, 0.80, 0.70), "solaio": (0.75, 0.73, 0.70), "gradino": (0.70, 0.68, 0.65),
    "pianerottolo": (0.70, 0.68, 0.65), "ringhiera": (0.15, 0.15, 0.15), "scala-pioli": (0.30, 0.22, 0.15),
    "marcapiano": (0.92, 0.90, 0.85), "cornicione": (0.92, 0.90, 0.85), "portone-chiuso": (0.35, 0.22, 0.12),
    "portone-aperto": (0.35, 0.22, 0.12), "persiana": (0.22, 0.38, 0.25),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    boxes = G.build()
    with open(os.path.join(OUT, "edificio.json"), "w") as fh:
        json.dump(boxes, fh)
    with open(os.path.join(OUT, "edificio.mtl"), "w") as fh:
        for k, (r, g, b) in COLORS.items():
            fh.write(f"newmtl {k}\nKd {r} {g} {b}\n\n")
    lines = ["# Edificio a tre portoni - modello a blocchi", "# Y-up, 1 unita = 1 u (≈ 1 m)",
             "mtllib edificio.mtl"]
    vi = 1
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for n, b in enumerate(boxes):
        lines.append(f"o {b['tag']}_{n}")
        lines.append(f"usemtl {b['tag']}")
        for x in (b["x0"], b["x1"]):
            for y in (b["y0"], b["y1"]):
                for z in (b["z0"], b["z1"]):
                    # (x, z, -y): Y in alto, facciata rivolta verso +Z
                    lines.append(f"v {x:.4f} {z:.4f} {-y:.4f}")
        for fc in faces:
            lines.append("f " + " ".join(str(vi + i) for i in fc))
        vi += 8
    with open(os.path.join(OUT, "edificio.obj"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(len(boxes), "box esportati")


if __name__ == "__main__":
    main()
