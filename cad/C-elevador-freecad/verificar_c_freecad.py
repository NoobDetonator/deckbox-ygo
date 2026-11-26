"""Checagens da versao C no FreeCAD (rodar sem GUI, depois de gerar_c_freecad.py):
    "C:/Program Files/FreeCAD 1.1/bin/FreeCADCmd.exe" -c "exec(open(r'<repo>/cad/C-elevador-freecad/verificar_c_freecad.py', encoding='utf-8').read())"
Interferencia entre todas as pecas em 12 angulos da tampa, batente, berco sem carga fechado e pinos nas ranhuras.
"""
import itertools
import sys
from pathlib import Path

import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = Path(r"E:/Projetos/03 - 3D/ygo box/deckbox-ygo/cad/C-elevador-freecad")
sys.path.insert(0, str(HERE.parent / "C-elevador-v2"))
sys.dont_write_bytecode = True
import gerar_c2 as g  # noqa: E402

doc = App.openDocument(str(HERE / "C_elevador.FCStd"))
S0 = {o.Name: o.Shape for o in doc.Objects}
LIDG = {"Lid", "CrankR", "CrankL", "CpinR", "CpinL"}
LEVG = {"LeverR", "LeverL", "EpinR", "EpinL"}
UPG = {"Cradle", "Deck", "Divider"}
# encaixes de proposito: pinos apertados nos furos e a cauda de andorinha manivela-tampa
PRESS = {frozenset(p) for p in (("AxleR", "Core"), ("AxleR", "ShellR"), ("AxleL", "Core"), ("AxleL", "ShellL"),
                                 ("PivotR", "Core"), ("PivotR", "ShellR"), ("PivotL", "Core"), ("PivotL", "ShellL"),
                                 ("CpinR", "CrankR"), ("CpinL", "CrankL"), ("EpinR", "LeverR"), ("EpinL", "LeverL"),
                                 ("CrankR", "Lid"), ("CrankL", "Lid"), ("Deck", "Divider"))}
TOL = 1e-3


def placed(t_lid, t_mech, lift_extra=0.0):
    tm = min(t_mech, g.TH3)
    lid = App.Placement(V(), App.Rotation(V(1, 0, 0), -t_lid), V(0, g.Hy, g.Hz))
    lev = App.Placement(V(), App.Rotation(V(1, 0, 0), -(g.phi(tm) - g.PHI0)), V(0, g.Hy + g.QY, g.Hz + g.QZ))
    up = App.Placement(V(0, 0, g.Lc(tm) + lift_extra), App.Rotation())
    out = {}
    for k, s in S0.items():
        s = s.copy()
        if k in LIDG:
            s.transformShape(lid.toMatrix())
        elif k in LEVG:
            s.transformShape(lev.toMatrix())
        elif k in UPG:
            s.transformShape(up.toMatrix())
        out[k] = s
    return out


def inter(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


fails = []


def check(label, ok, info=""):
    print(("ok   " if ok else "FALHA"), label, info)
    sys.stdout.flush()
    if not ok:
        fails.append(label)


moving = LIDG | LEVG | UPG
bad, loose = [], []
x2 = (g.L2[0], g.L2[1])
r_probe = g.P["pin_d"] / 2 + g.P["cam_clr"] + 0.15   # 0,15 alem da folga: tem de tocar a ranhura / o garfo
for t in range(0, 111):   # de grau em grau ate o fim do curso
    sh = placed(t, t)
    for a, b in itertools.combinations(sorted(sh), 2):
        if frozenset((a, b)) in PRESS or (t and a not in moving and b not in moving):
            continue   # pares fixos so mudam no angulo 0
        vol = inter(sh[a], sh[b])
        if vol > TOL:
            bad.append(f"{t}:{a}x{b}={vol:.3f}")
    # sondas: o pino C anda dentro da ranhura do balancim e o pino E dentro do garfo do berco (nem folgado, nem fora)
    cy, cz = g.rot_ccw(g.Cc, -t)
    ey, ez = g.rot_ccw((g.E0[0] - g.QY, g.E0[1] - g.QZ), -(g.phi(min(t, g.TH3)) - g.PHI0))
    pc = Part.makeCylinder(r_probe, x2[1] - x2[0], V(x2[0], g.Hy + cy, g.Hz + cz), V(1, 0, 0))
    pe = Part.makeCylinder(r_probe, 1.0, V(g.L1[0] + 1, g.Hy + g.QY + ey, g.Hz + g.QZ + ez), V(1, 0, 0))
    if inter(pc, sh["LeverR"]) <= TOL:
        loose.append(f"C{t}")
    # o pino E so encosta no garfo parado no fundo ou levantando; no meio da folga morta ele fica solto de proposito
    in_slack = 0 < g.L(min(t, g.TH3)) < g.YOKE_SLACK
    if not in_slack and inter(pe, sh["Cradle"]) <= TOL:
        loose.append(f"E{t}")
check("tampa de 0 a 110 graus, grau a grau: interferencia zero", not bad, " ".join(bad[:12]))
check("pinos C e E encostam na ranhura e no garfo em todos os angulos", not loose, "soltos em: " + " ".join(loose))

sh = placed(113, g.TH3)
check("batente a 113 graus: manivela toca o corpo", inter(sh["CrankR"], sh["Core"]) > TOL)
check("batente a 113 graus: pino C nao chega ao fim da ranhura", inter(sh["CpinR"], sh["LeverR"]) <= TOL)
sh = placed(0, 0, -0.05)
check("fechada: berco 0,05 abaixo toca o fundo (apoiado)", inter(sh["Cradle"], sh["Core"]) > TOL)
sh = placed(0, 0, -(g.YOKE_SLACK + g.P["cam_clr"] - 0.05))
check("fechada: berco descendo a folga do garfo nao toca o pino E (mecanismo sem carga)", inter(sh["Cradle"], sh["EpinR"]) <= TOL)
print("RESULTADO:", "tudo ok" if not fails else f"{len(fails)} falha(s)")
