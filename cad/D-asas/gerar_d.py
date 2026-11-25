#!/usr/bin/env python3
"""Caixa D ("asas"): escreve o script do SolidCraft (D_asas_build.json) e o roteiro de verificacao
(D_verificacao.json) a partir da geometria de geo_d.py.  Rode:  python cad/D-asas/gerar_d.py

ponytail: a geometria sai numerica do Python (dentes evolventes, perfis da dobradica); o .py e a fonte
parametrica. Mudou um numero? Edite P em geo_d.py e rode de novo.
"""
import json
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Polygon, box as sbox

import geo_d as g

HERE = Path(__file__).resolve().parent
P, p = g.P, g.p
ZS, XP, H = g.ZS, g.XP, p["H"]
Wh, Dh = p["Wh"], p["Dh"]
x_ki, x_co, y_co, y_bi, y_bo, y_wi = (p[k] for k in ("x_ki", "x_co", "y_co", "y_bi", "y_bo", "y_wi"))
Y_H = y_co                                    # a dobradica vai de -Y_H a +Y_H (fora das faixas das placas)
N_SEG, KG = 7, 0.3                            # nos da dobradica: base nos pares (0,2,4,6), porta nos impares
SEG = [-Y_H + 2 * Y_H * i / N_SEG for i in range(N_SEG + 1)]
SCREW = [(28.0, 64.0), (28.0, 91.0)]          # parafusos M2 das placas (|x|, z) nas paredes da frente/tras das portas
Y_MID = (y_bi + y_bo) / 2

cmds = []
C = lambda _cmd, **params: cmds.append({"command": _cmd, "params": params})
r4 = lambda v: round(v, 4)


def box(name, x0, x1, y0, y1, z0, z1, op, body=None, targets=None):
    prm = dict(length=r4(x1 - x0), width=r4(y1 - y0), height=r4(z1 - z0), corner=[r4(x0), r4(y0), r4(z0)], operation=op, name=name)
    if body:
        prm["body_name"] = body
    if targets:
        prm["targets"] = targets
    C("solid.box", **prm)


def cyl(name, r, base, axis, h, op, body=None, targets=None):
    prm = dict(radius=r4(r), height=r4(h), axis=axis, base=[r4(v) for v in base], operation=op, name=name)
    if body:
        prm["body_name"] = body
    if targets:
        prm["targets"] = targets
    C("solid.cylinder", **prm)


def rings(geom):
    """Contornos (externo + furos) de um poligono shapely, sem o ponto repetido do fim."""
    geom = geom.simplify(0.003)
    polys = geom.geoms if hasattr(geom, "geoms") else [geom]
    out = []
    for pg in polys:
        out.append(list(pg.exterior.coords)[:-1])
        out += [list(i.coords)[:-1] for i in pg.interiors]
    return out


def extrude(name, plane, offset, loops, dist, op, body=None, targets=None):
    C("sketch.create", plane=plane, offset=r4(offset), name=name + "Sk")
    for lp in loops:
        C("sketch.line", closed=True, points=[[r4(a), r4(b)] for a, b in lp])
    C("sketch.finish")
    prm = dict(sketch=name + "Sk", distance=r4(dist), operation=op, name=name)
    if body:
        prm["body_name"] = body
    if targets:
        prm["targets"] = targets
    C("solid.extrude", **prm)


def xz(name, geom, y0, y1, op, **kw):
    """Perfil no plano XZ (mundo x, z) extrudado de y0 a y1 (no plano XZ o y do esboco e -z)."""
    loops = [[(a, -b) for a, b in lp] for lp in rings(geom)]
    extrude(name, "XZ", y0, loops, y1 - y0, op, **kw)


def yz(name, pts, x0, x1, op, **kw):
    extrude(name, "YZ", x0, [pts], x1 - x0, op, **kw)


def xy(name, pts, z0, z1, op, **kw):
    extrude(name, "XY", z0, [pts], z1 - z0, op, **kw)


