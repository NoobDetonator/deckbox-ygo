#!/usr/bin/env python3
"""Caixa D ("asas"): geometria 2D (vista de frente, plano XZ) e checagens de folga.

Mecanismo: as duas portas giram em eixos paralelos a Y, 2,4 mm fora das laterais, na altura da divisao.
Cada porta leva duas placas-setor (frente e tras) com 10 dentes evolventes (m 1,5, z 42); elas engrenam em
duas cremalheiras duplas (frente e tras) que correm numa cauda de andorinha do berco com folga morta:
nos primeiros 12 graus so a cremalheira anda e o berco fica parado (as cartas nao batem no teto da porta);
depois o berco sobe junto. As engrenagens ficam engatadas o tempo todo, entao as portas abrem juntas.
Dobradica: uma peca impressa ja montada (print-in-place, como a da versao B), colada em rebaixos da base e
da porta. Batente: orelhas na base, nas duas pontas da dobradica, onde a lateral da porta encosta a 78 graus.

Folgas (por lado, bico 0,4, camada 0,2, ABS): ver GUIA_IMPRESSAO_3D.md na raiz do repositorio.
Este modulo so tem numeros e poligonos (shapely); gerar_d.py importa daqui e escreve o script do SolidCraft.
"""
import math
import os

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

D2R = math.pi / 180
# solidcraft-cli: a variavel SOLIDCRAFT_CLI ou o primeiro destes que existir (os dois computadores do projeto)
CLI = next((c for c in (os.environ.get("SOLIDCRAFT_CLI", ""),
                        "C:/Users/allan/Desktop/programas/cad/solidcraft-portable/app/solidcraft-0.40.1-windows-x64-portable/solidcraft-cli.exe",
                        "C:/Program Files/SolidCraft/solidcraft-cli.exe") if c and os.path.exists(c)), "solidcraft-cli")

# ---------------- parametros ----------------
P = dict(card_w=62.5, card_h=91.0, card_t=0.68, n_cards=90, liner_t=1.0, play_x=1.5, play_y=2.0, div_t=1.6,
         shrink=0.006, crad_t=1.6, crad_f=1.6, base_t=2.0, wall_t=2.0, dwall_t=2.3, roof_t=2.0, head=2.5,
         rail_clr=0.3, lay_t=5.0, z_s=55.0,
         # dobradica print-in-place (geometria da B, que ja funcionou na impressora): o eixo fica hk_r acima da face
         # colada (os nos encostam na mesa); a face colada fica num rebaixo de hk_r - e_h, entao o eixo sai e_h da lateral
         e_h=2.4, hk_r=3.0, hk_t=1.2, hk_w=10.0, hk_len=64.0, hk_n=7, hk_pin=2.6,
         hk_pin_clr=0.35, hk_gap=0.4, hk_clr=0.4, hk_pocket_clr=0.15,
         m=1.5, z_g=42, alpha=20.0, bl=0.1, n_teeth=10,
         dwell=12.0, th_stop=78.0, th_rest=77.5,
         ef=0.2, ef_h=0.3,              # alivio do pe de elefante: borda da face da mesa 0,2 para dentro, 0,3 de altura
         dt_clr=0.25, dt_depth_clr=0.3, dt_mouth=0.4)   # cauda de andorinha: folga por lado, no fundo, chanfro da boca
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
p["hk_pocket"] = P["hk_r"] - P["e_h"]                   # profundidade do rebaixo da aba (0,6)
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


