#!/usr/bin/env python3
"""Exporta os STLs da caixa D na posicao de impressao (precisa do D_asas.sc, ver NOTAS.md):
    python cad/D-asas/exportar_stl_d.py
Gira cada peca no solidcraft-cli, exporta, e depois poe cada STL na mesa (z minimo 0, centrado em x e y).
"""
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
import gerar_d as d  # noqa: E402  (reescreve os JSON com o mesmo conteudo)
from geo_d import CLI  # noqa: E402  (SOLIDCRAFT_CLI ou o primeiro caminho conhecido que existir)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "stl" / "D-asas"

# arquivo, corpos, giro (eixo, graus) para a posicao de impressao
PARTS = [
    ("D_base", ["Base"], None),                                   # em pe
    ("D_berco", ["Tray"], None),                                  # em pe
    ("D_divisoria", ["Divider"], None),                           # ja sai deitada
    ("D_porta_esquerda", ["DoorL"], ([1, 0, 0], 180)),            # de cabeca para baixo: teto na mesa
    ("D_porta_direita", ["DoorR"], ([1, 0, 0], 180)),
    ("D_placa_esquerda_x2", ["PlateLF"], ([1, 0, 0], 90)),        # deitada (frente e tras sao a mesma peca)
    ("D_placa_direita_x2", ["PlateRF"], ([1, 0, 0], 90)),
    ("D_cremalheira_frente", ["RackF"], ([1, 0, 0], -90)),        # rasgo da cauda de andorinha (face +Y) para baixo
    ("D_cremalheira_tras", ["RackB"], ([1, 0, 0], 90)),           # rasgo (face -Y) para baixo, nervura da trava para cima
    ("D_dobradica_x2", ["HingeLA", "HingeLB"], ([0, 1, 0], 90)),  # print-in-place: as duas abas juntas, face colada na mesa
    ("D_pino_placa_x8", ["PlatePin"], None),                      # em pe sobre a cabeca
    ("D_teste_deitado", d.FLAT, None),                            # pecas de teste (ver o README): ja na posicao
    ("D_teste_em_pe", d.UP_, None),
]
# o setor e a cremalheira do equipamento de teste estao montados nele: descem para a mesa, ao lado
SPREAD = [(["TestSector"], [55, 0, -2.3]), (["TestRack"], [60, 0, -2.3])]


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
        (a, b, c), (e, f, g), (h, i, j) = v
        vol += (a * (f * j - g * i) - b * (e * j - g * h) + c * (e * i - f * h)) / 6
        out += struct.pack("<12fH", *t[:3], *v[0], *v[1], *v[2], t[12])
    path.write_bytes(bytes(out))
    return max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), vol


cmds = [{"command": "solid.move", "params": {"bodies": b, "translate": tr}} for b, tr in SPREAD]
for name, bodies, rot in PARTS:
    if rot:
        cmds.append({"command": "solid.move", "params": {"bodies": bodies, "axis": rot[0], "angle": f"{rot[1]} deg"}})
    cmds.append({"command": "file.export_stl", "params": {"path": str(OUT / f"{name}.stl"), "bodies": bodies, "quality": "fine"}})
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    script = Path(tmp) / "export.json"
    script.write_text(json.dumps({"commands": cmds}), encoding="utf-8")
    r = subprocess.run([CLI, "run", str(script), "--in", str(HERE / "D_asas.sc"), "--quiet"],
                       capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
if r.returncode:
    sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
for name, _, _ in PARTS:
    x, y, z, v = stl_to_bed(OUT / f"{name}.stl")
    print(f"{name:26s} {x:6.1f} x {y:6.1f} x {z:6.1f} mm   {v / 1000:7.2f} cm3")