def rounded(x0, z0, x1, z1, r):
    return sbox(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, quad_segs=6)


def hinge(tag, s, body, bar, own_even):
    """Dobradica em fatias de y, cada uma com o seu perfil (sem cilindro analitico: o booleano de um cilindro
    contra o perfil poligonal da barra falhava). Nos proprios: barra + no de r_k; o resto (nos do outro lado e as
    folgas de 0,15): barra - disco de r_k + k_clr. Antes, o entalhe na parede no lugar dos nos do outro lado."""
    rel = g.disc((0, 0), P["r_k"] + P["k_clr"], 96)
    own_p = g.at_pivot(bar.union(g.disc((0, 0), P["r_k"], 96)), s)
    other_p = g.at_pivot(bar.difference(rel), s)
    for i in range(N_SEG):
        a, b = SEG[i], SEG[i + 1]
        if (i % 2 == 0) == own_even:
            lo, hi = (a if i == 0 else a + KG / 2), (b if i == N_SEG - 1 else b - KG / 2)
            xz(f"Knuckle{tag}{i}", own_p, lo, hi, "join", targets=[body])
        else:
            xz(f"WallRelief{tag}{i}", g.at_pivot(rel, s), a - 0.1, b + 0.1, "cut", targets=[body])
            xz(f"Hinge{tag}{i}", other_p, a - KG / 2, b + KG / 2, "join", targets=[body])


# ---------------- parametros (informativos; a geometria vem do Python) ----------------
for n, e, c in (("W", 2 * Wh, "largura (sem a dobradica)"), ("D", 2 * Dh, "profundidade"), ("H", H, "altura"),
                ("z_split", ZS, "divisao base/portas = eixo das portas"), ("module", P["m"], "engrenagem"),
                ("lift", g.lift(P["th_stop"]), "subida do berco a 78 graus")):
    C("parameters.add", name=n, expression=f"{e:.3f} mm", comment=c)
C("parameters.add", name="bt_title", expression="DECK BOX", comment="texto do fundo, 1a linha", unit="text")
C("parameters.add", name="bt_sub", expression="90 CARTAS · ABS", comment="texto do fundo, 2a linha", unit="text")

# ======================= BASE =======================
box("BaseBlock", -Wh, Wh, -Dh, Dh, 0, ZS, "new", body="Base")
C("solid.fillet", body="Base", edges=[[sx * Wh, sy * Dh, ZS / 2] for sx in (1, -1) for sy in (1, -1)], radius=4, name="BaseCorners")
C("solid.chamfer", body="Base", edges=[[0, -Dh, 0]], distance=0.8, name="BaseBedChamfer")
C("solid.chamfer", body="Base", edges=[[0, -Dh, ZS]], distance=0.5, name="BaseReveal")
box("BaseCavity", -x_ki, x_ki, -y_wi, y_wi, P["base_t"], ZS + 1, "cut", targets=["Base"])
# trava de abertura na parede de tras: canal de 0,5 para a nervura da cremalheira, lingueta horizontal com cortes a 45
# graus (imprime sem suporte) e um ressalto de 0,5; a cremalheira passa a nervura por cima dele perto de 78 graus
box("DetentChannel", -7, 7, y_wi - 0.01, y_wi + 0.5, g.Z_RIDGE - 1, ZS + 1, "cut", targets=["Base"])
yi, zb = y_wi + 0.5, g.Z_BUMP
wt = Dh - yi
for nm, z0 in (("TongueSlitTop", zb + 2.5), ("TongueSlitBot", zb - 2.5 - 0.6)):
    yz(nm, [(yi - 0.05, z0), (Dh + 0.05, z0 + wt + 0.1), (Dh + 0.05, z0 + wt + 0.7), (yi - 0.05, z0 + 0.6)], -6, 3.6, "cut", targets=["Base"])
