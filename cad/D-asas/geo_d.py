#!/usr/bin/env python3
"""Caixa D ("asas"): geometria 2D (vista de frente, plano XZ) e checagens de folga.

Mecanismo: as duas portas giram em eixos paralelos a Y, 1,5 mm fora das laterais, na altura da divisao.
Cada porta leva duas placas-setor (frente e tras) com 10 dentes evolventes (m 1,5, z 42); elas engrenam em
duas cremalheiras duplas (frente e tras) que correm numa cauda de andorinha do berco com 8,25 mm de folga
morta: nos primeiros 15 graus so a cremalheira anda e o berco fica parado (as cartas nao batem no teto da
porta); depois o berco sobe junto, 34,6 mm ate 78 graus. As engrenagens ficam engatadas o tempo todo, entao
as portas abrem juntas.
Este modulo so tem numeros e poligonos (shapely); gerar_d.py importa daqui e escreve o script do SolidCraft.
"""
import math

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

D2R = math.pi / 180

# ---------------- parametros ----------------
P = dict(card_w=62.5, card_h=91.0, card_t=0.68, n_cards=90, liner_t=1.0, play_x=1.5, play_y=2.0, div_t=1.6,
         shrink=0.006, crad_t=1.6, crad_f=1.6, base_t=2.0, wall_t=2.0, dwall_t=2.3, roof_t=2.0, head=2.5,
         rail_clr=0.3, lay_t=5.0, z_s=55.0,
         e_h=1.5, r_k=3.5, k_clr=0.3, pin_press=1.9, pin_free=2.2,
         m=1.5, z_g=42, alpha=20.0, bl=0.075, n_teeth=10,
         dwell=12.0, th_stop=78.0, th_rest=77.5)
p = dict(P)
k = 1 + P["shrink"]
p["in_x"] = k * (P["card_w"] + 2 * P["liner_t"] + P["play_x"])
p["in_y"] = k * (P["n_cards"] * P["card_t"] + P["div_t"] + 2 * P["liner_t"] + P["play_y"])
p["x_co"] = p["in_x"] / 2 + P["crad_t"]                 # face externa do berco
p["x_ki"] = p["x_co"] + P["rail_clr"]                   # face interna da base
p["Wh"] = p["x_ki"] + P["wall_t"]                       # meia largura externa
p["y_co"] = p["in_y"] / 2 + P["crad_t"]                 # face frontal/traseira do berco
p["y_bi"] = p["y_co"] + P["rail_clr"]                   # placa: face do lado do berco
p["y_bo"] = p["y_bi"] + P["lay_t"]                      # placa: face do lado da parede (encosta na porta)
p["y_wi"] = p["y_bo"] + P["rail_clr"]                   # face interna da parede da base
p["Dh"] = p["y_wi"] + P["wall_t"]                       # meia profundidade externa
p["card_z0"] = P["base_t"] + P["crad_f"] + P["liner_t"]
p["card_top"] = p["card_z0"] + P["card_h"]
p["roof_in"] = p["card_top"] + P["head"]
p["H"] = p["roof_in"] + P["roof_t"]
p["xp"] = p["Wh"] + P["e_h"]                            # eixo das portas: x = +-xp, z = z_s
p["R"] = P["m"] * P["z_g"] / 2
p["Rb"] = p["R"] * math.cos(P["alpha"] * D2R)
p["Ra"] = p["R"] + P["m"]
p["Rf"] = p["R"] - 1.25 * P["m"]
p["pitch"] = math.pi * P["m"]
p["tau"] = 360.0 / P["z_g"]
p["x_pl"] = p["xp"] - p["R"]                            # linha primitiva da cremalheira (x = +-)
p["x_rt"] = p["x_pl"] + P["m"]                          # ponta dos dentes da cremalheira (para fora, rumo ao setor)
p["x_rr"] = p["x_pl"] - 1.25 * P["m"]                   # raiz (meia largura do nucleo)
ZS, XP, R = P["z_s"], p["xp"], p["R"]


def travel(t):
    """Subida da cremalheira (mm) com a porta a t graus."""
    return R * t * D2R


def lift(t):
    """Subida do berco: parado nos primeiros `dwell` graus (folga morta na cauda de andorinha)."""
    return max(0.0, travel(t) - travel(P["dwell"]))


# ---------------- engrenagem ----------------
inv = lambda a: math.tan(a) - a


