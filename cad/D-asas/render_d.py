#!/usr/bin/env python3
"""Imagens do README da caixa D (precisa do D_asas.sc, ver NOTAS.md):
    python cad/D-asas/render_d.py [nome ...]      # sem nomes: todas
"""
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
import gerar_d as d  # noqa: E402  (reescreve os JSON com o mesmo conteudo)

HERE = Path(__file__).resolve().parent
IMG = HERE.parent.parent / "images"
from geo_d import CLI  # noqa: E402  (SOLIDCRAFT_CLI ou o primeiro caminho conhecido que existir)
OPEN = d.P["th_rest"]
# corte na folga entre o berco e as placas de tras: ficam so as placas, a cremalheira de tras e o trilho no rasgo
CUT = f"y={d.y_co + d.P['rail_clr'] / 2:.3f},flip"
# nome: (angulo das portas, camera, corte, esconder)
LOOSE = ["Divider", "PlatePin"] + d.FLAT + d.UP_          # pecas soltas ao lado da caixa (divisoria, pino, testes)
BOX = ["Base", "DoorL", "DoorR", "Tray", "Deck", "RackF", "RackB", "PlateLF", "PlateLB", "PlateRF", "PlateRB",
       "HingeLA", "HingeLB", "HingeRA", "HingeRB"]
SHOTS = {
    "D_fechada": (0, {"target": [0, 0, 48], "yaw": -0.6, "pitch": 0.42, "distance": 250}, None, LOOSE),
    "D_aberta": (OPEN, {"target": [0, 4, 70], "yaw": -0.5, "pitch": 0.5, "distance": 330}, None, LOOSE),
    "D_mecanismo_fechada": (0, {"target": [0, 0, 55], "yaw": 0.0, "pitch": 0.0, "distance": 260}, CUT, LOOSE + ["Deck"]),
    "D_mecanismo_aberta": (OPEN, {"target": [0, 0, 62], "yaw": 0.0, "pitch": 0.0, "distance": 300}, CUT, LOOSE + ["Deck"]),
    "D_dobradica": (0, {"target": [-40, 0, 54], "yaw": 1.2, "pitch": 0.22, "distance": 150}, None, LOOSE),
    "D_batente": (OPEN, {"target": [-46, 0, 60], "yaw": 1.35, "pitch": 0.3, "distance": 175}, None, LOOSE + ["Deck"]),
    "D_testes": (0, {"target": [d.TX + 57, d.TY - 8, 4], "yaw": -0.25, "pitch": 0.95, "distance": 230}, None,
                 BOX + ["Divider", "PlatePin"]),
}


def shot(name, w=1200, h=900):
    t, cam, section, hide = SHOTS[name]
    cmds = d.pose(t) + [{"command": "browser.visibility", "params": {"visible": False, "items": hide}}]
    with tempfile.TemporaryDirectory() as tmp:
        sp = Path(tmp) / "shot.json"
        sp.write_text(json.dumps({"commands": cmds}), encoding="utf-8")
        args = [CLI, "snapshot", str(sp), "--in", str(HERE / "D_asas.sc"), "--out", str(IMG / f"{name}.png"),
                "--width", str(w), "--height", str(h), "--camera", json.dumps(cam), "--no-grid", "--no-axes",
                "--quality", "fine"]
        if section:
            args += ["--section", section]
        r = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8")
    return f"{name}: " + ("ok" if not r.returncode else "ERRO " + (r.stderr or r.stdout)[-600:])


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(shot, sys.argv[1:] or list(SHOTS)):
            print(line)