box("TongueSlitEnd", 3, 3.6, yi - 0.1, Dh + 0.1, zb - 3.3, zb + 2.5 + 0.6 + wt + 0.2, "cut", targets=["Base"])
yz("DetentBump", [(yi + 0.01, zb - 0.5), (yi - 0.5, zb), (yi + 0.01, zb + 0.5)], -2.5, 2.0, "join", targets=["Base"])
# frente: painel rebaixado para o adesivo
xz("FrontPanel", rounded(-27, 9, 27, 47, 4), -Dh - 1, -Dh + 0.5, "cut", targets=["Base"])
# pes e texto do fundo (iguais aos da C)
cyl("FootRecess", 4.2, [-(Wh - 7), -(Dh - 7), -1], "Z", 1.6, "cut", targets=["Base"])
C("solid.pattern.rectangular", features=["FootRecess"], dir1=[1, 0, 0], count1=2, spacing1=r4(2 * Wh - 14),
  dir2=[0, 1, 0], count2=2, spacing2=r4(2 * Dh - 14), name="FootRecesses")
C("sketch.create", plane="XY", offset=-1, flip=True, name="BottomTextSk")
C("sketch.text", text_expression="bt_title", at=[0, 4], height=6, align="center", vertical_align="middle")
C("sketch.text", text_expression="bt_sub", at=[0, -4], height=3.5, align="center", vertical_align="middle")
C("sketch.finish")
C("solid.extrude", sketch="BottomTextSk", distance=1.4, direction="negative", name="BottomText", operation="cut", targets=["Base"])
# dobradica da base: barra de baixo continua (45 graus por baixo, topo = batente), nos nos pares, alivio nos impares
lug = g.base_lug()
for s, tag in ((-1, "L"), (1, "R")):
    hinge(f"Base{tag}", s, "Base", lug, True)
    # pino de filamento 1,75: furo de 1,9 (aperta depois de impresso), em gota para cima; fechado 1 mm na frente
    xz(f"PinHoleBase{tag}", affinity.translate(g.teardrop(P["pin_press"] / 2, True), s * XP, ZS), -Y_H + 1, Y_H + 1, "cut", targets=["Base"])

# ======================= PORTAS =======================
for s, tag in ((-1, "L"), (1, "R")):
    body = f"Door{tag}"
    xs = (-Wh, g.X_SEAM) if s < 0 else (-g.X_SEAM, Wh)
    box(f"Door{tag}Block", xs[0], xs[1], -Dh, Dh, ZS, H, "new", body=body)
    C("solid.fillet", body=body, edges=[[s * Wh, sy * Dh, (ZS + H) / 2] for sy in (1, -1)], radius=4, name=f"Door{tag}Corners")
    C("solid.chamfer", body=body, edges=[[s * Wh / 2, -Dh, H]], distance=1.0, name=f"Door{tag}TopChamfer")
    C("solid.chamfer", body=body, edges=[[s * Wh / 2, -Dh, ZS]], distance=0.5, name=f"Door{tag}Reveal")
    xin = (-x_ki, g.X_SEAM + 1) if s < 0 else (-g.X_SEAM - 1, x_ki)
    box(f"Door{tag}Inside", xin[0], xin[1], -y_bo, y_bo, ZS - 1, p["roof_in"], "cut", targets=[body])
    # friso no teto (moldura de 0,8 rebaixada 0,4)
    xo = (-Wh + 5, -4) if s < 0 else (4, Wh - 5)
    outer = rounded(xo[0], -Dh + 5, xo[1], Dh - 5, 3)
    ring = outer.difference(rounded(xo[0] + 0.8, -Dh + 5.8, xo[1] - 0.8, Dh - 5.8, 2.2))
    extrude(f"Door{tag}Frame", "XY", H - 0.4, rings(ring), 1, "cut", targets=[body])
    for k, (sx, sz) in enumerate(SCREW):
        C("solid.hole", position=[r4(s * sx), r4(-Dh), sz], direction=[0, 1, 0], diameter=2.3, type="countersink",
          cs_diameter=4.2, cs_angle=90, depth=P["dwall_t"] + 0.5, targets=[body], name=f"ScrewF{tag}{k}")
        C("solid.hole", position=[r4(s * sx), r4(Dh), sz], direction=[0, -1, 0], diameter=2.3, type="countersink",
          cs_diameter=4.2, cs_angle=90, depth=P["dwall_t"] + 0.5, targets=[body], name=f"ScrewB{tag}{k}")
    # dobradica da porta: mao-francesa de cima continua, nos impares, alivio nos pares, furo livre de 2,2 em gota para baixo
    hinge(f"Door{tag}", s, body, g.door_gusset(), False)
    xz(f"PinHoleDoor{tag}", affinity.translate(g.teardrop(P["pin_free"] / 2, False), s * XP, ZS), -Y_H - 1, Y_H + 1, "cut", targets=[body])