def tooth(center_deg, r_from, s_pitch):
    """Dente evolvente centrado no angulo center_deg (em volta do eixo esquerdo), de r_from ate Ra.
    s_pitch: espessura no circulo primitivo. Pontos relativos ao eixo."""
    a0 = P["alpha"] * D2R
    half0 = s_pitch / (2 * R) + inv(a0)
    rs = [max(r_from, p["Rb"])]
    n = 10
    rs = [rs[0] + (p["Ra"] - rs[0]) * i / n for i in range(n + 1)]
    up, lo = [], []
    for r in rs:
        ar = math.acos(min(1.0, p["Rb"] / r))
        psi = half0 - inv(ar)
        up.append((r, center_deg * D2R + psi))
        lo.append((r, center_deg * D2R - psi))
    pts = [(r_from, lo[0][1])] + lo + up[::-1] + [(r_from, up[0][1])]
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


TOOTH_ANG = [-j * p["tau"] for j in range(P["n_teeth"])]        # dentes do setor (angulo inicial, porta fechada)
RACK_Z = [ZS + R * (p["tau"] / 2) * D2R - j * p["pitch"] for j in range(P["n_teeth"] + 1)]  # dentes da cremalheira


def at_pivot(geom, side):
    """Leva uma geometria relativa ao eixo para o mundo (lado -1 esquerdo, +1 direito: espelha em x)."""
    g = affinity.translate(geom, -XP, ZS)
    return affinity.scale(g, -1, 1, origin=(0, 0)) if side > 0 else g


def rot_door(geom, t, side):
    """Gira uma geometria da porta `side` de t graus de abertura (esquerda: anti-horario visto de frente)."""
    return affinity.rotate(geom, t if side < 0 else -t, origin=(side * XP, ZS))


