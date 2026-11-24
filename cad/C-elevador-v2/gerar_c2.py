#!/usr/bin/env python3
"""Versao C V2 ("elevador"): gera o script do SolidCraft e o roteiro de verificacao.

Mecanismo (igual nos dois lados, nas cavidades laterais):
  tampa -> manivela (gira com a tampa no eixo H) -> pino C numa ranhura de came do balancim
  -> balancim (pivo Q no corpo) -> pino E num garfo horizontal da lingua do berco -> berco sobe.
A ranhura e calculada aqui a partir da lei de elevacao (3 fases). Mudou lift_*, th_*, crank_*,
lev_* ou h_a/h_b? Rode de novo:  python cad/C-elevador-v2/gerar_c2.py
Saidas: C2_elevador_build.json (modelo) e C2_verificacao.json (chamadas MCP das checagens).

Mudancas da V2 (revisao depois da impressao da C):
- berco apoiado no fundo com a tampa fechada e folga morta de 0,6 mm no garfo: o mecanismo fica sem carga fechado
  (na C o deck pendurado punha ~33 N em cada pino da manivela e do pivo, o tempo todo);
- painel de 3,0 mm em L, dobrando na quina de tras: os furos do eixo e do pivo ficam inteiros (na C passavam da borda);
- painel preso com 4 parafusos M2 auto-atarraxantes (2 na frente, 2 pela dobra de tras), sem cola;
- eixo e pivo entram por fora depois do painel: cabeca rebaixada, apertados no painel, soltos no corpo (furo de 1,6);
- peca de teste de folgas (furos de 2,8 a 3,5) para calibrar antes de imprimir tudo.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
D2R = math.pi / 180

# ---------------- parametros (valores numericos, iguais aos do SolidCraft) ----------------
P = dict(card_w=62.5, card_h=91.0, card_t=0.68, n_cards=90, liner_t=1.0, play_x=1.5, play_y=2.0,
         play_z=1.5, div_t=1.6, shrink=0.006,
         crad_t=1.6, crad_f=1.6, crad_gap=0.0, core_t=2.0, base_t=2.0, roof_t=2.0, lid_t=2.4,
         rail_clr=0.3, cam_clr=0.3, hinge_clr=0.2, pin_press=-0.1, weld_clr=0.05, lay_t=3.2,
         shell_t=3.0, sh_m=4.0, sh_z0=3.0, fl_t=2.0, fl_in=4.0, shell_press=0.1, head_d=5.0, head_t=0.9,
         back_t=6.8, h_b=10.8, lid_h=12.4, r_out=4.0, bed_ch=0.8, top_ch=1.0, reveal=0.4,
         pin_d=3.0, pin_s_d=2.8, pin_bl=1.6, hub_r=3.3, tg_w=9.2, tg_h=14.0, u_w=30.0, u_d=18.0,
         mag_d=4.0, mag_t=2.0, mag_stack=1, mag_clr=0.2, sg_d=0.5, sg_h=1.2,
         foot_d=8.4, foot_h=0.6, foot_e=7.0,
         bt_d=0.4, bt_y=4.0, div_gap=0.4, tab_w=22.0)
# cinematica (etapa 1)
LIFT_H, LIFT_OD, TH1, TH2, TH3, BLEND = 22.0, 0.6, 25.0, 95.0, 110.0, 20.0
YOKE_SLACK = 0.6   # folga morta no garfo: fechado, o berco descansa no fundo e o pino E nao carrega nada;
                   # o mecanismo sobe LIFT_H + YOKE_SLACK e o berco, LIFT_H
CRANK_R, CRANK_A0 = 10.0, 260.0          # manivela: raio e angulo (graus, a partir de +Y, anti-horario visto de +X)
QY, QZ, LEV_R2, PHI_END = 0.0, -16.0, 60.0, 15.0   # pivo Q relativo a H; braco de saida; inclinacao final
SLOT_W = P["pin_d"] + 2 * P["cam_clr"]   # largura das ranhuras
LEV_WALL, ARM_HW = 1.65, 4.0             # parede em volta da ranhura (4 perimetros); meia largura do braco de saida
LEV_HUB_R = ARM_HW                       # cubo do pivo e ponta do balancim: raio = meia largura, ponta redonda sem canto sobrando
CRANK_HW, CRANK_HUB_R = 3.2, 4.0         # manivela: meia largura do braco (= raio do ressalto do pino) e raio do cubo
CAP_T = 1.6                              # tampa da cavidade no painel (era 2,0: abre espaco para o balancim mais grosso)
RING_IN, RING_OUT, RING_A0 = 10.8, 15.0, 115.0    # gancho da manivela; com back_t 6,8 o anel interno sobe de 10,3 para 10,8
BN_Z = P["h_b"] - 2.8                    # entalhe traseiro sob a tampa, relativo ao eixo (back_t 6,8 pede 2,8 mm)

# ---------------- derivados ----------------
p = dict(P)
p["k"] = 1 + p["shrink"]
p["in_x"] = p["k"] * (p["card_w"] + 2 * p["liner_t"] + p["play_x"])
p["in_y"] = p["k"] * (p["n_cards"] * p["card_t"] + p["div_t"] + 2 * p["liner_t"] + p["play_y"])
p["in_z"] = p["k"] * (p["card_h"] + 2 * p["liner_t"] + p["play_z"])
p["cav_w"] = 2 * p["lay_t"] + 3 * p["cam_clr"]
p["W"] = p["in_x"] + 2 * (p["crad_t"] + p["rail_clr"] + p["core_t"] + p["cav_w"] + p["shell_t"])
p["D"] = p["in_y"] + 2 * p["crad_t"] + 2 * p["rail_clr"] + p["core_t"] + p["back_t"]
p["H"] = p["base_t"] + p["crad_gap"] + p["crad_f"] + p["in_z"] + p["roof_t"]
p["split"] = p["H"] - p["lid_h"]
p["Hy"], p["Hz"] = p["D"] / 2 - p["back_t"], p["split"] - p["h_b"]


def L(t):
    """Elevacao do mecanismo (pino E, mm) pelo angulo da tampa (graus). O berco sobe Lc(t)."""
    h = LIFT_H + YOKE_SLACK + LIFT_OD
    if t <= TH1:
        return 0.0
    if t <= TH2:
        beta, w = TH2 - TH1, BLEND
        v = h / (beta - w)
        u = t - TH1
        ramp = lambda x: (x - w / math.pi * math.sin(math.pi * x / w)) / 2
        if u <= w:
            return v * ramp(u)
        if u <= beta - w:
            return v * (w / 2 + u - w)
        return v * ((beta - w) - ramp(beta - u))
    u = min(t, TH3) - TH2
    return h - LIFT_OD * (1 - math.cos(math.pi * u / (TH3 - TH2))) / 2


def Lc(t):
    """Elevacao do berco: o pino E primeiro vence a folga morta do garfo."""
    return max(0.0, L(t) - YOKE_SLACK)


PHI0 = math.degrees(math.asin(math.sin(PHI_END * D2R) - (LIFT_H + YOKE_SLACK + LIFT_OD) / LEV_R2))
phi = lambda t: math.degrees(math.asin(math.sin(PHI0 * D2R) + L(t) / LEV_R2))
crank = lambda t: (CRANK_R * math.cos((CRANK_A0 - t) * D2R), CRANK_R * math.sin((CRANK_A0 - t) * D2R))


def rot_ccw(v, deg):
    c, s = math.cos(deg * D2R), math.sin(deg * D2R)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


# ranhura no referencial do balancim (pose fechada), relativa a Q; balancim gira horario de (phi - phi0)
SLOT_EXTRA = 2.0  # a ranhura passa 2 graus do fim (berco parado): quem para a tampa e o batente; 3+ bate na tampa da cavidade
TS = [i * 1.0 for i in range(int(TH3 + SLOT_EXTRA) + 1)]
SLOT = [rot_ccw((crank(t)[0] - QY, crank(t)[1] - QZ), phi(t) - PHI0) for t in TS]
E0 = (QY - LEV_R2 * math.cos(PHI0 * D2R), QZ + LEV_R2 * math.sin(PHI0 * D2R))   # pino E fechado (rel. H)


def offset_outline(pts, r, n_cap=10):
    """Contorno fechado a distancia r de uma polilinha (lados + meias-luas nas pontas)."""
    def normal(i):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy)
        return (-dy / l, dx / l)
    left = [(q[0] + r * normal(i)[0], q[1] + r * normal(i)[1]) for i, q in enumerate(pts)]
    right = [(q[0] - r * normal(i)[0], q[1] - r * normal(i)[1]) for i, q in enumerate(pts)]
    def cap(c, n, sgn):
        a0 = math.atan2(n[1], n[0])
        return [(c[0] + r * math.cos(a0 - sgn * math.pi * j / n_cap), c[1] + r * math.sin(a0 - sgn * math.pi * j / n_cap))
                for j in range(1, n_cap)]
    return left + cap(pts[-1], normal(len(pts) - 1), 1) + right[::-1] + cap(pts[0], (-normal(0)[0], -normal(0)[1]), 1)


def hull(points):
    pts = sorted(set((round(a, 4), round(b, 4)) for a, b in points))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def circle(c, r, n=24):
    return [(c[0] + r * math.cos(2 * math.pi * j / n), c[1] + r * math.sin(2 * math.pi * j / n)) for j in range(n)]


def ring_outline():
    """Gancho: anel entre RING_IN e RING_OUT de RING_A0 a 262 graus, cortado na divisao (z' <= h_b)."""
    rc, rr = (RING_IN + RING_OUT) / 2, (RING_OUT - RING_IN) / 2
    a_end = 262.0 - math.degrees(rr / rc)   # ponta redonda (meia-lua) que chega onde ficava o canto, sem bico para fora
    a_out = 180 - math.degrees(math.asin(P["h_b"] / RING_OUT))       # anel externo cruza a divisao
    pts = [(RING_OUT * math.cos(a * D2R), RING_OUT * math.sin(a * D2R)) for a in frange(a_out, a_end, 4)]
    cen = (rc * math.cos(a_end * D2R), rc * math.sin(a_end * D2R))
    pts += [(cen[0] + rr * math.cos(b * D2R), cen[1] + rr * math.sin(b * D2R)) for b in frange(a_end + 15, a_end + 165, 15)]
    pts += [(RING_IN * math.cos(a * D2R), RING_IN * math.sin(a * D2R)) for a in frange(a_end, RING_A0, -4)]
    r_s = P["h_b"] / math.sin(RING_A0 * D2R)
    pts += [(r_s * math.cos(RING_A0 * D2R), P["h_b"])]
    return pts


def frange(a, b, step):
    n = max(2, int(abs(b - a) / abs(step)) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ---------------- emissao ----------------
cmds = []
C = lambda _cmd, **params: cmds.append({"command": _cmd, "params": params})
f = lambda x: f"{x:.4f}".rstrip("0").rstrip(".")
ry = lambda v: f"Hy + {f(v)}" if v >= 0 else f"Hy - {f(-v)}"      # y relativo ao eixo H -> expressao
rz = lambda v: f"Hz + {f(v)}" if v >= 0 else f"Hz - {f(-v)}"

def param(name, expr, comment, unit=None, fav=False):
    d = {"name": name, "expression": expr, "comment": comment}
    if unit is not None:
        d["unit"] = unit
    if fav:
        d["favorite"] = True
    C("parameters.add", **d)

mm = lambda n: f"{f(P[n])} mm"
param("card_w", mm("card_w"), "carta com sleeve (sleeve japones 62 + 0,5)")
param("card_h", mm("card_h"), "carta com sleeve (89 + costura)")
param("card_t", mm("card_t"), "CALIBRAR: espessura por carta com sleeve duplo", fav=True)
param("n_cards", "90", "capacidade", unit="")
param("liner_t", mm("liner_t"), "CALIBRAR: forro em todas as faces internas", fav=True)
param("play_x", mm("play_x"), "folga livre na largura")
param("play_y", mm("play_y"), "folga livre na profundidade")
param("play_z", mm("play_z"), "folga livre em cima")
param("div_t", mm("div_t"), "divisoria")
param("shrink", "0.006", "CALIBRAR: contracao do ABS (so onde o ABS encosta em carta, ima ou aco)", unit="", fav=True)
param("k", "1 + shrink", "fator de compensacao", unit="")
param("in_x", "k*(card_w + 2*liner_t + play_x)", "interior do berco: largura", fav=True)
param("in_y", "k*(n_cards*card_t + div_t + 2*liner_t + play_y)", "interior do berco: profundidade", fav=True)
param("in_z", "k*(card_h + 2*liner_t + play_z)", "do piso do berco ao teto da tampa", fav=True)
for n, c in [("crad_t", "parede do berco"), ("crad_f", "piso do berco"), ("crad_gap", "berco acima do fundo"),
             ("core_t", "parede do nucleo"), ("base_t", "fundo"), ("roof_t", "teto da tampa"), ("lid_t", "parede da tampa"),
             ("lay_t", "espessura de cada camada do mecanismo"), ("shell_t", "painel externo"),
             ("sh_m", "borda do nucleo em volta do painel"), ("sh_z0", "base do painel"),
             ("back_t", "eixo da tampa: distancia da face traseira (h_a)"), ("h_b", "eixo da tampa abaixo da divisao"),
             ("lid_h", "altura da tampa"), ("r_out", "raio das quinas"), ("bed_ch", "chanfro da base"),
             ("top_ch", "chanfro do topo"), ("reveal", "chanfro da divisao"), ("pin_d", "pinos de aco"),
             ("pin_bl", "profundidade dos furos cegos dos pinos"), ("hub_r", "raio dos cubos"),
             ("tg_w", "lingua do berco: largura"), ("tg_h", "lingua do berco: altura"), ("u_w", "recorte em U: largura"),
             ("u_d", "recorte em U: profundidade"), ("mag_d", "ima"), ("mag_t", "ima"), ("sg_d", "linha de sombra"),
             ("sg_h", "linha de sombra"), ("foot_d", "pes de silicone"), ("foot_h", "pes"),
             ("foot_e", "pes: distancia da borda"), ("bt_d", "texto do fundo"), ("bt_y", "texto do fundo"),
             ("div_gap", "folga lateral da divisoria"), ("tab_w", "aba da divisoria"),
             ("fl_t", "painel: espessura da dobra de tras (e a parede de tras da cavidade)"),
             ("fl_in", "painel: quanto a dobra de tras entra na traseira do corpo (onde vao os parafusos)"),
             ("head_d", "eixo e pivo: diametro da cabeca"), ("head_t", "eixo e pivo: altura da cabeca")]:
    param(n, mm(n), c)
param("shell_press", mm("shell_press"), "CALIBRAR: aperto do eixo e do pivo no painel (furo = pin_d - shell_press)", fav=True)
for n, c in [("rail_clr", "CALIBRAR: folga berco x nucleo (cada lado)"), ("cam_clr", "CALIBRAR: folga dos pinos nas ranhuras e entre camadas"),
             ("hinge_clr", "CALIBRAR: folga radial dos furos que giram"), ("pin_press", "CALIBRAR: aperto dos pinos fixos (negativo = folga: furo de 3,1, pino colado)"),
             ("weld_clr", "CALIBRAR: folga dos pinos-guia dos paineis"), ("mag_clr", "CALIBRAR: folga dos imas"),
             ("pin_s_d", "CALIBRAR: diametro do pino curto impresso (os furos de 3,1 da manivela e do balancim saem apertados)")]:
    param(n, mm(n), c, fav=True)
param("mag_stack", "1", "imas empilhados por furo", unit="")
param("bt_title", "DECK BOX", "texto do fundo, 1a linha", unit="text")
param("bt_sub", "90 CARTAS · ABS", "texto do fundo, 2a linha", unit="text")
param("cav_w", "2*lay_t + 3*cam_clr", "largura da cavidade do mecanismo")
param("W", "in_x + 2*(crad_t + rail_clr + core_t + cav_w + shell_t)", "largura externa")
param("D", "in_y + 2*crad_t + 2*rail_clr + core_t + back_t", "profundidade externa")
param("H", "base_t + crad_gap + crad_f + in_z + roof_t", "altura externa")
param("split", "H - lid_h", "divisao corpo/tampa")
param("Hy", "D/2 - back_t", "eixo da tampa: Y")
param("Hz", "split - h_b", "eixo da tampa: Z")
param("x_co", "in_x/2 + crad_t", "face externa do berco")
param("x_ki", "x_co + rail_clr", "face interna do nucleo")
param("x_ko", "x_ki + core_t", "face externa do nucleo")
param("x_si", "x_ko + cav_w", "face interna do painel")
param("cy", "(core_t - back_t)/2", "centro do interior do berco em Y")
param("z_c0", "base_t + crad_gap", "base do berco")
param("mag_h", "mag_stack*mag_t + 0.1", "profundidade do furo do ima")
param("cav_y0", f"Hy - {f(-E0[0] + ARM_HW + 1.2)}", "frente da cavidade (atras do pilar dos imas)")
param("cav_y1", "D/2 - fl_t", "fundo da cavidade: a dobra de tras do painel fecha a cavidade")
param("cav_z0", f"Hz - {f(-E0[1] + P['tg_h'] - 5 + 1)}", "piso da cavidade")
param("tg_y", ry(E0[0]), "centro da lingua do berco")
param("tg_z0", f"Hz - {f(-E0[1] + P['tg_h'] - 5)}", "base da lingua (fechada)")
param("mag_x", "(x_ko + x_si)/2", "imas: X")
param("mag_y", "(-D/2 + cav_y0)/2", "imas: Y (pilar da frente)")
param("bn_z", "h_b - 2.8", "entalhe traseiro sob a tampa (relativo ao eixo)")
param("scr_yf", "(-D/2 + sh_m + cav_y0)/2", "parafusos da frente: Y (meio do pilar dos imas)")
param("scr_xb", "x_ko - fl_in/2", "parafusos de tras: X (meio da dobra que entra no corpo)")
param("div_h", "card_h - 7", "altura da divisoria")
param("tab_top", "card_h + 1", "topo da aba")

n = {k: v for k, v in p.items()}
n.update(x_co=p["in_x"] / 2 + p["crad_t"])
n["x_ki"] = n["x_co"] + p["rail_clr"]
n["x_ko"] = n["x_ki"] + p["core_t"]
n["x_si"] = n["x_ko"] + p["cav_w"]
n["cy"] = (p["core_t"] - p["back_t"]) / 2
n["z_c0"] = p["base_t"] + p["crad_gap"]
W, D, H, split, Hy, Hz = (n[k] for k in ("W", "D", "H", "split", "Hy", "Hz"))
L1 = (n["x_ko"] + P["cam_clr"], n["x_ko"] + P["cam_clr"] + P["lay_t"])
L2 = (L1[1] + P["cam_clr"], L1[1] + P["cam_clr"] + P["lay_t"])
L1e = ("x_ko + cam_clr", "x_ko + cam_clr + lay_t")
L2e = ("x_ko + 2*cam_clr + lay_t", "x_ko + 2*cam_clr + 2*lay_t")


def xbox(x0, x1, s):
    """(corner_x, length) de uma faixa em X do lado s (+1 direita, -1 esquerda)."""
    return (x0, f"({x1}) - ({x0})") if s > 0 else (f"-({x1})", f"({x1}) - ({x0})")


def box(name, xs, ys, zs, op, body=None, targets=None):
    prm = dict(length=xs[1], width=f"({ys[1]}) - ({ys[0]})", height=f"({zs[1]}) - ({zs[0]})",
               corner=[xs[0], ys[0], zs[0]], operation=op, name=name)
    if body:
        prm["body_name"] = body
    if targets:
        prm["targets"] = targets
    C("solid.box", **prm)


def cyl_x(name, r, x0, x1, s, y, z, op, targets=None, body=None):
    cx, ln = xbox(x0, x1, s)
    prm = dict(radius=r, height=ln, axis="X", base=[cx, y, z], operation=op, name=name)
    if targets:
        prm["targets"] = targets
    if body:
        prm["body_name"] = body
    C("solid.cylinder", **prm)


def poly_x(name, pts, x0, x1, s, op, targets=None, body=None):
    """Poligono no plano YZ (pontos relativos a H), extrudado na faixa X do lado s."""
    off, _ = xbox(x0, x1, s)
    C("sketch.create", plane="YZ", offset=off, name=name + "Sk")
    C("sketch.line", closed=True, points=[[ry(a), rz(b)] for a, b in pts])
    C("sketch.finish")
    prm = dict(sketch=name + "Sk", distance=f"({x1}) - ({x0})", operation=op, name=name)
    if targets:
        prm["targets"] = targets
    if body:
        prm["body_name"] = body
    C("solid.extrude", **prm)


# ---------- CORPO (nucleo) ----------
box("CoreBlock", ("-W/2", "W"), ("-D/2", "D/2"), ("0", "split"), "new", body="Core")
C("solid.fillet", body="Core", edges=[[sx * W / 2, sy * D / 2, split / 2] for sx in (1, -1) for sy in (1, -1)],
  radius="r_out", name="CoreCorners")
C("solid.chamfer", body="Core", edges=[[0, -D / 2, 0]], distance="bed_ch", name="BedChamfer")
box("CradleCavity", ("-x_ki", "2*x_ki"), ("-D/2 + core_t", "Hy"), ("base_t", "split + 1"), "cut", targets=["Core"])
ykf = -D / 2 + P["core_t"]
C("solid.fillet", body="Core", edges=[[sx * n["x_ki"], yy, 50] for sx in (1, -1) for yy in (ykf, Hy)], radius=1.0,
  name="CavityCorners")
for s, tag in ((1, "R"), (-1, "L")):
    # o painel em L ocupa a lateral inteira ate a face de tras e dobra na quina: a quina de tras passa a ser do painel
    box(f"ShellRecess{tag}", xbox("x_si", "W/2 + 1", s), ("-D/2 + sh_m", "D/2 + 1"), ("sh_z0", "split + 1"), "cut", targets=["Core"])
    box(f"BackRecess{tag}", xbox("x_ko - fl_in", "W/2 + 1", s), ("D/2 - fl_t", "D/2 + 1"), ("sh_z0", "split + 1"), "cut", targets=["Core"])
    box(f"MechCavity{tag}", xbox("x_ko", "x_si + 0.01", s), ("cav_y0", "cav_y1 + 0.01"), ("cav_z0", "split + 1"), "cut", targets=["Core"])
    box(f"TongueSlot{tag}", xbox("x_ki - 0.5", "x_ko + 0.5", s), ("tg_y - tg_w/2 - rail_clr", "tg_y + tg_w/2 + rail_clr"),
        ("tg_z0 - rail_clr", "split + 1"), "cut", targets=["Core"])
    # eixo e pivo: furo cego de 1,6 mm no corpo, com folga (o pino gira solto ali; quem o segura e o painel)
    cyl_x(f"AxleHoleCore{tag}", "(pin_d - pin_press)/2", "x_ko - pin_bl", "x_ko + 0.5", s, "Hy", "Hz", "cut", ["Core"])
    cyl_x(f"PivotHoleCore{tag}", "(pin_d - pin_press)/2", "x_ko - pin_bl", "x_ko + 0.5", s, ry(QY), rz(QZ), "cut", ["Core"])
    C("solid.cylinder", diameter="mag_d + mag_clr", height="mag_h + 1", axis="Z", base=[f"{'' if s > 0 else '-'}mag_x", "mag_y", "split - mag_h"],
      operation="cut", targets=["Core"], name=f"MagnetPocketBody{tag}")
    for (py, pz) in (("-D/2 + 8", "20"), ("D/2 - 8", "20")):
        cyl_x(f"PegHole{tag}{len(cmds)}", "1.2 + weld_clr", "x_si - 2", "x_si + 0.5", s, py, pz, "cut", ["Core"])
    # furos-piloto dos parafusos M2 auto-atarraxantes (O1,6): 2 no pilar da frente (ao longo de X) e 2 atras (ao longo de Y),
    # estes so ate 0,4 mm do berco para nao furar a cavidade dele
    for k, pz in enumerate(("split - 14", "16")):
        cyl_x(f"ScrewPilotF{tag}{k}", "0.8", "x_si - 7.5", "x_si + 0.5", s, "scr_yf", pz, "cut", ["Core"])
    for k, pz in enumerate((rz(5.0), rz(-8.0))):
        C("solid.cylinder", radius="0.8", height="back_t - fl_t - 0.4 + 0.5", axis="Y",
          base=[f"{'' if s > 0 else '-'}scr_xb", "Hy + 0.4", pz], operation="cut", targets=["Core"], name=f"ScrewPilotB{tag}{k}")
    # batente da tampa a 111 graus: bloco na camada 1 junto ao eixo, na frente do braco da manivela
    a_stop = CRANK_A0 - 111.0
    u = (math.cos(a_stop * D2R), math.sin(a_stop * D2R))
    nrm = (u[1], -u[0])                                     # lado de onde o braco chega (horario)
    off = CRANK_HW + 0.05                                  # face de batente paralela ao lado do braco da manivela
    edge = lambda r: (math.sqrt(r * r - off ** 2) * u[0] + off * nrm[0], math.sqrt(r * r - off ** 2) * u[1] + off * nrm[1])
    ang = lambda q: math.degrees(math.atan2(q[1], q[0]))
    r_si, r_so = CRANK_HUB_R + 0.6, 9.0                    # face de batente de r 4,6 a 9: fora do cubo, dentro do anel (10,3)
    a7, a5 = ang(edge(r_so)), ang(edge(r_si))
    a_far = a7 - 30                                        # o bloco vai 30 graus alem da face de batente
    stop = [edge(r_si), edge(r_so)] + [(r_so * math.cos(a * D2R), r_so * math.sin(a * D2R)) for a in frange(a7 - 4, a_far, -4)] \
        + [(r_si * math.cos(a * D2R), r_si * math.sin(a * D2R)) for a in frange(a_far, a5 - 2, 4)]
    poly_x(f"LidStop{tag}", stop, "x_ko - 0.2", L1e[1], s, "join", targets=["Core"])
C("solid.cylinder", diameter="foot_d", height="foot_h + 1", axis="Z", base=["-(W/2 - foot_e)", "-(D/2 - foot_e)", -1],
  name="FootRecess", operation="cut", targets=["Core"])
C("solid.pattern.rectangular", features=["FootRecess"], dir1=[1, 0, 0], count1=2, spacing1="W - 2*foot_e",
  dir2=[0, 1, 0], count2=2, spacing2="D - 2*foot_e", name="FootRecesses")
C("sketch.create", plane="XY", offset=-1, flip=True, name="BottomTextSk")
C("sketch.text", text_expression="bt_title", at=["0*W", "bt_y"], height=6, align="center", vertical_align="middle")
C("sketch.text", text_expression="bt_sub", at=["0*W", "-bt_y"], height=3.5, align="center", vertical_align="middle")
C("sketch.finish")
C("solid.extrude", sketch="BottomTextSk", distance="1 + bt_d", direction="negative", name="BottomText", operation="cut", targets=["Core"])

# ---------- PAINEIS EXTERNOS ----------
for s, tag in ((1, "R"), (-1, "L")):
    sx = "" if s > 0 else "-"
    # painel em L: lateral de 3,0 mm ate a face de tras + dobra de 2,0 mm que fecha a cavidade e entra fl_in na traseira
    box(f"ShellPlate{tag}", xbox("x_si", "W/2", s), ("-D/2 + sh_m + weld_clr", "D/2"), ("sh_z0 + weld_clr", "split"), "new", body=f"Shell{tag}")
    box(f"ShellFlange{tag}", xbox("x_ko - fl_in + weld_clr", "x_si + 0.1", s), ("D/2 - fl_t", "D/2"), ("sh_z0 + weld_clr", "split"), "join", targets=[f"Shell{tag}"])
    C("solid.fillet", body=f"Shell{tag}", edges=[[s * W / 2, D / 2, (P["sh_z0"] + split) / 2]], radius="r_out", name=f"ShellCorner{tag}")
    box(f"ShellCap{tag}", xbox("x_ko + weld_clr", "x_si + 0.1", s), ("cav_y0 + weld_clr", "cav_y1 + 0.05"), (f"split - {f(CAP_T)}", "split"), "join", targets=[f"Shell{tag}"])
    box(f"HookSlot{tag}", xbox("x_ko - 0.2", L2e[0], s), (f"Hy - {f(RING_OUT - 0.2)}", "D/2 + 1"), ("split - 3", "split + 1"), "cut", targets=[f"Shell{tag}"])
    # eixo e pivo: furo passante apertado (pin_d - shell_press) + rebaixo para a cabeca na face de fora
    for nome, py, pz in (("Axle", "Hy", "Hz"), ("Pivot", ry(QY), rz(QZ))):
        cyl_x(f"{nome}HoleShell{tag}", "(pin_d - shell_press)/2", "x_si - 0.5", "W/2 + 0.5", s, py, pz, "cut", [f"Shell{tag}"])
        cyl_x(f"{nome}HeadShell{tag}", "head_d/2 + 0.2", "W/2 - head_t - 0.1", "W/2 + 0.5", s, py, pz, "cut", [f"Shell{tag}"])
    for (py, pz) in (("-D/2 + 8", "20"), ("D/2 - 8", "20")):
        cyl_x(f"Peg{tag}{len(cmds)}", "1.2", "x_si - 1.6", "x_si + 0.2", s, py, pz, "join", [f"Shell{tag}"])
    # parafusos M2: furo de passagem O2,3 com escareado de 90 graus (cabeca chata rente)
    for k, pz in enumerate(("split - 14", "16")):
        C("solid.hole", position=[f"{sx}W/2", "scr_yf", pz], direction=[-s, 0, 0], diameter=2.3, type="countersink",
          cs_diameter=4.2, cs_angle=90, depth="shell_t + 0.5", targets=[f"Shell{tag}"], name=f"ScrewHoleF{tag}{k}")
    for k, pz in enumerate((rz(5.0), rz(-8.0))):
        C("solid.hole", position=[f"{sx}scr_xb", "D/2", pz], direction=[0, -1, 0], diameter=2.3, type="countersink",
          cs_diameter=4.2, cs_angle=90, depth="fl_t + 0.5", targets=[f"Shell{tag}"], name=f"ScrewHoleB{tag}{k}")
# linha de sombra (nucleo + paineis) e entalhe traseiro sob a tampa (giro da tampa)
C("sketch.create", plane="XY", offset="split - sg_h", name="ShadowGapSk")
C("sketch.draw.dimensioned", command="sketch.rectangle.center", params={"center": [0, 0], "corner": [W / 2 + 5, D / 2 + 5]},
  dimensions={"width": "W + 10", "height": "D + 10"})
C("sketch.draw.dimensioned", command="sketch.rectangle.center", params={"center": [0, 0], "corner": [W / 2 - 0.5, D / 2 - 0.5]},
  dimensions={"width": "W - 2*sg_d", "height": "D - 2*sg_d"})
C("sketch.fillet", points=[{"a": "l7", "b": "l10"}, {"a": "l7", "b": "l8"}, {"a": "l8", "b": "l9"}, {"a": "l9", "b": "l10"}], radius="r_out - sg_d")
C("sketch.finish")
C("solid.extrude", sketch="ShadowGapSk", distance="sg_h + 1", name="ShadowGap", operation="cut", targets=["Core", "ShellR", "ShellL"])
box("BackNotch", ("-W/2 - 1", "W + 2"), ("Hy", "D/2 + 1"), ("Hz + bn_z", "split + 1"), "cut", targets=["Core", "ShellR", "ShellL"])

# ---------- BERCO ----------
box("CradleBlock", ("-x_co", "2*x_co"), ("cy - in_y/2 - crad_t", "cy + in_y/2 + crad_t"), ("z_c0", "split - 0.5"), "new", body="Cradle")
cyo = (n["cy"] - p["in_y"] / 2 - P["crad_t"], n["cy"] + p["in_y"] / 2 + P["crad_t"])
C("solid.fillet", body="Cradle", edges=[[sx * n["x_co"], yy, 40] for sx in (1, -1) for yy in cyo], radius=1.6, name="CradleCorners")
C("solid.chamfer", body="Cradle", edges=[[0, cyo[0], n["z_c0"]]], distance=0.6, name="CradleLeadIn")
box("CradleInside", ("-in_x/2", "in_x"), ("cy - in_y/2", "cy + in_y/2"), ("z_c0 + crad_f", "split"), "cut", targets=["Cradle"])
ztop = split - 0.5
box("CradleU", ("-u_w/2", "u_w"), ("cy - in_y/2 - crad_t - 1", "cy - in_y/2 + 0.1"), ("split - 0.5 - u_d + u_w/2", "split + 1"), "cut", targets=["Cradle"])
C("solid.cylinder", radius="u_w/2", height="crad_t + 1.1", axis="Y", base=[0, "cy - in_y/2 - crad_t - 1", "split - 0.5 - u_d + u_w/2"],
  operation="cut", targets=["Cradle"], name="CradleUBottom")
tg_z0 = Hz + E0[1] - (P["tg_h"] - 5)
yoke_z = Hz + E0[1]
e_ys = [QY - LEV_R2 * math.cos(phi(t) * D2R) for t in TS]
for s, tag in ((1, "R"), (-1, "L")):
    box(f"Tongue{tag}", xbox("x_co - 0.2", L1e[1], s), ("tg_y - tg_w/2", "tg_y + tg_w/2"), ("tg_z0", "tg_z0 + tg_h"), "join", targets=["Cradle"])
    C("solid.chamfer", body="Cradle", edges=[[s * L1[1], Hy + E0[0], tg_z0]], distance=f(L1[1] - n["x_co"] - 0.05), name=f"TongueChamfer{tag}")
    # garfo com folga morta em cima: fechado, o pino E fica 0,3 + YOKE_SLACK abaixo do teto e o berco descansa no fundo
    box(f"Yoke{tag}", xbox("x_co - 0.5", L1e[1] + " + 0.5", s), (ry(min(e_ys) - SLOT_W / 2), ry(max(e_ys) + SLOT_W / 2)),
        (rz(E0[1] - SLOT_W / 2), rz(E0[1] + SLOT_W / 2 + YOKE_SLACK)), "cut", targets=["Cradle"])

# ---------- TAMPA ----------
box("LidBlock", ("-W/2", "W"), ("-D/2", "D/2"), ("split", "H"), "new", body="Lid")
C("solid.fillet", body="Lid", edges=[[sx * W / 2, sy * D / 2, (split + H) / 2] for sx in (1, -1) for sy in (1, -1)], radius="r_out", name="LidCorners")
C("solid.chamfer", body="Lid", edges=[[0, -D / 2, split]], distance="reveal", name="LidReveal")
C("solid.chamfer", body="Lid", edges=[[0, -D / 2, H]], distance="top_ch", name="LidTopChamfer")
box("LidInside", ("-(W/2 - lid_t)", "W - 2*lid_t"), ("-D/2 + lid_t", "D/2 - lid_t"), ("split - 1", "H - roof_t"), "cut", targets=["Lid"])
for s, tag in ((1, "R"), (-1, "L")):
    box(f"LidMagBlock{tag}", xbox(L1e[0], "W/2 - lid_t + 0.5", s), ("-D/2 + lid_t - 0.5", "cav_y0"), ("split", "H - roof_t + 0.5"), "join", targets=["Lid"])
    # orelha da cauda de andorinha: vai ate Hy - 4 para o encaixe (que chega a Hy - 5,5) ficar inteiro dentro dela;
    # ate Hy - 6 ele furava a face de tras e deixava uma lasca de 0,15 mm solta na borda
    box(f"LidEar{tag}", xbox(L1e[0], "W/2 - lid_t + 0.5", s), ("Hy - 14", "Hy - 4"), ("split", "H - roof_t + 0.5"), "join", targets=["Lid"])
    C("solid.cylinder", diameter="mag_d + mag_clr", height="mag_h + 1", axis="Z", base=[f"{'' if s > 0 else '-'}mag_x", "mag_y", "split - 1"],
      operation="cut", targets=["Lid"], name=f"MagnetPocketLid{tag}")
    hb = P["h_b"]
    mort = [(-9.6 - 0.1, hb - 0.6), (-6.4 + 0.1, hb - 0.6), (-5.6 + 0.1, hb + 2.6 + 0.1), (-10.4 - 0.1, hb + 2.6 + 0.1)]
    poly_x(f"Mortise{tag}", mort, f"{L1e[0]} - 1", f"{L1e[1]} + 0.1", s, "cut", targets=["Lid"])

# ---------- MANIVELAS (camada 1) ----------
tenon = [(-9.6, P["h_b"] - 0.6), (-6.4, P["h_b"] - 0.6), (-5.6, P["h_b"] + 2.6), (-10.4, P["h_b"] + 2.6)]
Cc = crank(0)
ua = (Cc[0] / CRANK_R, Cc[1] / CRANK_R)
na = (-ua[1], ua[0])
arm = [(CRANK_HW * na[0], CRANK_HW * na[1]), (Cc[0] + CRANK_HW * na[0], Cc[1] + CRANK_HW * na[1]),
       (Cc[0] - CRANK_HW * na[0], Cc[1] - CRANK_HW * na[1]), (-CRANK_HW * na[0], -CRANK_HW * na[1])]
for s, tag in ((1, "R"), (-1, "L")):
    poly_x(f"CrankRing{tag}", ring_outline(), L1e[0], L1e[1], s, "new", body=f"Crank{tag}")
    poly_x(f"CrankArm{tag}", arm, L1e[0], L1e[1], s, "join", targets=[f"Crank{tag}"])
    poly_x(f"CrankTenon{tag}", tenon, L1e[0], L1e[1], s, "join", targets=[f"Crank{tag}"])
    cyl_x(f"CrankHub{tag}", f(CRANK_HUB_R), L1e[0], L1e[1], s, "Hy", "Hz", "join", [f"Crank{tag}"])
    cyl_x(f"CrankBoss{tag}", f(CRANK_HW), L1e[0], L1e[1], s, ry(Cc[0]), rz(Cc[1]), "join", [f"Crank{tag}"])
    cyl_x(f"CrankHubHole{tag}", "pin_d/2 + hinge_clr", L1e[0] + " - 0.5", L1e[1] + " + 0.5", s, "Hy", "Hz", "cut", [f"Crank{tag}"])
    cyl_x(f"CrankPinHole{tag}", "(pin_d - pin_press)/2", L1e[0] + " - 0.5", L1e[1] + " + 0.5", s, ry(Cc[0]), rz(Cc[1]), "cut", [f"Crank{tag}"])

# ---------- BALANCINS (camada 2) ----------
slot_world = [(QY + a, QZ + b) for a, b in SLOT]
band = offset_outline(slot_world, SLOT_W / 2 + LEV_WALL)
web = band                                  # a faixa da ranhura ja encosta no cubo do pivo (sem casco convexo)
cut = offset_outline(slot_world, SLOT_W / 2)
# nas curvas fechadas do "J" o contorno deslocado dobra sobre si e a parede afina (ate 0,85 mm): discos de raio
# cheio nesses pontos da linha central repoem a parede de LEV_WALL
R_BAND = SLOT_W / 2 + LEV_WALL


def _dseg(q, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    k = max(0.0, min(1.0, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / (vx * vx + vy * vy)))
    return math.hypot(q[0] - a[0] - k * vx, q[1] - a[1] - k * vy)


FOLDS = sorted({min(range(len(slot_world)), key=lambda i: math.dist(q, slot_world[i])) for q in band
                if min(_dseg(q, slot_world[i], slot_world[i + 1]) for i in range(len(slot_world) - 1)) < R_BAND - 0.1})
groups = []
for i in FOLDS:                                   # indices vizinhos = mesma dobra
    if groups and i - groups[-1][-1] <= 2:
        groups[-1].append(i)
    else:
        groups.append([i])
# um poligono por dobra: casco de discos de raio 3,1 (0,1 a menos que a faixa, para nao ficar tangente ao contorno)
FOLD_POLYS = [hull([q for i in grp for q in circle(slot_world[i], R_BAND - 0.1)]) for grp in groups]
# autoverificacao 2D: balancim (faixa + cubo + braco) e gancho ao longo do giro
lev_pts = band + circle((QY, QZ), LEV_HUB_R) + circle(E0, LEV_HUB_R) + [q for pl in FOLD_POLYS for q in pl]
worst = dict(top=-1e9, back=-1e9, axle=1e9)
for t in TS:
    d = phi(t) - PHI0
    for a, b in lev_pts:
        q = rot_ccw((a - QY, b - QZ), -d)
        y, z = QY + q[0], QZ + q[1]
        worst["top"], worst["back"] = max(worst["top"], z), max(worst["back"], y)
        worst["axle"] = min(worst["axle"], math.hypot(y, z))
print(f"balancim: topo {worst['top']:.2f} (tampa da cavidade em {P['h_b'] - CAP_T:.2f}), tras {worst['back']:.2f} "
      f"(dobra do painel em {P['back_t'] - P['fl_t']:.2f}), menor dist. ao eixo {worst['axle']:.2f} (min {P['pin_d'] / 2 + 0.3:.2f})")
ue = ((E0[0] - QY) / LEV_R2, (E0[1] - QZ) / LEV_R2)
ne = (-ue[1], ue[0])
out_arm = [(QY + ARM_HW * ne[0], QZ + ARM_HW * ne[1]), (E0[0] + ARM_HW * ne[0], E0[1] + ARM_HW * ne[1]),
           (E0[0] - ARM_HW * ne[0], E0[1] - ARM_HW * ne[1]), (QY - ARM_HW * ne[0], QZ - ARM_HW * ne[1])]
# reforco: preenche o vao entre a faixa da ranhura e o braco. Sem ele a ranhura so se liga ao cubo por um pescoco
# de ~1,4 mm, que leva o torque inteiro do balancim (~85 N.mm com o deck cheio: ~80 MPa, o ABS quebra).
tn = ne if ne[1] > 0 else (-ne[0], -ne[1])                               # normal para o lado de cima do braco
top0 = (QY + ARM_HW * tn[0], QZ + ARM_HW * tn[1])
i_left = min(range(len(slot_world)), key=lambda i: slot_world[i][0])     # canto do "J" (ponto mais a frente)
k_left = (slot_world[i_left][0] - top0[0]) * ue[0] + (slot_world[i_left][1] - top0[1]) * ue[1]
gusset = slot_world[:i_left + 1] + [(top0[0] + k_left * ue[0], top0[1] + k_left * ue[1]), top0, (QY, QZ)]
for s, tag in ((1, "R"), (-1, "L")):
    poly_x(f"LeverWeb{tag}", web, L2e[0], L2e[1], s, "new", body=f"Lever{tag}")
    poly_x(f"LeverArm{tag}", out_arm, L2e[0], L2e[1], s, "join", targets=[f"Lever{tag}"])
    poly_x(f"LeverGusset{tag}", gusset, L2e[0], L2e[1], s, "join", targets=[f"Lever{tag}"])
    for k, pl in enumerate(FOLD_POLYS):
        poly_x(f"LeverFill{tag}{k}", pl, L2e[0], L2e[1], s, "join", targets=[f"Lever{tag}"])
    cyl_x(f"LeverEBoss{tag}", f(LEV_HUB_R), L2e[0], L2e[1], s, ry(E0[0]), rz(E0[1]), "join", [f"Lever{tag}"])
    cyl_x(f"LeverHub{tag}", f(LEV_HUB_R), L2e[0], L2e[1], s, ry(QY), rz(QZ), "join", [f"Lever{tag}"])
    poly_x(f"CamSlot{tag}", cut, L2e[0] + " - 0.5", L2e[1] + " + 0.5", s, "cut", targets=[f"Lever{tag}"])
    cyl_x(f"LeverPivotHole{tag}", "pin_d/2 + hinge_clr", L2e[0] + " - 0.5", L2e[1] + " + 0.5", s, ry(QY), rz(QZ), "cut", [f"Lever{tag}"])
    cyl_x(f"LeverEHole{tag}", "(pin_d - pin_press)/2", L2e[0] + " - 0.5", L2e[1] + " + 0.5", s, ry(E0[0]), rz(E0[1]), "cut", [f"Lever{tag}"])

# ---------- PINOS O3 ----------
# eixo e pivo: entram por fora, pelo painel ja parafusado; cabeca no rebaixo, 0,1 abaixo da face; ponta 0,1 antes do fundo
for s, tag in ((1, "R"), (-1, "L")):
    for nome, py, pz in (("Axle", "Hy", "Hz"), ("Pivot", ry(QY), rz(QZ))):
        cyl_x(f"{nome}Pin{tag}", "pin_d/2", "x_ko - pin_bl + 0.1", "W/2 - head_t - 0.1", s, py, pz, "new", body=f"{nome}{tag}")
        cyl_x(f"{nome}PinHead{tag}", "head_d/2", "W/2 - head_t - 0.1", "W/2 - 0.1", s, py, pz, "join", [f"{nome}{tag}"])
    cyl_x(f"CPin{tag}", "pin_d/2", L1e[0], L2e[1] + " - cam_clr", s, ry(Cc[0]), rz(Cc[1]), "new", body=f"Cpin{tag}")
    cyl_x(f"EPin{tag}", "pin_d/2", L1e[0] + " + cam_clr", L2e[1], s, ry(E0[0]), rz(E0[1]), "new", body=f"Epin{tag}")

# ---------- DIVISORIA (deitada ao lado, para imprimir) e BLOCO DE CARTAS (so para checagem) ----------
box("DividerPlate", ("W/2 + 15", "in_x - 2*liner_t - 2*div_gap"), ("-D/2", "-D/2 + div_h"), ("0", "div_t"), "new", body="Divider")
box("DividerTab", ("W/2 + 15 + (in_x - 2*liner_t - 2*div_gap - tab_w)/2", "tab_w"), ("-D/2 + div_h - 1", "-D/2 + tab_top"), ("0", "div_t"), "join", targets=["Divider"])
deck_t = P["n_cards"] * P["card_t"] + P["div_t"]
box("DeckBlock", ("-card_w/2", "card_w"), ("cy + in_y/2 - liner_t - n_cards*card_t - div_t", "cy + in_y/2 - liner_t"),
    ("z_c0 + crad_f + liner_t", "z_c0 + crad_f + liner_t + card_h"), "new", body="Deck")

# ---------- PINOS IMPRESSOS (alternativa aos de aco), deitados ao lado da caixa ----------
# eixo do pino em X: as camadas correm ao longo dele e ele aguenta flexao; chato de 0,2 mm embaixo para assentar na mesa
LONG = "W/2 - head_t - 0.1 - (x_ko - pin_bl + 0.1)"                  # haste do eixo e do pivo
PINS = (("PinLong", "pin_d", LONG, "-D/2 - 10"),                       # eixo da tampa e pivo (com cabeca)
        ("PinShort", "pin_s_d", "2*lay_t", "-D/2 - 18"))               # pino da manivela e da ponta do balancim: mais fino (furos de placa fina)
for nome, dia, comp, py in PINS:
    C("solid.cylinder", radius=f"{dia}/2", height=comp, axis="X", base=["W/2 + 15", py, f"{dia}/2 - 0.2"], operation="new",
      name=nome + "Rod", body_name=nome)
    if nome == "PinLong":   # cabeca: disco cortado reto no mesmo chato da haste (cabeca em D, sem balanco)
        C("solid.cylinder", radius="head_d/2", height="head_t", axis="X", base=[f"W/2 + 15 + ({LONG})", py, "pin_d/2 - 0.2"],
          operation="join", targets=[nome], name=nome + "Head")
    box(nome + "Flat", ("W/2 + 14", f"({comp}) + head_t + 2"), (f"{py} - head_d/2 - 1", f"{py} + head_d/2 + 1"), ("-3", "0"), "cut", targets=[nome])

# ---------- TESTE DE FOLGAS: placa de 3,2 mm (a espessura da manivela e do balancim), furos de 2,8 a 3,5 ----------
C("solid.box", length=52, width=12, height="lay_t", corner=["W/2 + 15", "-D/2 - 40", 0], operation="new", name="FitPlate", body_name="FitTest")
for i in range(8):
    d = 2.8 + 0.1 * i
    C("solid.cylinder", diameter=round(d, 2), height="lay_t + 2", axis="Z", base=[f"W/2 + 15 + {5 + 6 * i}", "-D/2 - 34", -1],
      operation="cut", targets=["FitTest"], name=f"FitHole{i}")
C("solid.chamfer", body="FitTest", edges=[[W / 2 + 15, -D / 2 - 40, P["lay_t"] / 2]], distance=3, name="FitMark")   # quina cortada = lado do 2,8

COLORS = {"Core": "#1f2a44", "ShellR": "#26324f", "ShellL": "#26324f", "Lid": "#d4a017", "Cradle": "#7a2230",
          "Divider": "#a8322d", "CrankR": "#9aa3ad", "CrankL": "#9aa3ad", "LeverR": "#c0c6cc", "LeverL": "#c0c6cc",
          "Deck": "#e8e2d0", "FitTest": "#9aa3ad"}
for b, c in COLORS.items():
    C("appearance.assign", bodies=[b], color=c)
for b in ("AxleR", "AxleL", "PivotR", "PivotL", "CpinR", "CpinL", "EpinR", "EpinL", "PinLong", "PinShort"):
    C("appearance.assign", bodies=[b], color="#5b6168")

(HERE / "C2_elevador_build.json").write_text(json.dumps({"commands": cmds}, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------- verificacao (chamadas MCP) ----------------
# os giros sao translada-gira-volta: o solid.move de algumas versoes do SolidCraft ignora `origin` e gira na origem
MOVE_LID = ["Lid", "CrankR", "CrankL", "CpinR", "CpinL"]
MOVE_LEV = ["LeverR", "LeverL", "EpinR", "EpinL"]
MOVE_UP = ["Cradle", "Deck"]
FIXED = ["Core", "ShellR", "ShellL", "AxleR", "AxleL", "PivotR", "PivotL"]
PRESS = [["AxleR", "Core"], ["AxleR", "ShellR"], ["AxleL", "Core"], ["AxleL", "ShellL"], ["PivotR", "Core"], ["PivotR", "ShellR"],
         ["PivotL", "Core"], ["PivotL", "ShellL"], ["CpinR", "CrankR"], ["CpinL", "CrankL"], ["EpinR", "LeverR"], ["EpinL", "LeverL"],
         ["CrankR", "Lid"], ["CrankL", "Lid"]]
UNDO = {"command": "undo", "params": {}}


def turn(bodies, deg, oy, oz):
    return [{"command": "solid.move", "params": {"bodies": bodies, "translate": [0, f"-({oy})", f"-({oz})"]}},
            {"command": "solid.move", "params": {"bodies": bodies, "axis": [1, 0, 0], "angle": f"{deg:.4f} deg"}},
            {"command": "solid.move", "params": {"bodies": bodies, "translate": [0, oy, oz]}}]


def pose(t_lid, t_mech):
    """Tampa a t_lid graus; balancim e berco na posicao de t_mech (o mecanismo para em TH3)."""
    s = turn(MOVE_LID, -t_lid, "Hy", "Hz") if t_lid else []
    d = phi(min(t_mech, TH3)) - PHI0
    if d:
        s += turn(MOVE_LEV, -d, ry(QY), rz(QZ))
    lift = Lc(min(t_mech, TH3))
    if lift:
        s.append({"command": "solid.move", "params": {"bodies": MOVE_UP, "translate": [0, 0, round(lift, 4)]}})
    return s


def batch(steps, label):
    checks.append({"tool": "batch", "args": {"verbose": False, "rollback": False, "commands": steps}, "label": label})


checks = []
for t in (0, 15, 25, 30, 45, 60, 75, 90, 95, 100, 105, 110):
    mv = pose(t, t)
    batch(mv + [{"command": "inspect.interference", "params": {"bodies": FIXED + MOVE_LID + MOVE_LEV + MOVE_UP, "exclude_pairs": PRESS}}]
          + [UNDO] * len(mv), f"tampa {t} graus, berco +{Lc(t):.2f}")
# pinos dentro das ranhuras: uma sonda 0,15 mais grossa que a folga tem de tocar a peca a cada angulo
probe_r = f"pin_d/2 + cam_clr + 0.15"
for t in (0, 25, 45, 60, 75, 95, 110):
    c = rot_ccw(Cc, -t)                                       # pino C gira com a tampa em volta de H
    e = rot_ccw((E0[0] - QY, E0[1] - QZ), -(phi(t) - PHI0))
    e = (QY + e[0], QZ + e[1])
    mv = pose(t, t)
    cx, ln = xbox(L2e[0], L2e[1], 1)
    batch(mv + [{"command": "solid.cylinder", "params": {"radius": probe_r, "height": ln, "axis": "X", "base": [cx, ry(c[0]), rz(c[1])], "operation": "new", "body_name": "ProbeC"}},
                {"command": "solid.cylinder", "params": {"radius": probe_r, "height": "1", "axis": "X", "base": [L1e[0] + " + 1", ry(e[0]), rz(e[1])], "operation": "new", "body_name": "ProbeE"}},
                {"command": "inspect.interference", "params": {"bodies": ["ProbeC", "LeverR"]}},
                {"command": "inspect.interference", "params": {"bodies": ["ProbeE", "Cradle"]}}]
          + [UNDO] * (len(mv) + 2), f"sondas {t} graus (tem de tocar)")
# batente: a 113 graus a manivela bate no bloco do corpo e o pino C ainda nao chega ao fim da ranhura
mv = pose(113, TH3)
batch(mv + [{"command": "inspect.interference", "params": {"bodies": ["CrankR", "Core"]}},
            {"command": "inspect.interference", "params": {"bodies": ["CpinR", "LeverR"]}}] + [UNDO] * len(mv),
      "batente a 113 graus (1a: tem de tocar; 2a: zero, o fim da ranhura nao e batente)")
# imas: os 4 cabem nos furos sem tocar nada (corpo, tampa, paineis, um no outro)
def mag(name, sx, z0, d="mag_d"):
    return {"command": "solid.cylinder", "params": {"diameter": d, "height": "mag_stack*mag_t", "axis": "Z",
                                                     "base": [f"{sx}mag_x", "mag_y", z0], "operation": "new", "body_name": name}}


SIDES = (("", "R"), ("-", "L"))
four = [mag(f"Mag{w}{t}", sx, z0) for sx, t in SIDES for w, z0 in (("Body", "split - mag_h"), ("Lid", "split + 0.1"))]
batch(four + [{"command": "inspect.interference", "params": {"bodies": [c["params"]["body_name"] for c in four] + ["Core", "Lid", "ShellR", "ShellL"]}}]
      + [UNDO] * 4, "imas: os 4 nos furos, 0,1 abaixo da face (zero)")
# sondas: o furo existe e tem o tamanho certo. Parede: um disco 0,1 mais largo que o furo tem de tocar (nem folgado, nem
# faltando); fundo: o ima 0,05 mais fundo tem de tocar (o ima assenta no fundo e fica 0,1 abaixo da face)
for sx, t in SIDES:
    for part, z_wall, z_floor in (("Core", "split - mag_h + 0.05", "split - mag_h - 0.05"), ("Lid", "split + 0.05", "split + 0.15")):
        batch([mag("ProbeWall", sx, z_wall, "mag_d + mag_clr + 0.1"),
               {"command": "inspect.interference", "params": {"bodies": ["ProbeWall", part]}}, UNDO],
              f"furo do ima {part} {t}: parede (toca)")
        batch([mag("ProbeFloor", sx, z_floor), {"command": "inspect.interference", "params": {"bodies": ["ProbeFloor", part]}}, UNDO],
              f"furo do ima {part} {t}: fundo (toca)")
# fechado: o berco descansa no fundo e o pino E nao encosta no teto do garfo (mecanismo sem carga)
batch([{"command": "solid.move", "params": {"bodies": ["Cradle"], "translate": [0, 0, -0.05]}},
       {"command": "inspect.interference", "params": {"bodies": ["Cradle", "Core"]}},
       UNDO,
       {"command": "solid.move", "params": {"bodies": ["Cradle"], "translate": [0, 0, f"-({YOKE_SLACK} + cam_clr - 0.05)"]}},
       {"command": "inspect.interference", "params": {"bodies": ["Cradle", "EpinR"]}},
       UNDO],
      "fechado (1a: berco 0,05 abaixo toca o fundo; 2a: berco descendo a folga inteira ainda nao toca o pino E)")
(HERE / "C2_verificacao.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    print(f"W={W:.2f} D={D:.2f} H={H:.2f} split={split:.2f} H=({Hy:.2f},{Hz:.2f}) phi0={PHI0:.2f} E0={E0}")
    print(f"{len(cmds)} comandos; ranhura {len(SLOT)} pontos; {len(checks)} checagens")