# entalhe para a unha na emenda, em cima na frente
cyl("ThumbNotch", 4.5, [0, -Dh - 1, H], "Y", 2.5, "cut", targets=["DoorL", "DoorR"])

# ======================= PLACAS-SETOR (4) =======================
for s, tag in ((-1, "L"), (1, "R")):
    geom = g.plate(s)
    for side, y0, y1 in (("F", -y_bo, -y_bi), ("B", y_bi, y_bo)):
        body = f"Plate{tag}{side}"
        xz(f"Plate{tag}{side}Body", geom, y0, y1, "new", body=body)
        for k, (sx, sz) in enumerate(SCREW):
            cyl(f"Plate{tag}{side}Pilot{k}", 0.8, [s * sx, y0 - 0.5, sz], "Y", y1 - y0 + 1, "cut", targets=[body])
        # ima 4 x 2 na face da emenda (eixo X): furo de 4,2 x 2,2
        x0 = g.X_SEAM - 2.2 if s < 0 else -g.X_SEAM - 0.5
        cyl(f"Plate{tag}{side}Magnet", 2.1, [x0, (y0 + y1) / 2, g.Z_MAG], "X", 2.7, "cut", targets=[body])

# ======================= CREMALHEIRAS (2) =======================
rk, z_top = g.rack()
gw = (g.RAIL["neck"] + 0.2, g.RAIL["tip"] + 0.2, g.RAIL["h"] + 0.2)      # rasgo da cauda de andorinha
for side, sg in (("F", -1), ("B", 1)):
    body = f"Rack{side}"
    y0, y1 = (-y_bo, -y_bi) if sg < 0 else (y_bi, y_bo)
    xz(f"Rack{side}Body", rk, y0, y1, "new", body=body)
    ym, yd = sg * (y_bi - 0.05), sg * (y_bi + gw[2])                       # boca (no lado do berco) e fundo do rasgo
    xy(f"Rack{side}Groove", [(-gw[0], ym), (gw[0], ym), (gw[1], yd), (-gw[1], yd)], g.Z_GE, z_top + 1, "cut", targets=[body])
rd = g.RIDGE
yz("RackBRidge", [(y_bo - 0.01, g.Z_RIDGE), (y_bo + rd["h"], g.Z_RIDGE + rd["lo"]), (y_bo - 0.01, g.Z_RIDGE + rd["lo"] + rd["up"])],
   -4.5, 4.5, "join", targets=["RackB"])