def frange(a, b, step):
    n = max(2, int(round(abs(b - a) / step)) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ---------------- engrenagem ----------------
inv = lambda a: math.tan(a) - a


def tooth(center_deg, r_from, s_pitch):
    """Dente evolvente centrado no angulo center_deg (em volta do eixo esquerdo), de r_from ate Ra.
    s_pitch: espessura no circulo primitivo. Pontos relativos ao eixo."""
    a0 = P["alpha"] * D2R
    half0 = s_pitch / (2 * R) + inv(a0)
    r0 = max(r_from, p["Rb"])
    rs = [r0 + (p["Ra"] - r0) * i / 10 for i in range(11)]
    up, lo = [], []
    for r in rs:
        psi = half0 - inv(math.acos(min(1.0, p["Rb"] / r)))
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


def relief(geom):
    """Contorno da face que vai na mesa: 0,2 para dentro (a primeira camada sai mais larga, o 'pe de elefante')."""
    return geom.buffer(-P["ef"], join_style="mitre")


# ---------------- placa-setor (porta esquerda, pose fechada, mundo XZ) ----------------
X_SEAM = -0.15                     # face da emenda (folga de 0,3 entre as portas)
Z_NOTCH = 64.0                     # acima disso a placa chega na emenda (ima e engate)
X_NOTCH = -(p["x_rt"] + 1.5)       # abaixo de Z_NOTCH a placa para 1,5 antes da ponta dos dentes da cremalheira
X_CLIP = -(p["x_ki"] - 0.15)       # abaixo da divisao a placa fica 0,15 longe da lateral da base
Z_MAG, Z_SNAP = 74.0, 88.0
MAG = dict(h=4.3, d=2.15)          # rasgo do ima 4 x 2 na face da emenda, passante na espessura (sem ponte)
# engate: duas hastes afinando de 1,4 (raiz) a 1,0 (ponta), farpa de 0,6, folga de 0,25 no receptaculo; a haste cede
# 0,27 (deformacao 0,5 %, o ABS aguenta muito mais); vao de 0,6 em volta da haste dentro da propria placa
SNAP = dict(root=-6.3, t0=1.4, t1=1.0, gap=1.6, barb=0.6, b0=1.9, top=0.3, back=35.0, lead=30.0,
            win=0.6, clr=0.25, lip=1.85)
SNAP["b1"] = SNAP["b0"] + SNAP["barb"] / math.tan(SNAP["back"] * D2R) + SNAP["top"] + SNAP["barb"] / math.tan(SNAP["lead"] * D2R)
SNAP["tip"] = SNAP["b1"] + 0.3


def sector_body():
    s_pitch = p["pitch"] / 2 - 2 * P["bl"]
    teeth = [Polygon(tooth(a, p["Rf"] - 0.05, s_pitch)) for a in TOOTH_ANG]
    arc = [(p["Rf"] * math.cos(a * D2R), p["Rf"] * math.sin(a * D2R)) for a in frange(-84.0, 25.0, 1.0)]
    g = at_pivot(unary_union([Polygon([(0, 0)] + arc)] + teeth), -1)
    g = g.difference(box(-100, -100, X_CLIP, ZS))                       # lateral da base
    g = g.difference(box(-100, ZS - 1e-6, -p["x_ki"], 200))             # acima da divisao: lateral da porta (a ponta da
    #                                                                     fatia, no eixo, ficaria 4 mm para fora)
    region_a = box(-p["x_ki"], ZS, X_SEAM, p["roof_in"]).difference(box(X_NOTCH, ZS - 1, 1, Z_NOTCH))
    return unary_union([g, region_a])


def _prong_outer(u):
    s = SNAP
    return s["gap"] / 2 + s["t0"] + (s["t1"] - s["t0"]) * (u - s["root"]) / (s["tip"] - s["root"])


def snap_prongs():
    """Hastes do engate (placa esquerda), relativas a (0, Z_SNAP): (corte na placa, hastes para fora da emenda)."""
    s = SNAP
    us = frange(s["root"], s["tip"], 0.5)
    cut, prongs = [], []
    for sg in (1, -1):
        # canal de 0,6 por fora da haste, com fundo redondo na raiz
        outer = [(u, sg * _prong_outer(u)) for u in us if u <= 0.5]
        ch = Polygon(outer + [(u, sg * (_prong_outer(u) + s["win"])) for u in reversed([q[0] for q in outer])])
        cut += [ch, disc((s["root"] + s["win"] / 2, sg * (_prong_outer(s["root"]) + s["win"] / 2)), s["win"] / 2, 24)]
        body = Polygon([(s["root"] - 0.5, sg * s["gap"] / 2), (s["tip"], sg * s["gap"] / 2)]
                       + [(u, sg * _prong_outer(u)) for u in reversed(us)] + [(s["root"] - 0.5, sg * _prong_outer(s["root"]))])
        ho = _prong_outer(s["b0"])
        barb = Polygon([(s["b0"], sg * ho), (s["b0"] + s["barb"] / math.tan(s["back"] * D2R), sg * (ho + s["barb"])),
                        (s["b1"] - s["barb"] / math.tan(s["lead"] * D2R), sg * (ho + s["barb"])), (s["b1"], sg * _prong_outer(s["b1"]))])
        prongs += [body, barb]
    # vao entre as hastes, com fundo em meia-lua na raiz (alivia a tensao)
    cut.append(box(s["root"] + s["gap"] / 2, -s["gap"] / 2, 0.5, s["gap"] / 2))
    cut.append(disc((s["root"] + s["gap"] / 2, 0), s["gap"] / 2, 32))
    mv = lambda g: affinity.translate(g, 0, Z_SNAP)
    return mv(unary_union(cut)), mv(unary_union(prongs).difference(box(-50, -s["gap"] / 2, 50, s["gap"] / 2)))


def snap_slot():
    """Receptaculo na placa direita (mundo, x > 0): boca chanfrada, labio e alojamento das farpas (folga 0,25)."""
    s = SNAP
    x0, xl, xe = -X_SEAM, s["lip"], s["tip"] + 0.5
    h_in = max(_prong_outer(u) for u in frange(x0, xl, 0.1)) + s["clr"]          # meia altura no labio
    h_re = _prong_outer(s["b0"]) + s["barb"] + s["clr"]                           # meia altura no alojamento
    pts = [(x0 - 1, h_in + 0.8), (x0 + 0.5, h_in), (xl, h_in), (xl + 0.3, h_re), (xe, h_re),
           (xe, -h_re), (xl + 0.3, -h_re), (xl, -h_in), (x0 + 0.5, -h_in), (x0 - 1, -h_in - 0.8)]
    return affinity.translate(Polygon(pts), 0, Z_SNAP)


def magnet_slot(side):
    face = -side * X_SEAM                          # face da emenda da placa (x = -0,15 na esquerda, +0,15 na direita)
    a, b = face + side * MAG["d"], face - side * 0.5
    return box(min(a, b), Z_MAG - MAG["h"] / 2, max(a, b), Z_MAG + MAG["h"] / 2)


def plate(side):
    g = sector_body()
    if side < 0:
        cut, prongs = snap_prongs()
        g = unary_union([g.difference(cut), prongs])
    else:
        g = affinity.scale(g, -1, 1, origin=(0, 0)).difference(snap_slot())
    return g.difference(magnet_slot(side))


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
RAIL = dict(neck=2.5, tip=3.2, h=2.0)   # meias larguras e altura do rabo de andorinha
Z_GE = Z_RB + P["rail_clr"] - travel(P["dwell"])   # fim do rasgo na cremalheira: a 12 graus encosta no chanfro do trilho
Z_BUMP = 49.0                            # ressalto da lingueta na parede de tras (mundo)
RIDGE = dict(h=0.6, lo=0.6, up=0.6 / math.tan(30 * D2R))   # nervura na cremalheira de tras: flanco de baixo 45, de cima 30
Z_RIDGE = Z_BUMP + 0.5 + 0.15 - travel(P["th_rest"])        # base da nervura (cremalheira, pose fechada)
SLIT = 0.9                               # cortes a 45 graus da lingueta (0,64 na perpendicular: nao solda na impressao)


def rail_rect():
    return box(-RAIL["tip"], Z_RB, RAIL["tip"], Z_RT)


def groove_profile():
    """Rasgo da cauda de andorinha na cremalheira, em (x, d), d = profundidade a partir da face do lado do berco
    (que vai na mesa): o trilho + dt_clr por lado, + dt_depth_clr no fundo (teto em ponte) e boca chanfrada."""
    c, rl = P["dt_clr"], RAIL
    w = lambda d: rl["neck"] + c + (rl["tip"] - rl["neck"]) * d / rl["h"]          # meia largura no fundo d
    dm = P["dt_mouth"] / (1 + (rl["tip"] - rl["neck"]) / rl["h"])                  # chanfro de 45 graus encontra a rampa
    dd = rl["h"] + P["dt_depth_clr"]
    right = [(w(0) + P["dt_mouth"], -0.05), (w(dm), dm), (w(dd), dd)]
    return [(-x, d) for x, d in reversed(right)] + right


# ---------------- dobradica (relativo ao eixo esquerdo; x para fora e negativo) ----------------
def teardrop(r, up):
    sg = 1 if up else -1
    tip = (0, sg * r * math.sqrt(2))
    tan = [(r * math.cos(a * D2R), sg * r * math.sin(a * D2R)) for a in (45, 135)]
    return unary_union([disc((0, 0), r, 32), Polygon([tan[0], tip, tan[1]])])


HK_SEG = (P["hk_len"] - (P["hk_n"] - 1) * P["hk_gap"]) / P["hk_n"]   # comprimento de cada no
HK_Y = [-P["hk_len"] / 2 + i * (HK_SEG + P["hk_gap"]) for i in range(P["hk_n"])]   # comeco (y) de cada no
EAR_Y = (P["hk_len"] / 2 + 0.9, p["Dh"] - 4.2)                     # orelhas do batente: das pontas da dobradica ate a quina


def door_wall_section():
    """Lateral da porta perto do eixo (fora da dobradica, onde ficam as orelhas): parede de 2 com o chanfro de 0,5."""
    e, w = P["e_h"], P["wall_t"]
    return Polygon([(e + 0.5, 0), (e + w, 0), (e + w, 30), (e, 30), (e, 0.5)])


def base_ear():
    """Orelha do batente (relativa ao eixo): 45 graus por baixo; o topo e o lugar da lateral da porta girada ate
    th_stop, entao ela encosta ali a th_stop. Sai da face da lateral da base (x = e_h)."""
    e = P["e_h"]
    raw = Polygon([(e + 0.1, -10.5), (e + 0.1, 5.0), (-5.0, 5.0), (-5.0, -10.5 + e + 5.1)])   # 2 mm alem dos nos
    swept = unary_union([affinity.rotate(door_wall_section(), t, origin=(0, 0)) for t in frange(0, P["th_stop"], 0.25)])
    ear = raw.difference(swept)
    return max(ear.geoms, key=lambda q: q.area) if ear.geom_type == "MultiPolygon" else ear


# ---------------- checagens 2D ----------------
def door_section():
    """Corte da porta esquerda sobre as cartas: teto e lateral (o que pode bater nas cartas)."""
    return unary_union([box(-p["Wh"], p["roof_in"], X_SEAM, p["H"]), box(-p["Wh"], ZS, -p["x_ki"], p["H"])])


def report():
    out = []
    W, D, H = 2 * p["Wh"], 2 * p["Dh"], p["H"]
    out.append(f"caixa {W:.2f} x {D:.2f} x {H:.2f} (+{P['e_h'] + P['hk_r']:.1f} da dobradica de cada lado); "
               f"eixos x=+-{XP:.3f} z={ZS}; R {R} pitch {p['pitch']:.3f}; cremalheira: primitiva +-{p['x_pl']:.3f}, "
               f"ponta +-{p['x_rt']:.3f}, nucleo +-{p['x_rr']:.3f}; rebaixo da aba {p['hk_pocket']:.2f}")
    out.append(f"curso da cremalheira a {P['th_stop']} graus: {travel(P['th_stop']):.2f}; berco: {lift(P['th_stop']):.2f}")
    rk, z_top = rack()
    plates = {s: plate(s) for s in (-1, 1)}
    worst, wd = 0.0, 1e9
    for i in range(0, int(P["th_stop"] * 4) + 1):
        t = i / 4
        rr = affinity.translate(rk, 0, travel(t))
        for s in (-1, 1):
            pl = rot_door(plates[s], t, s)
            worst = max(worst, pl.intersection(rr).area)
            if i % 4 == 0:
                wd = min(wd, pl.distance(rr))
    out.append(f"placa x cremalheira de 0 a {P['th_stop']}: pior sobreposicao {worst:.4f} mm2, menor folga {wd:.3f}")
    # a face da mesa (contorno 0,2 para dentro) tambem engrena: so muda a folga
    out.append(f"placa x lateral da base: "
               f"{max(rot_door(plates[-1], t, -1).intersection(box(-p['Wh'], 0, -p['x_ki'], ZS)).area for t in frange(0, P['th_stop'], 1)):.4f}; "
               f"placa fora da porta (x < -{p['x_ki']:.3f}): {plates[-1].intersection(box(-100, -100, -p['x_ki'], 200)).area:.4f}")
    card = box(-P["card_w"] / 2, p["card_z0"], P["card_w"] / 2, p["card_top"])
    dsec, md, tmin = door_section(), 1e9, None
    for i in range(0, int(P["th_stop"] * 2) + 1):
        t = i / 2
        c = affinity.translate(card, 0, lift(t))
        d = rot_door(dsec, t, -1)
        v = d.distance(c) if not d.intersects(c) else -d.intersection(c).area
        if v < md:
            md, tmin = v, t
    out.append(f"porta x cartas (espera {P['dwell']} graus): menor folga {md:.2f} a {tmin} graus")
    ov = [(t, rot_door(plates[-1], t, -1).intersection(rot_door(plates[1], t, 1)).area) for t in frange(0, 20, 0.5)]
    out.append("placa E x placa D (area por angulo; so o engate): " + ", ".join(f"{t:g}:{a:.2f}" for t, a in ov if a > 1e-6))
    rail = rail_rect()
    wr = max(rot_door(plates[s], t, s).intersection(affinity.translate(rail, 0, lift(t))).area
             for s in (-1, 1) for t in frange(0, P["th_stop"], 0.5))
    out.append(f"trilho do berco x placas: {wr:.4f}")
    ear, dw = base_ear(), door_wall_section()
    a_lo = affinity.rotate(dw, P["th_stop"] - 0.5, origin=(0, 0)).intersection(ear).area
    a_hi = affinity.rotate(dw, P["th_stop"] + 0.5, origin=(0, 0)).intersection(ear).area
    out.append(f"batente (orelha): a {P['th_stop'] - 0.5} graus {a_lo:.4f} mm2, a {P['th_stop'] + 0.5} graus {a_hi:.4f} mm2; "
               f"orelha {[round(v, 2) for v in ear.bounds]} (relativo ao eixo)")
    out.append(f"trava: ressalto z {Z_BUMP}, nervura na cremalheira z {Z_RIDGE:.2f}..{Z_RIDGE + RIDGE['lo'] + RIDGE['up']:.2f}; "
               f"rasgo da cauda comeca em z {Z_GE:.2f}")
    # engate fechado: as farpas ficam no alojamento sem tocar; a haste cede `ced` para passar o labio
    ced = _prong_outer(SNAP["b0"]) + SNAP["barb"] - (max(_prong_outer(u) for u in frange(-X_SEAM, SNAP["lip"], 0.1)) + SNAP["clr"])
    eps = 1.5 * SNAP["t0"] * ced / (SNAP["tip"] - SNAP["root"]) ** 2
    out.append(f"engate: a haste cede {ced:.2f} mm (deformacao {100 * eps:.2f} %); vao em volta {SNAP['win']}, entre hastes {SNAP['gap']}")
    return out


if __name__ == "__main__":
    print("\n".join(report()))
