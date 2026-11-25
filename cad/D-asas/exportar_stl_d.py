#!/usr/bin/env python3
"""Exporta os STLs da caixa D na posicao de impressao (precisa do D_asas.sc, ver NOTAS.md):
    python cad/D-asas/exportar_stl_d.py
Gira cada peca no solidcraft-cli, exporta, e depois poe cada STL na mesa (z minimo 0, centrado em x e y).
"""
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "stl" / "D-asas"
CLI = os.environ.get("SOLIDCRAFT_CLI", "C:/Users/allan/Desktop/programas/cad/solidcraft-portable/app/"
                     "solidcraft-0.40.1-windows-x64-portable/solidcraft-cli.exe")

# corpo, arquivo, giro em X (graus) para a posicao de impressao
PARTS = [
    ("Base", "D_base", 0),                          # em pe: dobradica com o furo em gota para cima
    ("Tray", "D_berco", 0),                         # em pe
    ("Divider", "D_divisoria", 0),                  # ja sai deitada
    ("DoorL", "D_porta_esquerda", 180),             # de cabeca para baixo: teto na mesa, gota do pino para cima
    ("DoorR", "D_porta_direita", 180),
    ("PlateLF", "D_placa_esquerda_x2", 90),         # deitada (frente e tras sao a mesma peca)
    ("PlateRF", "D_placa_direita_x2", 90),
    ("RackF", "D_cremalheira_frente", -90),         # rasgo da cauda de andorinha (face +Y) para baixo
    ("RackB", "D_cremalheira_tras", 90),            # rasgo (face -Y) para baixo, nervura da trava para cima
]


def stl_to_bed(path):
    """Translada um STL binario para z minimo 0 e centro em x, y; devolve (dx, dy, dz, volume)."""
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    tris = [struct.unpack_from("<12fH", data, 84 + 50 * i) for i in range(n)]
    xs = [t[k] for t in tris for k in (3, 6, 9)]
    ys = [t[k] for t in tris for k in (4, 7, 10)]
    zs = [t[k] for t in tris for k in (5, 8, 11)]
    ox, oy, oz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    out = bytearray(data[:84])
    vol = 0.0
    for t in tris:
        v = [(t[3 + 3 * j] - ox, t[4 + 3 * j] - oy, t[5 + 3 * j] - oz) for j in range(3)]
        (a, b, c), (d, e, f), (g, h, i) = v
        vol += (a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)) / 6
        out += struct.pack("<12fH", *t[:3], *v[0], *v[1], *v[2], t[12])
    path.write_bytes(bytes(out))
    return max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), vol


cmds = []
for body, name, rx in PARTS:
    if rx:
        cmds.append({"command": "solid.move", "params": {"bodies": [body], "axis": [1, 0, 0], "angle": f"{rx} deg"}})
    cmds.append({"command": "file.export_stl", "params": {"path": str(OUT / f"{name}.stl"), "bodies": [body], "quality": "fine"}})
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    script = Path(tmp) / "export.json"
    script.write_text(json.dumps({"commands": cmds}), encoding="utf-8")
    r = subprocess.run([CLI, "run", str(script), "--in", str(HERE / "D_asas.sc"), "--quiet"],
                       capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
if r.returncode:
    sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
for body, name, _ in PARTS:
    x, y, z, v = stl_to_bed(OUT / f"{name}.stl")
    print(f"{name:26s} {x:6.1f} x {y:6.1f} x {z:6.1f} mm   {v / 1000:7.2f} cm3")