# ======================= BERCO =======================
box("TrayBlock", -x_co, x_co, -y_co, y_co, P["base_t"], ZS - 0.5, "new", body="Tray")
C("solid.fillet", body="Tray", edges=[[sx * x_co, sy * y_co, 30] for sx in (1, -1) for sy in (1, -1)], radius=1.6, name="TrayCorners")
C("solid.chamfer", body="Tray", edges=[[0, -y_co, P["base_t"]]], distance=0.6, name="TrayLeadIn")
box("TrayInside", -p["in_x"] / 2, p["in_x"] / 2, -p["in_y"] / 2, p["in_y"] / 2, P["base_t"] + P["crad_f"], ZS + 1, "cut", targets=["Tray"])
rl = g.RAIL
for side, sg in (("F", -1), ("B", 1)):
    pts = [(-rl["neck"], sg * (y_co - 0.3)), (rl["neck"], sg * (y_co - 0.3)), (rl["neck"], sg * y_bi),
           (rl["tip"], sg * (y_bi + rl["h"])), (-rl["tip"], sg * (y_bi + rl["h"])), (-rl["neck"], sg * y_bi)]
    xy(f"TrayRail{side}", pts if sg > 0 else pts[::-1], g.Z_RB, g.Z_RT, "join", targets=["Tray"])
    ye = sg * (y_bi + rl["h"] + 0.1)
    yz(f"TrayRailChamfer{side}", [(sg * (y_co - 0.01), g.Z_RB - 0.01), (ye, g.Z_RB - 0.01), (ye, g.Z_RB + abs(ye) - y_co)],
       -4, 4, "cut", targets=["Tray"])

# ======================= DIVISORIA, BLOCO DE CARTAS, PINOS =======================
div_w, div_h, tab_w = p["in_x"] - 2 * P["liner_t"] - 0.8, P["card_h"] - 7, 22.0
box("DividerPlate", Wh + 15, Wh + 15 + div_w, -Dh, -Dh + div_h, 0, P["div_t"], "new", body="Divider")
box("DividerTab", Wh + 15 + (div_w - tab_w) / 2, Wh + 15 + (div_w + tab_w) / 2, -Dh + div_h - 1, -Dh + P["card_h"] + 1, 0, P["div_t"], "join", targets=["Divider"])
deck_t = P["n_cards"] * P["card_t"] + P["div_t"]
yb = p["in_y"] / 2 - P["liner_t"]
box("DeckBlock", -P["card_w"] / 2, P["card_w"] / 2, yb - deck_t, yb, p["card_z0"], p["card_top"], "new", body="Deck")
for s, tag in ((-1, "L"), (1, "R")):
    cyl(f"Pin{tag}", 1.75 / 2, [s * XP, -Y_H + 1.2, ZS], "Y", 2 * Y_H - 1.4, "new", body=f"Pin{tag}")

COLORS = {"Base": "#1c2331", "DoorL": "#c9a227", "DoorR": "#c9a227", "Tray": "#7a2230", "Divider": "#a8322d",
          "Deck": "#e8e2d0", "RackF": "#c0c6cc", "RackB": "#c0c6cc", "PinL": "#5b6168", "PinR": "#5b6168"}
for b in ("PlateLF", "PlateLB", "PlateRF", "PlateRB"):
    COLORS[b] = "#9aa3ad"
for b, c in COLORS.items():
    C("appearance.assign", bodies=[b], color=c)

(HERE / "D_asas_build.json").write_text(json.dumps({"commands": cmds}, ensure_ascii=False, indent=1), encoding="utf-8")

# ======================= VERIFICACAO (chamadas MCP) =======================
DOOR = {-1: ["DoorL", "PlateLF", "PlateLB"], 1: ["DoorR", "PlateRF", "PlateRB"]}
RACKS, UP, FIXED = ["RackF", "RackB"], ["Tray", "Deck"], ["Base", "PinL", "PinR"]
ALL = FIXED + DOOR[-1] + DOOR[1] + RACKS + UP
TOUCH = [["DoorL", "PlateLF"], ["DoorL", "PlateLB"], ["DoorR", "PlateRF"], ["DoorR", "PlateRB"], ["Tray", "RackF"], ["Tray", "RackB"]]
UNDO = {"command": "undo", "params": {}}


def turn(bodies, deg, ox, oz):
    # gira em Y em volta de (ox, oz): translada-gira-volta (o solid.move gira na origem)
    return [{"command": "solid.move", "params": {"bodies": bodies, "translate": [-ox, 0, -oz]}},
            {"command": "solid.move", "params": {"bodies": bodies, "axis": [0, 1, 0], "angle": f"{deg:.4f} deg"}},
            {"command": "solid.move", "params": {"bodies": bodies, "translate": [ox, 0, oz]}}]