def disc(c, r, n=64):
    return Point(c).buffer(r, quad_segs=n // 4)


# ---------------- placa-setor (porta esquerda, pose fechada, mundo XZ) ----------------
X_SEAM = -0.15                     # face da emenda (folga de 0,3 entre as portas)
Z_NOTCH = 64.0                     # acima disso a placa chega na emenda (bloco dos imas e do engate)
X_NOTCH = -10.0                    # abaixo de Z_NOTCH a placa para em x = -10 (topo da cremalheira)
X_CLIP = -(p["x_ki"] - 0.15)       # abaixo da divisao a placa fica 0,15 longe da lateral da base
Z_MAG, Z_SNAP = 74.0, 88.0
SNAP = dict(root=-6.3, tip=4.0, t=1.2, gap=1.4, barb=0.25, b0=1.9, b1=3.6, lip=1.85, clr=0.1)


def sector_body():
    s_pitch = p["pitch"] / 2 - 2 * P["bl"]
    teeth = [Polygon(tooth(a, p["Rf"] - 0.05, s_pitch)) for a in TOOTH_ANG]
    a0, a1 = -84.0, 25.0
    arc = [(p["Rf"] * math.cos(a * D2R), p["Rf"] * math.sin(a * D2R)) for a in frange(a0, a1, 1.0)]
    pie = Polygon([(0, 0)] + arc)
    g = at_pivot(unary_union([pie] + teeth), -1)
    g = g.difference(box(-100, -100, X_CLIP, ZS))                       # lateral da base
    region_a = box(-p["x_ki"], ZS, X_SEAM, p["roof_in"]).difference(box(X_NOTCH, ZS - 1, 1, Z_NOTCH))
    g = unary_union([g, region_a])
    g = g.difference(disc((-XP, ZS), P["r_k"] + 0.5))                    # dobradica
    return g


def frange(a, b, step):
    n = max(2, int(round(abs(b - a) / step)) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def snap_prongs():
    s = SNAP
    win = box(s["root"], Z_SNAP - s["t"] - s["gap"] / 2 - 0.4, 0.5, Z_SNAP + s["t"] + s["gap"] / 2 + 0.4)
    prongs = []
    for sg in (1, -1):
        zi, zo = Z_SNAP + sg * s["gap"] / 2, Z_SNAP + sg * (s["gap"] / 2 + s["t"])
        body = box(s["root"] - 0.01, min(zi, zo), s["tip"], max(zi, zo))
        # farpa: rampa de entrada 25 graus (ponta), face de tras 40 graus
        zb = zo + sg * s["barb"]
        x_in = s["b1"] - s["barb"] / math.tan(25 * D2R)
        x_out = s["b0"] + s["barb"] / math.tan(40 * D2R)
        barb = Polygon([(s["b0"], zo), (x_out, zb), (x_in, zb), (s["b1"], zo)])
        prongs += [body, barb]
    return win, unary_union(prongs)


def snap_slot():
    """Receptaculo na placa direita (mundo, x > 0): boca com chanfro, labio e alojamento das farpas."""
    s = SNAP
    h_in = s["gap"] / 2 + s["t"] + s["clr"]                 # meia altura no labio
    h_re = h_in + s["barb"] + s["clr"]                      # meia altura no alojamento
    x0, xl, xe = -X_SEAM, s["lip"], s["tip"] + 0.5
    pts = [(x0 - 1, Z_SNAP + h_in + 0.6), (x0 + 0.6, Z_SNAP + h_in), (xl, Z_SNAP + h_in), (xl + 0.2, Z_SNAP + h_re),
           (xe, Z_SNAP + h_re), (xe, Z_SNAP - h_re), (xl + 0.2, Z_SNAP - h_re), (xl, Z_SNAP - h_in),
           (x0 + 0.6, Z_SNAP - h_in), (x0 - 1, Z_SNAP - h_in - 0.6)]
    return Polygon(pts)


def plate(side):
    g = sector_body()
    win, prongs = snap_prongs()
    if side < 0:
        return unary_union([g.difference(win), prongs])
    g = affinity.scale(g, -1, 1, origin=(0, 0))
    return g.difference(snap_slot())


# ---------------- cremalheira (pose fechada) ----------------
Z_RACK_BOT = 4.0


def rack():
    half_p = p["pitch"] / 4 - P["bl"]
    t = math.tan(P["alpha"] * D2R)
    xr, xt, xl = p["x_rr"], p["x_rt"], p["x_pl"]
    hr = half_p + (xl - xr) * t                 # meia largura na raiz (mais larga)
    ht = half_p - (xt - xl) * t                 # meia largura na ponta
    z_top = RACK_Z[0] + hr + 0.6
    core = box(-xr, Z_RACK_BOT, xr, z_top)
    teeth = []
    for zc in RACK_Z:
        for sg in (1, -1):
            teeth.append(Polygon([(sg * (xr - 0.01), zc - hr), (sg * xt, zc - ht), (sg * xt, zc + ht), (sg * (xr - 0.01), zc + hr)]))
    return unary_union([core] + teeth), z_top


# ---------------- trilho do berco (cauda de andorinha) e trava de abertura ----------------
Z_RB, Z_RT = 17.0, 52.0                 # trilho no berco (pose fechada); fundo chanfrado a 45 graus
RAIL = dict(neck=2.5, tip=3.2, h=2.0)   # meias larguras e altura do rabo de andorinha (o rasgo tem +0,2 por lado)
Z_GE = Z_RB + P["rail_clr"] - travel(P["dwell"])   # fim do rasgo na cremalheira: a 12 graus encosta no chanfro do trilho
Z_BUMP = 49.0                            # ressalto da lingueta na parede de tras (mundo)
RIDGE = dict(h=0.6, lo=0.6, up=0.6 / math.tan(30 * D2R))   # nervura na cremalheira de tras: flanco de baixo 45, de cima 30
Z_RIDGE = Z_BUMP + 0.5 + 0.15 - travel(P["th_rest"])        # base da nervura (cremalheira, pose fechada)


def rail_rect():
    return box(-RAIL["tip"], Z_RB, RAIL["tip"], Z_RT)


# ---------------- dobradica (relativo ao eixo esquerdo; x para fora e negativo) ----------------
def door_gusset():
    """Mao-francesa da porta (acima do eixo, por fora): tangente ao no a 135 graus, desce a 45 ate a lateral."""
    rk, e = P["r_k"], P["e_h"]
    T = (rk * math.cos(135 * D2R), rk * math.sin(135 * D2R))
    E = (e, T[1] + (e - T[0]))
    return Polygon([T, E, (e + 0.1, E[1] + 0.1), (e + 0.1, 0), (0, 0)]).convex_hull


def door_hinge_profile():
    return unary_union([disc((0, 0), P["r_k"]), door_gusset(), box(P["e_h"], 0, P["e_h"] + P["wall_t"], 30)])


def base_lug():
    """Barra de baixo da dobradica (toda a extensao): 45 graus por baixo; o topo e o lugar da porta girada ate
    th_stop, entao a mao-francesa da porta encosta nela a th_stop (batente)."""
    e = P["e_h"]
    raw = Polygon([(e + 0.1, -8.0), (e + 0.1, 2.5), (-6.0, 2.5), (-6.0, -0.4)])
    prof = door_hinge_profile()
    swept = unary_union([affinity.rotate(prof, t, origin=(0, 0)) for t in frange(0, P["th_stop"], 0.25)])
    lug = raw.difference(swept)
    return max(lug.geoms, key=lambda g: g.area) if lug.geom_type == "MultiPolygon" else lug


def teardrop(r, up):
    sg = 1 if up else -1
    tip = (0, sg * r * math.sqrt(2))
    tan = [(r * math.cos(a * D2R), sg * r * math.sin(a * D2R)) for a in (45, 135)]
    return unary_union([disc((0, 0), r, 32), Polygon([tan[0], tip, tan[1]])])


# ---------------- checagens 2D ----------------
def door_section():
    """Corte da porta esquerda sobre as cartas: teto e lateral (o que pode bater nas cartas)."""
    return unary_union([box(-p["Wh"], p["roof_in"], X_SEAM, p["H"]), box(-p["Wh"], ZS, -p["x_ki"], p["H"])])


def report():
    out = []
    W, D, H = 2 * p["Wh"], 2 * p["Dh"], p["H"]
    out.append(f"caixa {W:.2f} x {D:.2f} x {H:.2f} (+{P['r_k'] + P['e_h'] - 0:.1f} da dobradica de cada lado); "
               f"eixos x=+-{XP:.3f} z={ZS}; R {R} pitch {p['pitch']:.3f}; cremalheira: primitiva +-{p['x_pl']:.3f}, "
               f"ponta +-{p['x_rt']:.3f}, nucleo +-{p['x_rr']:.3f}")
    out.append(f"curso da cremalheira a {P['th_stop']} graus: {travel(P['th_stop']):.2f}; berco: {lift(P['th_stop']):.2f}")
    rk, z_top = rack()
    plates = {s: plate(s) for s in (-1, 1)}
    worst, wd = 0.0, 1e9
    for i in range(0, int(P["th_stop"] * 4) + 1):
        t = i / 4
        rr = affinity.translate(rk, 0, travel(t))
        for s in (-1, 1):
            pl = rot_door(plates[s], t, s)
            a = pl.intersection(rr).area
            worst = max(worst, a)
            if i % 4 == 0:
                wd = min(wd, pl.distance(rr))
    out.append(f"placa x cremalheira de 0 a {P['th_stop']}: pior sobreposicao {worst:.4f} mm2, menor folga {wd:.3f}")
    # placas x lateral da base (abaixo da divisao) e x berco/cartas nao se cruzam em y; so a lateral importa
    wall = box(-p["Wh"], 0, -p["x_ki"], ZS)
    w2 = max(rot_door(plates[-1], t, -1).intersection(wall).area for t in frange(0, P["th_stop"], 1))
    out.append(f"placa x lateral da base: {w2:.4f}")
    # portas x cartas
    card = box(-P["card_w"] / 2, p["card_z0"], P["card_w"] / 2, p["card_top"])
    dsec = door_section()
    for dw in (P["dwell"],):
        md = 1e9
        tmin = None
        for i in range(0, int(P["th_stop"] * 2) + 1):
            t = i / 2
            c = affinity.translate(card, 0, max(0.0, travel(t) - travel(dw)))
            d = rot_door(dsec, t, -1).distance(c) if not rot_door(dsec, t, -1).intersects(c) else -rot_door(dsec, t, -1).intersection(c).area
            if d < md:
                md, tmin = d, t
        out.append(f"porta x cartas (espera {dw} graus): menor folga {md:.2f} a {tmin} graus")
    # placa esquerda x direita: so o engate pode se tocar, e so perto de fechada
    ov = [(t, rot_door(plates[-1], t, -1).intersection(rot_door(plates[1], t, 1)).area) for t in frange(0, 20, 0.5)]
    out.append("placa E x placa D (area por angulo): " + ", ".join(f"{t:g}:{a:.2f}" for t, a in ov if a > 1e-6))
    # trilho do berco (na faixa das placas) x placas
    rail = rail_rect()
    wr = max(rot_door(plates[s], t, s).intersection(affinity.translate(rail, 0, lift(t))).area
             for s in (-1, 1) for t in frange(0, P["th_stop"], 0.5))
    out.append(f"trilho do berco x placas: {wr:.4f}")
    # batente na dobradica: a th_stop - 0,5 livre, a th_stop + 0,5 encosta
    lug, prof = base_lug(), door_hinge_profile()
    a_lo = affinity.rotate(prof, P["th_stop"] - 0.5, origin=(0, 0)).intersection(lug).area
    a_hi = affinity.rotate(prof, P["th_stop"] + 0.5, origin=(0, 0)).intersection(lug).area
    out.append(f"batente: a {P['th_stop'] - 0.5} graus {a_lo:.4f} mm2, a {P['th_stop'] + 0.5} graus {a_hi:.4f} mm2; "
               f"barra de baixo {[round(v, 2) for v in lug.bounds]}")
    out.append(f"trava: ressalto z {Z_BUMP}, nervura na cremalheira z {Z_RIDGE:.2f}..{Z_RIDGE + RIDGE['lo'] + RIDGE['up']:.2f}; "
               f"rasgo da cauda comeca em z {Z_GE:.2f}")
    return out


if __name__ == "__main__":
    print("\n".join(report()))
