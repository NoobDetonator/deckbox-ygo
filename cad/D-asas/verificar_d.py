#!/usr/bin/env python3
"""Roda as checagens de D_verificacao.json no solidcraft-cli (sem o MCP) e diz se cada uma deu o esperado.
    python cad/D-asas/verificar_d.py            # precisa do D_asas.sc (ver NOTAS.md), ~11 min
    python cad/D-asas/verificar_d.py --reuse    # so reanalisa a saida da ultima rodada
O rotulo diz o esperado: "(zero...)" = nenhuma interferencia; "toca" = alguma; o resto so mostra o resultado.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
from geo_d import CLI  # noqa: E402  (SOLIDCRAFT_CLI ou o primeiro caminho conhecido que existir)
RAW = Path(tempfile.gettempdir()) / "D_verificacao_saida.txt"
INSPECT = ("inspect.interference", "inspect.measure")

checks = json.loads((HERE / "D_verificacao.json").read_text(encoding="utf-8"))
cmds, spans = [], []
for c in checks:
    steps = [{"command": "edit.undo", "params": {}} if s["command"] == "undo" else s for s in c["args"]["commands"]]
    idx = [len(cmds) + k for k, s in enumerate(steps) if s["command"] in INSPECT]
    spans.append((c["label"], idx))
    cmds += steps
if "--reuse" not in sys.argv:
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "verif.json"
        script.write_text(json.dumps({"commands": cmds}), encoding="utf-8")
        out = subprocess.run([CLI, "run", str(script), "--in", str(HERE / "D_asas.sc"), "--results", "--quiet"],
                             capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    if out.returncode:
        sys.exit(out.stdout[-2000:] + out.stderr[-2000:])
    RAW.write_text(out.stdout, encoding="utf-8")
# a saida e uma sequencia de objetos JSON, um por comando, na ordem do script
raw, dec, i, objs = RAW.read_text(encoding="utf-8"), json.JSONDecoder(), 0, []
while (j := raw.find("{", i)) >= 0:
    o, i = dec.raw_decode(raw, j)
    objs.append(o)
if len(objs) != len(cmds):
    sys.exit(f"saida com {len(objs)} resultados para {len(cmds)} comandos: nao da para casar")
bad = 0
for label, idx in spans:
    got = [objs[k] for k in idx]
    pairs = [f"{x['a']}x{x['b']}={x.get('volume_mm3', 0):.3f}" for r in got for x in r.get("interferences", [])]
    touch = any(x.get("volume_mm3", 0) > 0 for r in got for x in r.get("interferences", []))
    ok = (not touch) if "(zero" in label else touch if "toca" in label else None
    bad += ok is False
    tag = {True: "ok   ", False: "FALHA", None: "info "}[ok]
    extra = " ".join(pairs) if ok is not None else json.dumps([r.get("bodies", r) for r in got])[:400]
    print(f"{tag} {label}  {extra}")
print("RESULTADO:", "tudo ok" if not bad else f"{bad} falha(s)")
sys.exit(1 if bad else 0)