def pose(t):
    """Portas a t graus, cremalheiras no curso, berco e cartas na subida. Esquerda: -t em Y (sobe por fora)."""
    if not t:
        return []
    s = turn(DOOR[-1], -t, -XP, ZS) + turn(DOOR[1], t, XP, ZS)
    s.append({"command": "solid.move", "params": {"bodies": RACKS, "translate": [0, 0, r4(g.travel(t))]}})
    if g.lift(t):
        s.append({"command": "solid.move", "params": {"bodies": UP, "translate": [0, 0, r4(g.lift(t))]}})
    return s


checks = []


def batch(steps, label):
    checks.append({"tool": "batch", "args": {"verbose": False, "rollback": False, "commands": steps}, "label": label})


def interf(bodies, excl=None):
    prm = {"bodies": bodies}
    if excl:
        prm["exclude_pairs"] = excl
    return {"command": "inspect.interference", "params": prm}


# 1) o sentido do giro: a porta esquerda aberta tem de ir para fora (x menor) e o bbox medido mostra isso
mv = pose(45)
batch(mv + [{"command": "inspect.measure", "params": {"bodies": ["DoorL", "RackF", "Tray"]}}] + [UNDO] * len(mv), "sentido: porta E a 45 graus (bbox)")
# 2) varredura: nada encosta em nada (fora dos pares parafusados/encaixados)
for t in (0, 3, 6, 9, 12, 16, 20, 30, 40, 50, 60, 70, 75, P["th_rest"]):
    mv = pose(t)
    batch(mv + [interf(ALL, TOUCH)] + [UNDO] * len(mv), f"portas a {t} graus (zero)")
# 3) engrenamento: a cremalheira 0,4 abaixo ou acima do lugar tem de bater nos dentes (folga < 0,4)
for t in (5, 40, 77):
    for dz in (-0.4, 0.4):
        mv = pose(t)
        batch(mv + [{"command": "solid.move", "params": {"bodies": ["RackF"], "translate": [0, 0, dz]}},
                    interf(["RackF", "PlateLF", "PlateRF"])] + [UNDO] * (len(mv) + 1), f"engrenamento {t} graus, cremalheira {dz:+} (toca)")
# 4) batente: a th_stop + 0,5 a porta encosta na barra de baixo da dobradica
mv = pose(P["th_stop"] + 0.5)
batch(mv + [interf(["DoorL", "Base"]), interf(["DoorR", "Base"])] + [UNDO] * len(mv), f"batente a {P['th_stop'] + 0.5} graus (toca)")
# 5) trava: a nervura passa por cima do ressalto entre ~74 e 77 graus (toca no meio, livre em th_rest)
t_click = (g.Z_BUMP - (g.Z_RIDGE + g.RIDGE["lo"])) / (g.R * g.D2R)
mv = pose(t_click)
batch(mv + [interf(["RackB", "Base"])] + [UNDO] * len(mv), f"trava a {t_click:.1f} graus (toca: a lingueta cede 0,3)")
# 6) engate na emenda a 1,5 grau (as farpas forcam as hastes: toca) e fechado (zero, ja checado em 0)
mv = pose(1.5)
batch(mv + [interf(["PlateLF", "PlateRF"])] + [UNDO] * len(mv), "engate a 1,5 grau (toca)")
# 7) cauda de andorinha: ao fim da espera (12 graus) o fundo do rasgo encosta no chanfro do trilho
mv = pose(P["dwell"])
batch(mv + [{"command": "solid.move", "params": {"bodies": ["Tray"], "translate": [0, 0, -0.05]}}, interf(["Tray", "RackF"])]
      + [UNDO] * (len(mv) + 1), "fim da espera: berco 0,05 abaixo toca a cremalheira")
(HERE / "D_verificacao.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    print("\n".join(g.report()))
    print(f"{len(cmds)} comandos; {len(checks)} checagens; trava a {t_click:.1f} graus")
