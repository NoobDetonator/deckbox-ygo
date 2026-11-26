#!/usr/bin/env python3
"""Caixa D ("asas"): escreve o script do SolidCraft (D_asas_build.json) e o roteiro de verificacao
(D_verificacao.json) a partir da geometria de geo_d.py.  Rode:  python cad/D-asas/gerar_d.py

ponytail: a geometria sai numerica do Python (dentes evolventes, perfis); o .py e a fonte parametrica.
Mudou um numero? Edite P em geo_d.py e rode de novo.
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
SCREW = [(28.0, 64.0), (28.0, 91.0)]          # pinos das placas (|x|, z) nas paredes da frente/tras das portas
# pino impresso colado (super bonder): haste pela parede da porta ate 4 mm dentro da placa; a cabeca larga fica
# num rebaixo da parede, rente, e tampa o furo. Furo de 2,8 (0,15 de folga por lado para a cola); na porta o furo
# e horizontal na impressao, por isso em gota
PIN = dict(d=2.5, hole=2.8, head=4.8, cb=5.0, head_t=0.8, bite=4.0)
PIN["l"] = P["dwall_t"] - PIN["head_t"] + PIN["bite"]           # comprimento da haste (5,5)
HL = P["hk_len"] / 2

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
    extrude(name, "XZ", y0, [[(a, -b) for a, b in lp] for lp in rings(geom)], y1 - y0, op, **kw)


def xy(name, geom, z0, z1, op, **kw):
    extrude(name, "XY", z0, rings(geom), z1 - z0, op, **kw)


def yz(name, pts, x0, x1, op, **kw):
    extrude(name, "YZ", x0, [pts], x1 - x0, op, **kw)


def rounded(x0, z0, x1, z1, r):
    return sbox(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, quad_segs=6)


def flat_part(name, prof, y0, y1, op_body, ef_faces):
    """Peca que imprime deitada (perfil XZ extrudado em y): corpo + alivio do pe de elefante (0,2 x 0,3) nas faces
    que podem ir na mesa (ef_faces: 'y0', 'y1' ou as duas)."""
    xz(name, prof, y0, y1, "new", body=op_body)
    ring = prof.difference(g.relief(prof))
    if "y0" in ef_faces:
        xz(name + "EF0", ring, y0 - 0.5, y0 + P["ef_h"], "cut", targets=[op_body])
    if "y1" in ef_faces:
        xz(name + "EF1", ring, y1 - P["ef_h"], y1 + 0.5, "cut", targets=[op_body])


def detent(tag, target, ox=0.0, oy=0.0, oz=0.0, x_lo=-7.0, x_hi=7.0, z_lo=None):
    """Trava de abertura na parede de tras (ou na amostra de teste, deslocada): canal de 0,5 para a nervura da
    cremalheira, lingueta horizontal com cortes a 45 graus (imprime em pe sem suporte) e o ressalto de 0,5."""
    yi, zb = y_wi + 0.5 + oy, g.Z_BUMP + oz
    wt = Dh + oy - yi
    z0 = (g.Z_RIDGE - 1 if z_lo is None else z_lo) + oz
    box(f"{tag}Channel", x_lo + ox, x_hi + ox, y_wi - 0.01 + oy, yi, z0, ZS + 1 + oz, "cut", targets=[target])
    for nm, zs in (("SlitTop", zb + 2.5), ("SlitBot", zb - 2.5 - g.SLIT)):
        yz(f"{tag}{nm}", [(yi - 0.05, zs), (Dh + oy + 0.05, zs + wt + 0.1), (Dh + oy + 0.05, zs + wt + 0.1 + g.SLIT),
                          (yi - 0.05, zs + g.SLIT)], -6 + ox, 3.8 + ox, "cut", targets=[target])
    box(f"{tag}SlitEnd", 3 + ox, 3.8 + ox, yi - 0.1, Dh + oy + 0.1, zb - 2.5 - g.SLIT - 0.2, zb + 2.5 + g.SLIT + wt + 0.3,
        "cut", targets=[target])
    yz(f"{tag}Bump", [(yi + 0.01, zb - 0.5), (yi - 0.5, zb), (yi + 0.01, zb + 0.5)], -2.5 + ox, 2.0 + ox, "join", targets=[target])


def hinge_part(tag, s, ax, az, y0, n, a_body, b_body):
    """Dobradica print-in-place (receita da versao B, com primitivas): abas de hk_t, nos de hk_r com o eixo hk_r
    acima da face colada, n nos alternados (A nos pares, B nos impares), pino de hk_pin preso em A, furo em gota
    nos nos de B. Eixo ao longo de Y em (ax, az); a face colada olha para dentro (sentido -s em x)."""
    r, t, w, seg, gap = P["hk_r"], P["hk_t"], P["hk_w"], g.HK_SEG, P["hk_gap"]
    L = n * seg + (n - 1) * gap
    xg = ax - s * r                                           # plano da face colada
    xa = sorted((xg, xg + s * t))
    box(f"{tag}LeafA", xa[0], xa[1], y0, y0 + L, az - w, az, "new", body=a_body)
    box(f"{tag}LeafB", xa[0], xa[1], y0, y0 + L, az, az + w, "new", body=b_body)
    for i in range(n):
        yi = y0 + i * (seg + gap)
        own, other = (a_body, b_body) if i % 2 == 0 else (b_body, a_body)
        cyl(f"{tag}Knuckle{i}", r, [ax, yi, az], "Y", seg, "join", targets=[own])
        cyl(f"{tag}Clear{i}", r + P["hk_clr"], [ax, yi - gap, az], "Y", seg + 2 * gap, "cut", targets=[other])
    cyl(f"{tag}Pin", P["hk_pin"] / 2, [ax, y0, az], "Y", L, "join", targets=[a_body])
    rh = P["hk_pin"] / 2 + P["hk_pin_clr"]
    cyl(f"{tag}Hole", rh, [ax, y0 - 1, az], "Y", L + 2, "cut", targets=[b_body])
    # gota com a ponta para fora (na impressao, para cima): o teto do furo sai a 45 graus e nao cai no pino
    c45 = rh * math.cos(45 * g.D2R)
    tip = Polygon([(ax + s * c45, az + c45), (ax + s * rh * math.sqrt(2), az), (ax + s * c45, az - c45)])
    xz(f"{tag}Tear", tip, y0 - 1, y0 + L + 1, "cut", targets=[b_body])
    return L


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
detent("Detent", "Base")
xz("FrontPanel", rounded(-27, 9, 27, 47, 4), -Dh - 1, -Dh + 0.5, "cut", targets=["Base"])
cyl("FootRecess", 4.2, [-(Wh - 7), -(Dh - 7), -1], "Z", 1.6, "cut", targets=["Base"])
C("solid.pattern.rectangular", features=["FootRecess"], dir1=[1, 0, 0], count1=2, spacing1=r4(2 * Wh - 14),
  dir2=[0, 1, 0], count2=2, spacing2=r4(2 * Dh - 14), name="FootRecesses")
C("sketch.create", plane="XY", offset=-1, flip=True, name="BottomTextSk")
C("sketch.text", text_expression="bt_title", at=[0, 4], height=6, align="center", vertical_align="middle")
C("sketch.text", text_expression="bt_sub", at=[0, -4], height=3.5, align="center", vertical_align="middle")
C("sketch.finish")
C("solid.extrude", sketch="BottomTextSk", distance=1.4, direction="negative", name="BottomText", operation="cut", targets=["Base"])
# dobradica colada: rebaixo de 0,6 para a aba (folga 0,15 em volta) + canal dos nos; orelhas do batente nas pontas
pk, pc = p["hk_pocket"], P["hk_pocket_clr"]
chan = g.disc((0, 0), P["hk_r"] + P["hk_clr"], 96)
for s, tag in ((-1, "L"), (1, "R")):
    xo, xin = s * (Wh + 0.2), s * (Wh - pk)
    box(f"HingePocket{tag}", min(xo, xin), max(xo, xin), -HL - pc, HL + pc, ZS - P["hk_w"] - pc, ZS + 1, "cut", targets=["Base"])
    xz(f"HingeChannel{tag}", g.at_pivot(chan, s), -HL - pc - 0.25, HL + pc + 0.25, "cut", targets=["Base"])
    for k, (e0, e1) in enumerate(((-g.EAR_Y[1], -g.EAR_Y[0]), g.EAR_Y)):
        xz(f"Ear{tag}{k}", g.at_pivot(g.base_ear(), s), e0, e1, "join", targets=["Base"])

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
    # friso no teto (moldura de 1,0 rebaixada 0,4; na mesa, entao larga o bastante para o pe de elefante nao fechar)
    xo = (-Wh + 5, -4) if s < 0 else (4, Wh - 5)
    ring = rounded(xo[0], -Dh + 5, xo[1], Dh - 5, 3).difference(rounded(xo[0] + 1.0, -Dh + 6, xo[1] - 1.0, Dh - 6, 2.0))
    xy(f"Door{tag}Frame", ring, H - 0.4, H + 0.6, "cut", targets=[body])
    for k, (sx, sz) in enumerate(SCREW):
        for f, y0, y1, ycb in (("F", -Dh - 0.5, -y_bo + 0.5, -Dh - 0.5), ("B", y_bo - 0.5, Dh + 0.5, Dh - PIN["head_t"])):
            xz(f"PinHole{f}{tag}{k}", affinity.translate(g.teardrop(PIN["hole"] / 2, False), s * sx, sz), y0, y1, "cut", targets=[body])
            cyl(f"PinRecess{f}{tag}{k}", PIN["cb"] / 2, [s * sx, ycb, sz], "Y", PIN["head_t"] + 0.5, "cut", targets=[body])
    xo, xin = s * (Wh + 0.2), s * (Wh - pk)
    box(f"DoorPocket{tag}", min(xo, xin), max(xo, xin), -HL - pc, HL + pc, ZS - 1, ZS + P["hk_w"] + pc, "cut", targets=[body])
    xz(f"DoorChannel{tag}", g.at_pivot(chan, s), -HL - pc - 0.25, HL + pc + 0.25, "cut", targets=[body])
cyl("ThumbNotch", 4.5, [0, -Dh - 1, H], "Y", 2.5, "cut", targets=["DoorL", "DoorR"])

# ======================= DOBRADICAS (print-in-place, coladas) =======================
for s, tag in ((-1, "L"), (1, "R")):
    hinge_part(f"Hinge{tag}", s, s * XP, ZS, -HL, P["hk_n"], f"Hinge{tag}A", f"Hinge{tag}B")

# ======================= PLACAS-SETOR (4) =======================
# as da frente e de tras sao a mesma peca (o perfil e simetrico na espessura): alivio do pe de elefante nas duas faces
for s, tag in ((-1, "L"), (1, "R")):
    prof = g.plate(s)
    for side, y0, y1 in (("F", -y_bo, -y_bi), ("B", y_bi, y_bo)):
        body = f"Plate{tag}{side}"
        flat_part(f"Plate{tag}{side}Body", prof, y0, y1, body, ("y0", "y1"))
        for k, (sx, sz) in enumerate(SCREW):
            cyl(f"Plate{tag}{side}PinHole{k}", PIN["hole"] / 2, [s * sx, y0 - 0.5, sz], "Y", y1 - y0 + 1, "cut", targets=[body])

# ======================= CREMALHEIRAS (2) =======================
rk, z_top = g.rack()
gp = g.groove_profile()
for side, sg in (("F", -1), ("B", 1)):
    body = f"Rack{side}"
    y0, y1 = (-y_bo, -y_bi) if sg < 0 else (y_bi, y_bo)
    flat_part(f"Rack{side}Body", rk, y0, y1, body, ("y1",) if sg < 0 else ("y0",))   # a face do rasgo vai na mesa
    xy(f"Rack{side}Groove", Polygon([(x, sg * (y_bi + d)) for x, d in gp]), g.Z_GE, z_top + 1, "cut", targets=[body])
rd = g.RIDGE
yz("RackBRidge", [(y_bo - 0.01, g.Z_RIDGE), (y_bo + rd["h"], g.Z_RIDGE + rd["lo"]), (y_bo - 0.01, g.Z_RIDGE + rd["lo"] + rd["up"])],
   -4.5, 4.5, "join", targets=["RackB"])

# ======================= BERCO =======================
box("TrayBlock", -x_co, x_co, -y_co, y_co, P["base_t"], ZS - 0.5, "new", body="Tray")
C("solid.fillet", body="Tray", edges=[[sx * x_co, sy * y_co, 30] for sx in (1, -1) for sy in (1, -1)], radius=1.6, name="TrayCorners")
C("solid.chamfer", body="Tray", edges=[[0, -y_co, P["base_t"]]], distance=0.6, name="TrayLeadIn")
box("TrayInside", -p["in_x"] / 2, p["in_x"] / 2, -p["in_y"] / 2, p["in_y"] / 2, P["base_t"] + P["crad_f"], ZS + 1, "cut", targets=["Tray"])
rl = g.RAIL


def rail_poly(sg, y_face):
    """Trilho em cauda de andorinha saindo da face y_face (sg = sentido para fora)."""
    return Polygon([(-rl["neck"], y_face - sg * 0.3), (rl["neck"], y_face - sg * 0.3), (rl["neck"], y_face + sg * P["rail_clr"]),
                    (rl["tip"], y_face + sg * (P["rail_clr"] + rl["h"])), (-rl["tip"], y_face + sg * (P["rail_clr"] + rl["h"])),
                    (-rl["neck"], y_face + sg * P["rail_clr"])])


for side, sg in (("F", -1), ("B", 1)):
    xy(f"TrayRail{side}", rail_poly(sg, sg * y_co), g.Z_RB, g.Z_RT, "join", targets=["Tray"])
    ye = sg * (y_bi + rl["h"] + 0.1)
    yz(f"TrayRailChamfer{side}", [(sg * (y_co - 0.01), g.Z_RB - 0.01), (ye, g.Z_RB - 0.01), (ye, g.Z_RB + abs(ye) - y_co)],
       -4, 4, "cut", targets=["Tray"])

# ======================= DIVISORIA, BLOCO DE CARTAS, PINO DAS PLACAS =======================
div_w, div_h, tab_w = p["in_x"] - 2 * P["liner_t"] - 0.8, P["card_h"] - 7, 22.0
box("DividerPlate", Wh + 15, Wh + 15 + div_w, -Dh, -Dh + div_h, 0, P["div_t"], "new", body="Divider")
box("DividerTab", Wh + 15 + (div_w - tab_w) / 2, Wh + 15 + (div_w + tab_w) / 2, -Dh + div_h - 1, -Dh + P["card_h"] + 1, 0, P["div_t"], "join", targets=["Divider"])
deck_t = P["n_cards"] * P["card_t"] + P["div_t"]
yb = p["in_y"] / 2 - P["liner_t"]
box("DeckBlock", -P["card_w"] / 2, P["card_w"] / 2, yb - deck_t, yb, p["card_z0"], p["card_top"], "new", body="Deck")


def plate_pin(name, x, y, body):
    cyl(name + "Head", PIN["head"] / 2, [x, y, 0], "Z", PIN["head_t"], "new", body=body)
    cyl(name + "Shaft", PIN["d"] / 2, [x, y, PIN["head_t"] - 0.01], "Z", PIN["l"] + 0.01, "join", targets=[body])


plate_pin("PlatePin", Wh + 15, -Dh - 12, "PlatePin")       # em pe sobre a cabeca (posicao de impressao)

# ======================= PECAS DE TESTE (imprima antes de tudo, ~10 g) =======================
# Ja na posicao de impressao, longe da caixa. Deitadas (Z = altura na mesa): equipamento da engrenagem (base com
# trilho e eixo, setor, cremalheira), pedacos da emenda (engate, ima, furo do pino), mini dobradica, 1 pino.
# Em pe: pedaco da parede da porta (furo em gota), lingueta da trava, trilho do berco.
TX, TY = Wh + 60.0, 0.0                       # canto da area de teste
FLAT, UP_ = [], []
# --- equipamento da engrenagem: o eixo do setor e o centro do trilho ficam a XP, como na caixa
PV = (TX + 8, TY + 30)                        # eixo do setor (mundo x, z -> mesa X, Y)
to_rig = lambda geom: affinity.translate(geom, PV[0] + XP, PV[1] - ZS)    # mundo (x, z) da placa esquerda -> mesa
rail_x = PV[0] + XP
fr = sbox(rail_x - 7, PV[1] - 28, rail_x + 7, PV[1] + 18).union(sbox(PV[0] - 5, PV[1] - 4, rail_x, PV[1] + 4)).union(g.disc(PV, 6, 48))
xy("RigFrame", fr, 0, 2, "new", body="TestRig")
rig_rail = Polygon([(rail_x - rl["neck"], 0), (rail_x + rl["neck"], 0), (rail_x + rl["neck"], 0.3),
                    (rail_x + rl["tip"], 0.3 + rl["h"]), (rail_x - rl["tip"], 0.3 + rl["h"]), (rail_x - rl["neck"], 0.3)])
xz("RigRail", affinity.translate(rig_rail, 0, 2), PV[1] - 28, PV[1] + 18, "join", targets=["TestRig"])
cyl("RigBoss", 4.5, [PV[0], PV[1], 1.99], "Z", 0.31, "join", targets=["TestRig"])
cyl("RigPin", 1.2, [PV[0], PV[1], 2.2], "Z", 6.8, "join", targets=["TestRig"])
s_pitch = p["pitch"] / 2 - 2 * P["bl"]
pie = Polygon([(0, 0)] + [(p["Rf"] * math.cos(a * g.D2R), p["Rf"] * math.sin(a * g.D2R)) for a in g.frange(-56, -18, 1)])
sector = g.at_pivot(pie.union(Polygon(g.tooth(-3 * p["tau"], p["Rf"] - 0.05, s_pitch))).union(
    g.unary_union([Polygon(g.tooth(-j * p["tau"], p["Rf"] - 0.05, s_pitch)) for j in (4, 5, 6)])), -1)
sector = to_rig(sector).union(g.disc(PV, 4.5, 48)).difference(g.disc(PV, 1.4, 32))
xy("RigSector", sector, 2.3, 2.3 + P["lay_t"], "new", body="TestSector")
xy("RigSectorEF", sector.difference(g.relief(sector)), 2.0, 2.3 + P["ef_h"], "cut", targets=["TestSector"])
rack_frag = to_rig(rk.intersection(sbox(-20, 26.6, 20, 45.6)))     # dentes 3 a 6 inteiros
xy("RigRack", rack_frag, 2.3, 2.3 + P["lay_t"], "new", body="TestRack")
xy("RigRackEF", rack_frag.difference(g.relief(rack_frag)), 2.0, 2.3 + P["ef_h"], "cut", targets=["TestRack"])
xz("RigRackGroove", Polygon([(rail_x + x, 2.3 + d) for x, d in gp]), PV[1] - 40, PV[1] + 30, "cut", targets=["TestRack"])
FLAT += ["TestRig", "TestSector", "TestRack"]
# --- pedacos da emenda: engate + ima + furo de pino (esquerda) e receptaculo (direita), deitados
ox, oy = TX + 62, TY - 60
snapL = affinity.translate(g.plate(-1).intersection(sbox(-12, 70, 5.5, 95)), ox + 12, oy - 70)
snapL = snapL.difference(g.disc((ox + 4, oy + 10), PIN["hole"] / 2, 32))
xy("TestSnapL", snapL, 0, P["lay_t"], "new", body="TestSnapL")
xy("TestSnapLEF", snapL.difference(g.relief(snapL)), -0.5, P["ef_h"], "cut", targets=["TestSnapL"])
snapR = affinity.translate(g.plate(1).intersection(sbox(0, 80, 10, 95)), ox + 22, oy - 70 + 10)
xy("TestSnapR", snapR, 0, P["lay_t"], "new", body="TestSnapR")
xy("TestSnapREF", snapR.difference(g.relief(snapR)), -0.5, P["ef_h"], "cut", targets=["TestSnapR"])
FLAT += ["TestSnapL", "TestSnapR"]
# --- mini dobradica (3 nos, mesmas folgas), deitada como a de verdade: face colada na mesa. Montada em pe com a
#     face colada em x = 0 (eixo em x = -hk_r) e girada 90 graus em Y na origem: x = 0 vira a mesa (z = 0)
hinge_part("TestHinge", -1, -P["hk_r"], TX + 12, TY - 60, 3, "TestHingeA", "TestHingeB")
C("solid.move", bodies=["TestHingeA", "TestHingeB"], axis=[0, 1, 0], angle="90 deg", name="TestHingeFlat")
FLAT += ["TestHingeA", "TestHingeB"]
plate_pin("TestPin", TX + 30, TY - 70, "TestPin")
FLAT.append("TestPin")
# --- em pe: parede da porta (2,3) com o furo em gota e o rebaixo da cabeca; lingueta da trava; trilho do berco
ux, uy = TX + 2, TY + 62
box("TestWall", ux, ux + 18, uy, uy + P["dwall_t"], 0, 14, "new", body="TestWall")
xz("TestWallHole", affinity.translate(g.teardrop(PIN["hole"] / 2, True), ux + 9, 7), uy - 0.5, uy + P["dwall_t"] + 0.5, "cut", targets=["TestWall"])
cyl("TestWallRecess", PIN["cb"] / 2, [ux + 9, uy - 0.5, 7], "Y", PIN["head_t"] + 0.5, "cut", targets=["TestWall"])
# lingueta: o pedaco da parede de tras entre x -9 e 6 e z 40 a 55, transladado para a area de teste
tox, toy, toz = ux + 32, uy - Dh + 6, -40
box("TestTongueWall", -9 + tox, 6 + tox, y_wi + toy, Dh + toy, 40 + toz, ZS + toz, "new", body="TestTongue")
detent("TestTongue", "TestTongue", tox, toy, toz, z_lo=41.0)
UP_ += ["TestWall", "TestTongue"]
# trilho: um pedaco da parede do berco (1,6) com o trilho, em pe como o berco
rx, ry = ux + 52, uy + 2
box("TestRailWall", rx - 6, rx + 6, ry - P["crad_t"], ry, 0, 16, "new", body="TestRail")
xy("TestRailDT", affinity.translate(rail_poly(1, 0), rx, ry), 0, 16, "join", targets=["TestRail"])
yz("TestRailChamfer", [(ry - 0.01, -0.01), (ry + P["rail_clr"] + rl["h"] + 0.1, -0.01), (ry + P["rail_clr"] + rl["h"] + 0.1, P["rail_clr"] + rl["h"] + 0.11)],
   rx - 4, rx + 4, "cut", targets=["TestRail"])
UP_.append("TestRail")

COLORS = {"Base": "#1c2331", "DoorL": "#c9a227", "DoorR": "#c9a227", "Tray": "#7a2230", "Divider": "#a8322d",
          "Deck": "#e8e2d0", "RackF": "#c0c6cc", "RackB": "#c0c6cc", "PlatePin": "#c9a227"}
for b in ("PlateLF", "PlateLB", "PlateRF", "PlateRB"):
    COLORS[b] = "#9aa3ad"
for b in ("HingeLA", "HingeRA"):
    COLORS[b] = "#3a4560"
for b in ("HingeLB", "HingeRB"):
    COLORS[b] = "#b08d1f"
for b in FLAT + UP_:
    COLORS[b] = "#6c8a9e"
for b, c in COLORS.items():
    C("appearance.assign", bodies=[b], color=c)

(HERE / "D_asas_build.json").write_text(json.dumps({"commands": cmds}, ensure_ascii=False, indent=1), encoding="utf-8")

# ======================= VERIFICACAO (chamadas MCP) =======================
DOOR = {-1: ["DoorL", "PlateLF", "PlateLB", "HingeLB"], 1: ["DoorR", "PlateRF", "PlateRB", "HingeRB"]}
RACKS, UP, FIXED = ["RackF", "RackB"], ["Tray", "Deck"], ["Base", "HingeLA", "HingeRA"]
ALL = FIXED + DOOR[-1] + DOOR[1] + RACKS + UP
TOUCH = [["DoorL", "PlateLF"], ["DoorL", "PlateLB"], ["DoorR", "PlateRF"], ["DoorR", "PlateRB"], ["Tray", "RackF"], ["Tray", "RackB"],
         ["Base", "HingeLA"], ["Base", "HingeRA"], ["DoorL", "HingeLB"], ["DoorR", "HingeRB"]]
UNDO = {"command": "undo", "params": {}}


def turn(bodies, deg, ox, oz, axis=(0, 1, 0)):
    # gira em volta de (ox, ., oz): translada-gira-volta (o solid.move gira na origem)
    return [{"command": "solid.move", "params": {"bodies": bodies, "translate": [-ox, 0, -oz] if axis[1] else [-ox, -oz, 0]}},
            {"command": "solid.move", "params": {"bodies": bodies, "axis": list(axis), "angle": f"{deg:.4f} deg"}},
            {"command": "solid.move", "params": {"bodies": bodies, "translate": [ox, 0, oz] if axis[1] else [ox, oz, 0]}}]


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
# 2) varredura: nada encosta em nada (fora dos pares colados/encaixados); perto do clique a nervura da cremalheira
#    passa por cima do ressalto da lingueta de proposito: ali o par cremalheira de tras x base fica para a checagem 5
t_click = (g.Z_BUMP - (g.Z_RIDGE + g.RIDGE["lo"])) / (g.R * g.D2R)
for t in (0, 3, 6, 9, 12, 16, 20, 30, 40, 50, 60, 70, 75, P["th_rest"]):
    mv = pose(t)
    near = abs(t - t_click) < 2.5
    batch(mv + [interf(ALL, TOUCH + ([["RackB", "Base"]] if near else []))] + [UNDO] * len(mv),
          f"portas a {t} graus (zero{', menos a trava' if near else ''})")
# 3) engrenamento: a cremalheira 0,45 abaixo ou acima do lugar tem de bater nos dentes (folga < 0,45)
for t in (5, 40, 77):
    for dz in (-0.45, 0.45):
        mv = pose(t)
        batch(mv + [{"command": "solid.move", "params": {"bodies": ["RackF"], "translate": [0, 0, dz]}},
                    interf(["RackF", "PlateLF", "PlateRF"])] + [UNDO] * (len(mv) + 1), f"engrenamento {t} graus, cremalheira {dz:+} (toca)")
# 4) batente: a th_stop + 0,5 a lateral da porta encosta nas orelhas da base
mv = pose(P["th_stop"] + 0.5)
batch(mv + [interf(["DoorL", "Base"]), interf(["DoorR", "Base"])] + [UNDO] * len(mv), f"batente a {P['th_stop'] + 0.5} graus (toca)")
# 5) trava: a nervura passa por cima do ressalto entre ~74 e 77 graus (toca no meio, livre em th_rest)
mv = pose(t_click)
batch(mv + [interf(["RackB", "Base"])] + [UNDO] * len(mv), f"trava a {t_click:.1f} graus (toca: a lingueta cede 0,3)")
# 6) engate na emenda a 1,5 grau (as farpas forcam as hastes: toca)
mv = pose(1.5)
batch(mv + [interf(["PlateLF", "PlateRF"])] + [UNDO] * len(mv), "engate a 1,5 grau (toca)")
# 7) cauda de andorinha: ao fim da espera (12 graus) o fundo do rasgo encosta no chanfro do trilho
mv = pose(P["dwell"])
batch(mv + [{"command": "solid.move", "params": {"bodies": ["Tray"], "translate": [0, 0, -0.05]}}, interf(["Tray", "RackF"])]
      + [UNDO] * (len(mv) + 1), "fim da espera: berco 0,05 abaixo toca a cremalheira")
# 8) dobradicas: pino solto no furo e nos sem se tocar, fechada e a 78 graus; a aba colada toca o fundo do rebaixo
for t in (0, P["th_stop"]):
    mv = turn(["HingeLB"], -t, -XP, ZS) if t else []
    batch(mv + [interf(["HingeLA", "HingeLB"])] + [UNDO] * len(mv), f"dobradica esquerda a {t} graus: pino e nos livres (zero)")
batch([{"command": "solid.move", "params": {"bodies": ["HingeLA"], "translate": [0.05, 0, 0]}}, interf(["HingeLA", "Base"]), UNDO],
      "aba da dobradica 0,05 para dentro toca o fundo do rebaixo (toca)")


# 9) pinos das placas: no lugar nao tocam nada; sondas 0,1 mais grossas tocam (furo 2,8, rebaixo 5,0)
def pin_bodies(name, s, sx, sz, f, dr=0.0):
    fy = -1 if f == "F" else 1
    yh = -Dh if fy < 0 else Dh - PIN["head_t"]
    ys = -Dh + PIN["head_t"] if fy < 0 else Dh - PIN["head_t"] - PIN["l"]
    cy = lambda nm, r, y0, h: {"command": "solid.cylinder", "params": {"radius": r4(r), "height": r4(h), "axis": "Y",
                                                                         "base": [r4(s * sx), r4(y0), sz], "operation": "new", "body_name": nm}}
    return [cy(name + "H", PIN["head"] / 2 + dr, yh, PIN["head_t"]), cy(name + "S", PIN["d"] / 2 + dr, ys, PIN["l"])]


pins, names = [], []
for s, tag in ((-1, "L"), (1, "R")):
    for f in "FB":
        for k, (sx, sz) in enumerate(SCREW):
            pins += pin_bodies(f"PP{tag}{f}{k}", s, sx, sz, f)
            names += [f"PP{tag}{f}{k}H", f"PP{tag}{f}{k}S"]
batch(pins + [interf(names + ["DoorL", "DoorR"] + [b for b in ALL if b.startswith("Plate")])] + [UNDO] * len(pins),
      "pinos das placas no lugar (zero)")
for part in ("DoorR", "PlateRF"):
    batch(pin_bodies("ProbePin", 1, SCREW[0][0], SCREW[0][1], "F", dr=0.05 + (PIN["hole"] - PIN["d"]) / 2)[1:]
          + [interf(["ProbePinS", part]), UNDO], f"furo do pino com {PIN['hole']} em {part} (sonda 0,1 maior toca)")
batch(pin_bodies("ProbeHead", 1, SCREW[0][0], SCREW[0][1], "F", dr=0.05 + (PIN["cb"] - PIN["head"]) / 2)[:1]
      + [interf(["ProbeHeadH", "DoorR"]), UNDO], f"rebaixo da cabeca com {PIN['cb']} (sonda 0,1 maior toca)")
# 10) pecas de teste: o equipamento engrena (setor girado 38 graus, cremalheira no curso) sem tocar e a mini
#     dobradica sai solta da mesa
ang = 38.0
rig = [{"command": "solid.move", "params": {"bodies": ["TestRack"], "translate": [0, r4(g.travel(ang)), 0]}}]
rig += turn(["TestSector"], ang, PV[0], PV[1], axis=(0, 0, 1))
batch(rig + [interf(["TestRig", "TestSector", "TestRack"])] + [UNDO] * len(rig), "teste: engrenagem montada a 38 graus (zero)")
batch(rig + [{"command": "solid.move", "params": {"bodies": ["TestRack"], "translate": [0, 0.45, 0]}},
             interf(["TestSector", "TestRack"])] + [UNDO] * (len(rig) + 1), "teste: engrenagem, cremalheira +0,45 (toca)")
batch([interf(["TestHingeA", "TestHingeB"])], "teste: mini dobradica impressa (zero)")
(HERE / "D_verificacao.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    print("\n".join(g.report()))
    print(f"{len(cmds)} comandos; {len(checks)} checagens; trava a {t_click:.1f} graus")
