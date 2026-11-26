#!/usr/bin/env python3
"""Manual de montagem da caixa D: folha A4 frente e verso, diagramada no DesignCraft.
    python cad/D-asas/manual_d.py [--render [cena,cena...]]
1. imagens (so com --render, ou se faltarem): o Blender (blender_d.py, o mesmo dos GIFs) renderiza as cenas em
   manual/D_img/, com fundo transparente. As pecas montadas vem do .sc (cache do animar_d) e as miniaturas, dos STLs
   de stl/D-asas (ja na posicao de impressao);
2. setas e chamadas: pontos 3D projetados com a mesma camera ortografica de cada cena, entao caem no lugar certo;
3. folha: um roteiro de comandos do DesignCraft (manual/D_manual_roteiro.txt) rodado no designcraft-cli, que grava
   manual/D_manual_montagem.designcraft (editavel), o PDF e as previas images/D/D_manual_frente.png e _verso.png.
"""
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import animar_d as A  # noqa: E402  (traz gerar_d, geo_d, cache de STLs e o Blender)
import geo_d as g  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
IMG = ROOT / "manual" / "D_img"
OUT = ROOT / "manual"
STL = ROOT / "stl" / "D-asas"
DCLI = next((c for c in (os.environ.get("DESIGNCRAFT_CLI", ""), "C:/Program Files/DesignCraft/designcraft-cli.exe")
             if c and os.path.exists(c)), "designcraft-cli")
P, p = g.P, g.p
XP, ZS, Dh, Wh = g.XP, g.ZS, p["Dh"], p["Wh"]
OPEN = P["th_rest"]
YM = (p["y_bi"] + p["y_bo"]) / 2                      # meio da faixa das placas e cremalheiras (|y|)


# ======================= cenas =======================
def cam(yaw, pitch, target, scale, res):
    return A.cam(yaw, pitch, target, scale, res)


def disp(groups, v):
    return {grp: {"t": list(v)} for grp in groups}


PLATES, MAGS, SCREWS, HINGES, CORE = A.PLATES, A.MAGS, A.SCREWS, A.HINGES, A.CORE
ALL = A.ALL
MAG_C = {e["name"]: e["center"] for e in A.EXTRAS if e["name"].startswith("Mag")}
SC = {}                                               # nome -> {cam, visible, poses, arrows, points}


def scene(name, camspec, groups, poses=None, arrows=(), points=None, cut=False):
    vis = [x + "_cut" for x in groups] if cut else A.objs(groups)
    SC[name] = dict(cam=camspec, visible=vis, poses=poses or {}, arrows=list(arrows), points=points or {})


STEP_RES = [1100, 790]
X_LEAF = -(Wh - p["hk_pocket"] + P["hk_t"])           # face de fora da aba da dobradica esquerda


def rot_l(pt, t=OPEN):
    """Ponto da porta esquerda (pose fechada) girado t graus em volta do eixo (como no solid.move do pose)."""
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    dx, dz = pt[0] + XP, pt[2] - ZS
    return (-XP + dx * c - dz * s, pt[1], ZS + dx * s + dz * c)


def rot_r(pt, t=OPEN):
    """O mesmo para a porta direita (espelho da esquerda)."""
    x, y, z = rot_l((-pt[0], pt[1], pt[2]), t)
    return -x, y, z


# 1 imas: as 4 placas abertas (E e D separadas 14 mm), ima acima e para fora do rasgo
k_mag = (4.0, 0, 16.0)
pose1 = {grp: {"t": [A.side_of(grp) * 14, 0, 0]} for grp in PLATES}
arr1 = []
for m in MAGS:
    s = A.side_of(m)
    c = MAG_C[m]
    pose1[m] = {"t": [s * k_mag[0], 0, k_mag[2]]}
    end = (c[0] + s * 14, c[1], c[2] + 2.6)
    arr1.append(((c[0] + s * 4, c[1], c[2] + 13.5), end))
scene("passo1", cam(-0.42, 0.34, [0, 0, 64], 172, STEP_RES), PLATES + MAGS, pose1, arr1,
      {"ima": (MAG_C["MagLF"][0] - k_mag[0], MAG_C["MagLF"][1], MAG_C["MagLF"][2] + k_mag[2]),
       "hastes": (-14 + 2.5, -YM, g.Z_SNAP), "recept": (14 + 2.5, -YM, g.Z_SNAP)})
# 2 cremalheiras sobem 55 mm para o trilho do berco
dz2 = -55.0
scene("passo2", cam(-0.55, 0.30, [0, 0, 8], 205, STEP_RES), ["Tray", "RackF", "RackB"],
      disp(["RackF", "RackB"], (0, 0, dz2)),
      [((13, -YM, -30), (13, -YM, 12)), ((13, YM, -30), (13, YM, 12))],
      {"nervura": (0, p["y_bo"] + 0.3, g.Z_RIDGE + 0.8 + dz2), "trilho": (0, -p["y_co"] - 1, 40)})
# 3 placas deslizam de lado (y) sobre as cremalheiras
dy3 = 48.0
pose3 = disp([x for x in PLATES + MAGS if x.endswith("F")], (0, -dy3, 0))
pose3.update(disp([x for x in PLATES + MAGS if x.endswith("B")], (0, dy3, 0)))
scene("passo3", cam(-0.55, 0.42, [0, 0, 64], 285, STEP_RES), ["Tray", "RackF", "RackB"] + PLATES + MAGS, pose3,
      [((0, -YM - dy3 - 8, 104), (0, -YM - 12, 104)), ((0, YM + dy3 + 8, 104), (0, YM + 12, 104))],
      {"engate": (0, -YM - dy3, g.Z_SNAP)})
# 4 conjunto desce na base
dz4 = 70.0
scene("passo4", cam(-0.55, 0.42, [0, 0, 92], 290, STEP_RES), ["Base"] + CORE, disp(CORE, (0, 0, dz4)),
      [((64, -46, 150), (64, -46, 84))], {"trava": (0, p["y_wi"] + 0.4, 49)})
# 5 portas descem
dz5 = 45.0
scene("passo5", cam(-0.55, 0.42, [0, 0, 86], 255, STEP_RES), ["Base", "DoorL", "DoorR"] + CORE,
      disp(["DoorL", "DoorR"], (0, 0, dz5)),
      [((-20, -Dh - 6, 168), (-20, -Dh - 6, 112)), ((20, -Dh - 6, 168), (20, -Dh - 6, 112))])
# 6 pinos das placas (frente), 18 mm para fora
dy6 = 26.0
pose6 = disp([x for x in SCREWS if x[5] == "F"], (0, -dy6, 0))
pose6.update(disp([x for x in SCREWS if x[5] == "B"], (0, dy6, 0)))
arr6 = []
for sx in (-1, 1):
    for _, sz in A.d.SCREW:
        x = sx * A.d.SCREW[0][0]
        arr6.append(((x, -Dh - dy6 - 6, sz + 4.5), (x, -Dh - 3, sz + 4.5)))
scene("passo6", cam(-0.25, 0.2, [0, -Dh, 81], 150, STEP_RES), ["Base", "DoorL", "DoorR"] + CORE + SCREWS, pose6, arr6)
# 7 dobradicas entram de lado nos rebaixos (vista da esquerda)
dx7 = 34.0
pose7 = disp(["HingeLA", "HingeLB"], (-dx7, 0, 0))
pose7.update(disp(["HingeRA", "HingeRB"], (dx7, 0, 0)))
scene("passo7", cam(0.95, 0.24, [-30, 0, 67], 210, STEP_RES), ["Base", "DoorL", "DoorR"] + CORE + SCREWS + HINGES, pose7,
      [((-XP - dx7 - 14, -38, ZS), (-XP - 8, -38, ZS)), ((-XP - dx7 - 14, 38, ZS), (-XP - 8, 38, ZS))],
      {"aba4": (X_LEAF - dx7, 20, 49), "lisa": (X_LEAF - dx7, -20, 61)})
# 8 teste: aberta, com o baralho; arco da porta e subida do berco
pose8 = A.mech(OPEN)
pose8["Deck"] = {"t": [0, 0, g.lift(OPEN)]}
arc = [(-XP + 50 * math.cos(math.radians(a)), -Dh - 3, ZS + 50 * math.sin(math.radians(a))) for a in range(80, 159, 6)]
scene("passo8", cam(-0.55, 0.42, [0, 0, 78], 240, STEP_RES), ALL + ["Deck"], pose8,
      [tuple(arc), ((36, -30, 97), (36, -30, 131))],
      {"orelha": (XP + 3, -36, ZS + 2), "berco": (P["card_w"] / 2, A.d.yb - A.d.deck_t + 40, p["card_top"] + g.lift(OPEN) - 12)})
# 9 colar: fechada, vista da frente-esquerda (dobradica e pinos da frente)
scene("passo9", cam(0.62, 0.26, [-8, 0, 70.5], 190, STEP_RES), ALL, {},
      [],
      {"abaB": (X_LEAF, -20, 61), "abaA": (X_LEAF, 20, 49), "pino": (-28, -Dh, 91)})
# capa: aberta, 3/4 frente-direita, com o baralho. A dobradica e as orelhas ficam atras da parede da frente da
# porta aberta nesta vista: aparecem nos passos 7 a 9
pose_h = A.mech(OPEN)
pose_h["Deck"] = {"t": [0, 0, g.lift(OPEN)]}
scene("capa", cam(-0.55, 0.40, [0, 0, 64], 208, [1500, 1250]), ALL + ["Deck"], pose_h, [],
      {"porta": rot_l((-18.5, -Dh, 80)), "placa": (-12, -p["y_bo"], 58), "crem": (0, -p["y_bo"], 98),
       "berco": (-25, -p["y_co"], 75), "base": (22, -Dh, 25), "pino": rot_r((A.d.SCREW[1][0], -Dh, A.d.SCREW[1][1])),
       "emenda": rot_l((-1, -p["y_bo"], g.Z_SNAP)), "deck": (10, -30.2, 120)})
# como funciona: corte logo atras do berco, fechada e aberta
for nm, t in (("corte_fechada", 0.0), ("corte_aberta", OPEN)):
    scene(nm, {"eye": [0, -900, 70], "target": [0, 0, 70], "ortho_scale": 165, "res": [760, 760]},
          ["Base", "DoorL", "DoorR", "Tray"], A.mech(t), [], {}, cut=True)
    SC[nm]["visible"] += A.objs(A.BACK)

# miniaturas (STLs na posicao de impressao)
PARTS = [("D_base", "Base", "#1c2331"), ("D_porta_esquerda", "Porta esquerda", "#c9a227"),
         ("D_porta_direita", "Porta direita", "#c9a227"), ("D_placa_esquerda_x2", "Placa-setor E", "#9aa3ad"),
         ("D_placa_direita_x2", "Placa-setor D", "#9aa3ad"), ("D_cremalheira_frente", "Cremalheira da frente", "#c0c6cc"),
         ("D_cremalheira_tras", "Cremalheira de trás", "#c0c6cc"), ("D_berco", "Berço", "#7a2230"),
         ("D_dobradica_x2", "Dobradiça", "#e08a1e"), ("D_pino_placa_x8", "Pino das placas", "#c9a227"),
         ("D_divisoria", "Divisória", "#a8322d"), ("D_teste_deitado", "Testes deitados", "#6c8a9e"),
         ("D_teste_em_pe", "Testes em pé", "#6c8a9e")]


def stl_bbox(path):
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    lo, hi = [1e9] * 3, [-1e9] * 3
    for i in range(n):
        t = struct.unpack_from("<12f", data, 84 + 50 * i)
        for j in range(3):
            v = t[3 + 3 * j:6 + 3 * j]
            lo = [min(a, b) for a, b in zip(lo, v)]
            hi = [max(a, b) for a, b in zip(hi, v)]
    return lo, hi


def fit_cam(lo, hi, res, yaw=-0.62, pitch=0.62, margin=1.12):
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    cs = cam(yaw, pitch, c, 100, res)
    ext_x, ext_y = 0.0, 0.0
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                u, v = project(cs, (x, y, z), unit=True)
                ext_x, ext_y = max(ext_x, abs(u)), max(ext_y, abs(v))
    w, h = res
    return cam(yaw, pitch, c, margin * 2 * max(ext_x, ext_y * w / h), res)


# ======================= projecao (igual a camera do blender_d) =======================
def _norm(v):
    m = math.sqrt(sum(a * a for a in v))
    return [a / m for a in v]


def project(cs, pt, unit=False):
    """Ponto 3D -> pixel (x para a direita, y para baixo) na imagem da camera ortografica `cs`."""
    eye, tgt = cs["eye"], cs["target"]
    d = _norm([b - a for a, b in zip(eye, tgt)])
    up = _norm([(1.0 if i == 2 else 0.0) - d[2] * d[i] for i in range(3)])
    right = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]]
    v = [a - b for a, b in zip(pt, tgt)]
    u_, v_ = sum(a * b for a, b in zip(v, right)), sum(a * b for a, b in zip(v, up))
    if unit:
        return u_, v_
    w, h = cs["res"]
    s = (w if w >= h else h) / cs["ortho_scale"]
    return w / 2 + u_ * s, h / 2 - v_ * s


def render(only=None):
    """Renderiza as cenas (todas, ou so as de `only`); cameras.json sempre sai com todas as cameras do codigo."""
    IMG.mkdir(parents=True, exist_ok=True)
    stl = A.export_stls()
    bodies = {b: [str(stl / f"{b}.stl"), c] for b, c in A.COLORS.items()}
    cams, frames = {}, []
    for nm, sc in SC.items():
        cams[nm] = sc["cam"]
        if not only or nm in only:
            frames.append({"cam": nm, "visible": sc["visible"], "poses": sc["poses"], "out": str(IMG / f"{nm}.png")})
    for f, _, color in PARTS:
        lo, hi = stl_bbox(STL / f"{f}.stl")
        body, nm = "P_" + f, "peca_" + f
        bodies[body] = [str(STL / f"{f}.stl"), color]
        cams[nm] = fit_cam(lo, hi, [520, 400])
        if not only or nm in only:
            frames.append({"cam": nm, "visible": [body], "poses": {}, "out": str(IMG / f"{nm}.png")})
    # no manual os pinos das placas saem laranja (a peca que entra no passo fica em destaque)
    extras = [dict(e, color="#e08a1e") if e["name"].startswith("Pino") else e for e in A.EXTRAS]
    spec = {"bodies": bodies, "extras": extras, "cameras": cams, "cut": {"y": A.CUT_Y, "bodies": A.CUT_BODIES}, "frames": frames}
    sp = A.WORK / "manual.json"
    sp.write_text(json.dumps(spec), encoding="utf-8")
    r = subprocess.run([A.BLENDER, "-b", "--factory-startup", "--python", str(HERE / "blender_d.py"), "--", str(sp)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    if r.returncode or "fim" not in r.stdout:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    (IMG / "cameras.json").write_text(json.dumps(cams, indent=1), encoding="utf-8")
    print(f"{len(frames)} imagens em {IMG}")


# ======================= folha (roteiro do DesignCraft) =======================
W, H = 595.28, 841.89
M = 22.0
C = dict(navy="#1c2331", navy2="#26324f", gold="#c9a227", ink="#1f2733", mute="#5b6472", soft="#eef1f5",
         line="#cfd6df", orange="#e08a1e", glue="#d65c28", ok="#2e8c57", warn="#b5651d", white="#ffffff")
HEAD, BODY = "Bahnschrift", "Segoe UI"
L = []


def cmd(c, **prm):
    L.append(f"{c} {json.dumps(prm, ensure_ascii=False)}")
    return len(L) - 1


def sel(i):
    cmd("selection.set", ids=[f"${i}.id"])


def box(sp, x0, y0, x1, y1, fill=None, stroke=None, weight=0.75, radius=0, shape="rectangle"):
    i = cmd("frame.create", spread=sp, rect=[round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)], shape=shape, content="unassigned")
    sel(i)
    if fill:
        cmd("object.color", color=fill, target="fill")
    else:
        cmd("object.fill", swatch="[None]")
    if stroke:
        cmd("object.color", color=stroke, target="stroke")
        cmd("object.stroke", weight=weight)
    else:
        cmd("object.stroke", swatch="[None]")
    if radius:
        cmd("object.cornerOptions", shape="rounded", size=radius)
    return i


def _bytes_ranges(text):
    """Tira os ** do texto e devolve (texto, [(inicio, fim) em bytes UTF-8 dos trechos em negrito])."""
    out, ranges, pos, bold = [], [], 0, False
    for part in text.split("**"):
        b = len(part.encode("utf-8"))
        if bold and part:
            ranges.append((pos, pos + b))
        out.append(part)
        pos += b
        bold = not bold
    return "".join(out), ranges


def text(sp, x0, y0, x1, y1, txt, font=BODY, style="Regular", size=8.0, color=None, align="left", lead=None,
         track=0, bold_style="Bold", vjust="top", space_after=0.0):
    color = color or C["ink"]
    plain, ranges = _bytes_ranges(txt)
    i = cmd("frame.create", spread=sp, rect=[round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)], content="text", text=plain)
    sel(i)
    attrs = {"fontFamily": font, "fontStyle": style, "size": size, "tracking": track}
    if lead:
        attrs["leading"] = {"kind": "points", "value": lead}
    cmd("type.char", attrs=attrs)
    cmd("object.color", color=color, text=True)
    para = {"align": align}
    if space_after:
        para["spaceAfter"] = space_after
    cmd("type.para", attrs=para)
    cmd("object.textFrameOptions", inset=0, verticalJustification=vjust)
    for a, b in ranges:
        cmd("text.select", story=f"${i}.story", anchor=a, focus=b)
        cmd("type.char", attrs={"fontStyle": bold_style})
    return i


def line(sp, a, b, color, weight=1.0, end="none", start="none", dash=None):
    i = cmd("line.create", spread=sp, a=[round(a[0], 2), round(a[1], 2)], b=[round(b[0], 2), round(b[1], 2)])
    sel(i)
    st = {"weight": weight, "end": end, "start": start, "cap": "round"}
    if dash:
        st["type"] = {"kind": "dashed", "pattern": dash}
    cmd("object.stroke", **st)
    cmd("object.color", color=color, target="stroke")
    return i


def polyline(sp, pts, color, weight=1.0, end="none", start="none"):
    i = cmd("path.create", spread=sp, anchors=[{"p": [round(x, 2), round(y, 2)]} for x, y in pts], closed=False)
    sel(i)
    cmd("object.fill", swatch="[None]")
    cmd("object.stroke", weight=weight, end=end, start=start, cap="round", join="round")
    cmd("object.color", color=color, target="stroke")
    return i


def image(sp, path, x, y, w):
    return cmd("file.place", path=str(path), spread=sp, x=round(x, 2), y=round(y, 2), width=round(w, 2))


def badge(sp, x, y, glue):
    w = 50 if glue else 58
    box(sp, x, y, x + w, y + 14, fill=C["glue"] if glue else C["ok"], radius=7)
    text(sp, x, y, x + w, y + 14, "COLA" if glue else "SEM COLA", HEAD, "Bold", 7.2, C["white"], "center", track=60, vjust="center")
    return w


def numdot(sp, x, y, n, d=22, fill=None, size=12):
    box(sp, x, y, x + d, y + d, fill=fill or C["gold"], shape="ellipse")
    text(sp, x, y, x + d, y + d, str(n), HEAD, "Bold", size, C["white"], "center", vjust="center")


def warn_icon(sp, x, y, s=11):
    i = cmd("frame.create", spread=sp, rect=[round(x, 2), round(y, 2), round(x + s, 2), round(y + s, 2)], shape="polygon",
            sides=3, content="unassigned")
    sel(i)
    cmd("object.color", color=C["warn"], target="fill")
    cmd("object.stroke", swatch="[None]")
    text(sp, x, y + s * 0.18, x + s, y + s, "!", HEAD, "Bold", s * 0.72, C["white"], "center", vjust="center")


class Img:
    """Imagem colocada na pagina: converte pixels da renderizacao em pontos da pagina."""

    def __init__(self, sp, name, x, y, w):
        self.cs = CAMS[name]
        self.x, self.y, self.k = x, y, w / self.cs["res"][0]
        self.h = self.cs["res"][1] * self.k
        image(sp, IMG / f"{name}.png", x, y, w)

    def pt(self, p3):
        u, v = project(self.cs, p3)
        return self.x + u * self.k, self.y + v * self.k


def arrows(sp, im, sc):
    for a in sc["arrows"]:
        pts = [im.pt(q) for q in a]
        polyline(sp, pts, C["orange"], 2.0, end="triangle")


def callout(sp, im, p3, tx, ty, txt, side="left", w=96, size=7.2, color=None):
    """Chamada: bolinha no ponto da peca, linha fina ate o texto em (tx, ty)."""
    px, py = im.pt(p3)
    line(sp, (px, py), (tx, ty), C["ink"], 0.6, start="circleSolid")
    x0 = tx - w - 3 if side == "left" else tx + 3
    text(sp, x0, ty - 5, x0 + w, ty + 18, txt, BODY, "Semibold", size, color or C["ink"], "right" if side == "left" else "left", lead=size + 1.6)


def section(sp, x, y, w, title, sub=None):
    text(sp, x, y, x + w, y + 14, title, HEAD, "Bold", 11.5, C["navy"], track=40)
    line(sp, (x, y + 16.5), (x + w, y + 16.5), C["gold"], 1.2)
    if sub:
        text(sp, x, y + 19.5, x + w, y + 30, sub, BODY, "Regular", 7.2, C["mute"])


def page_front():
    sp = 0
    # cabecalho
    box(sp, 0, 0, W, 80, fill=C["navy"])
    box(sp, 0, 80, W, 83, fill=C["gold"])
    text(sp, M + 2, 15, 380, 26, "DECK BOX YU-GI-OH · VERSÃO D", HEAD, "SemiBold", 8.2, C["gold"], track=180)
    text(sp, M, 26, 400, 58, "Caixa Asas", HEAD, "Bold", 27, C["white"])
    text(sp, M + 1, 58, 420, 72, "Manual de montagem · deck box mecânica para 90 cartas com sleeve duplo",
         BODY, "Regular", 9.2, "#c9d1dc")
    for k, (a, b) in enumerate((("ABS", "camada 0,2"), ("SEM SUPORTE", "em nenhuma peça"), ("~185 g", "com os testes"))):
        x = 318 + k * 62
        text(sp, x, 22, x + 60, 34, a, HEAD, "Bold", 8.8, C["white"], "center")
        text(sp, x, 35, x + 60, 45, b, BODY, "Regular", 6.6, "#aab4c3", "center")
    box(sp, W - M - 58, 12, W - M, 70, fill=C["white"], radius=5)
    cmd("object.qrCode", content="https://github.com/NoobDetonator/deckbox-ygo", rect=[W - M - 54, 16, W - M - 4, 66], color="[Black]")
    text(sp, 318, 55, W - M - 64, 65, "github.com/NoobDetonator/deckbox-ygo", BODY, "Regular", 6.6, "#aab4c3", "right")

    # visao geral: chamadas automaticas, cada uma do lado em que a peca aparece na imagem, sem se sobrepor
    XR = 396                                          # fim da coluna da visao geral
    section(sp, M, 94, XR - M, "VISÃO GERAL", "Aberta a 78°: as portas giram nas laterais e o berço sobe 36 mm com as cartas.")
    P_ = SC["capa"]["points"]
    im = Img(sp, "capa", M + 66, 128, 240)
    # lado fixo de cada chamada (esquerda: porta da esquerda e o que esta na frente dela); em cada lado, na ordem
    # da altura do ponto e empurradas para baixo ate nao se encostarem, entao as linhas nao se cruzam
    labels = [("emenda", "emenda: engate\n+ ímãs 4 × 2", "L"), ("porta", "porta (asa)", "L"), ("berco", "berço", "L"),
              ("placa", "placa-setor\n(10 dentes)", "L"),
              ("deck", "baralho: 90 cartas\ncom sleeve duplo", "R"), ("crem", "cremalheira dupla", "R"),
              ("pino", "pino da placa\n(8 no total)", "R"), ("base", "base", "R")]
    for side, x_text in (("L", M + 64), ("R", XR - 62)):
        y_min = 132.0
        for (qx, qy), lab in sorted([(im.pt(P_[k]), lab) for k, lab, s in labels if s == side], key=lambda q: q[0][1]):
            y = max(qy, y_min)
            y_min = y + 15 + 8.4 * lab.count("\n")
            line(sp, (qx, qy), (x_text, y), C["ink"], 0.55, start="circleSolid")
            if side == "L":
                text(sp, M, y - 4.5, x_text - 2, y + 16, lab, BODY, "Semibold", 7.0, C["ink"], "right", lead=8.4)
            else:
                text(sp, x_text + 2, y - 4.5, XR + 4, y + 16, lab, BODY, "Semibold", 7.0, C["ink"], "left", lead=8.4)

    # como funciona
    x0 = XR + 10
    section(sp, x0, 94, W - M - x0, "COMO FUNCIONA", "Corte logo atrás do berço.")
    iw = (W - M - x0 - 6) / 2
    for k, (nm, cap) in enumerate((("corte_fechada", "fechada"), ("corte_aberta", "aberta (78°)"))):
        xi = x0 + k * (iw + 6)
        box(sp, xi, 124, xi + iw, 124 + iw, fill=C["soft"], radius=6)
        Img(sp, nm, xi + 2, 126, iw - 4)
        text(sp, xi, 124 + iw + 3, xi + iw, 124 + iw + 13, cap, BODY, "Semibold", 7.2, C["mute"], "center")
    how = ("**0–12°:** só a cremalheira anda (folga na cauda de andorinha); as portas se afastam das cartas antes de o "
           "berço subir.\n**12–78°:** a cremalheira leva o berço junto, **+36 mm**. As duas portas engrenam na mesma "
           "cremalheira e abrem juntas.\n**75°:** clique da **trava**: uma lingueta na parede de trás segura o baralho com a "
           "caixa aberta.\n**78°:** a lateral da porta descansa nas **orelhas** da base (batente).\n**Fechada:** o **engate** "
           "da emenda dá clique e os **4 ímãs** puxam uma porta para a outra.")
    text(sp, x0, 124 + iw + 20, W - M, 352, how, BODY, "Regular", 7.0, C["ink"], lead=8.6, space_after=3.4)

    # pecas
    yp = 362
    section(sp, M, yp, W - 2 * M, "PEÇAS PARA IMPRIMIR",
            "Os arquivos de stl/D-asas já saem na posição de impressão (como nas miniaturas). Não gire no fatiador.")
    cards = [("D_base", "Base", "1×", "em pé"), ("D_porta_esquerda", "Porta esquerda", "1×", "teto na mesa"),
             ("D_porta_direita", "Porta direita", "1×", "teto na mesa"), ("D_placa_esquerda_x2", "Placa-setor E", "2×", "deitada · 40 %"),
             ("D_placa_direita_x2", "Placa-setor D", "2×", "deitada · 40 %"), ("D_berco", "Berço", "1×", "em pé"),
             ("D_cremalheira_frente", "Cremalheira frente", "1×", "rasgo p/ baixo"),
             ("D_cremalheira_tras", "Cremalheira trás", "1×", "rasgo p/ baixo"), ("D_dobradica_x2", "Dobradiça", "2×", "sai montada"),
             ("D_pino_placa_x8", "Pino das placas", "8× (+2)", "sobre a cabeça"), ("D_divisoria", "Divisória", "1×", "deitada")]
    cw, ch, gx = (W - 2 * M - 5 * 6) / 6, 88, 6
    for k, (f, nome, q, ori) in enumerate(cards):
        r, c = divmod(k, 6)
        x, y = M + c * (cw + gx), yp + 34 + r * (ch + 6)
        box(sp, x, y, x + cw, y + ch, fill=C["soft"], radius=6)
        Img(sp, f"peca_{f}", x + 4, y + 4, cw - 8)
        numdot(sp, x + 4, y + 4, k + 1, 15, C["navy"], 8)
        text(sp, x + 5, y + 63, x + cw - 4, y + 73, nome, BODY, "Bold", 7.2, C["ink"])
        text(sp, x + 5, y + 74, x + cw - 4, y + 84, f"{q} · {ori}", BODY, "Regular", 6.6, C["mute"])
    x, y = M + 5 * (cw + gx), yp + 34 + 1 * (ch + 6)
    box(sp, x, y, x + cw, y + ch, fill=C["navy"], radius=6)
    text(sp, x + 7, y + 9, x + cw - 6, y + ch - 6,
         "**Configuração**\nABS · camada 0,2\n6 perímetros\n15 % gyroid\nplacas/cremalh.: 40 %\nbrim 5–8 mm\nsem suporte",
         BODY, "Regular", 6.6, C["white"], lead=8.6)

    # compre + testes
    yb = yp + 34 + 2 * (ch + 6) + 6
    section(sp, M, yb, 200, "COMPRE / TENHA À MÃO")
    buy = ["**4 ímãs** de neodímio 4 × 2 mm", "**super bonder** (cianoacrilato) **+ ativador**", "**fita crepe** (teste antes de colar)",
           "**4 pés de silicone** adesivos Ø8 mm", "lixa 220 e estilete (rebarba e brim)", "opcional: feltro ou veludo para o forro"]
    y = yb + 23
    for b in buy:
        box(sp, M + 1, y + 3, M + 6, y + 8, fill=C["gold"], shape="ellipse")
        text(sp, M + 11, y, M + 200, y + 11, b, BODY, "Regular", 7.6, C["ink"])
        y += 13.2
    xt = M + 214
    section(sp, xt, yb, W - M - xt, "ANTES DE TUDO: PEÇAS DE TESTE (~10 g)")
    box(sp, xt, yb + 22, xt + 120, yb + 22 + 92, fill=C["soft"], radius=6)
    Img(sp, "peca_D_teste_deitado", xt + 4, yb + 26, 112)
    box(sp, xt + 124, yb + 22, xt + 172, yb + 22 + 92, fill=C["soft"], radius=6)
    Img(sp, "peca_D_teste_em_pe", xt + 125, yb + 40, 46)
    checks = ["**engrenagem**: girando o setor, a cremalheira corre lisa, com um pouco de folga",
              "**trilho do berço**: desliza no rasgo da cremalheira de teste",
              "**engate**: dá clique e segura; o **ímã** entra justo no rasgo",
              "**mini dobradiça**: gira livre ao sair da mesa",
              "**pino**: entra nos furos; **cortes da lingueta** saem abertos"]
    y = yb + 23
    for c in checks:
        box(sp, xt + 179, y + 1.5, xt + 186, y + 8.5, stroke=C["navy"], weight=0.8, radius=1.2)
        text(sp, xt + 190, y, W - M, y + 20, c, BODY, "Regular", 7.0, C["ink"], lead=8.4)
        y += 18.4
    text(sp, xt + 179, y + 1, W - M, y + 26, "Algo não encaixou? Veja abaixo, gere de novo e reimprima só aquele teste.",
         BODY, "Italic", 6.8, C["mute"], lead=8.2)

    # se algo der errado
    ye = yb + 128
    section(sp, M, ye, W - 2 * M, "SE ALGO DER ERRADO",
            "Mude o parâmetro em cad/D-asas/geo_d.py (P) e rode gerar_d.py, o build e exportar_stl_d.py (comandos no README).")
    fixes = [("Engrenagem dura ou travando", "bl 0,10 → 0,12 (folga de cada flanco)"),
             ("Cremalheira não corre no trilho", "dt_clr 0,25 → 0,30"),
             ("Engate não entra / não segura", "SNAP clr 0,25 → 0,30 / barb 0,6 → 0,7"),
             ("Dobradiça saiu soldada", "hk_pin_clr 0,35 → 0,40 e hk_gap 0,4 → 0,5"),
             ("Ímã solto ou não entra", "MAG: rasgo de 4,3 × 2,15"),
             ("Não fica aberta (o berço desce)", "RIDGE h 0,6 → 0,7 (nervura da trava)")]
    cw2 = (W - 2 * M - 12) / 3
    for k, (prob, fix) in enumerate(fixes):
        r, c = divmod(k, 3)
        x, y = M + c * (cw2 + 6), ye + 34 + r * 27
        box(sp, x, y, x + cw2, y + 23, fill=C["soft"], radius=5)
        box(sp, x, y + 4, x + 3, y + 19, fill=C["gold"])
        text(sp, x + 8, y + 3.5, x + cw2 - 4, y + 12, prob, BODY, "Bold", 7.0, C["ink"])
        text(sp, x + 8, y + 12.5, x + cw2 - 4, y + 21, fix, BODY, "Regular", 6.8, C["mute"])

    # rodape
    line(sp, (M, H - 30), (W - M, H - 30), C["line"], 0.6)
    x = M
    for glue, txt_ in ((True, "use super bonder"), (False, "encaixe a seco")):
        w = badge(sp, x, H - 24, glue)
        text(sp, x + w + 4, H - 21.5, x + w + 80, H - 11, txt_, BODY, "Regular", 7, C["mute"])
        x += w + 84
    warn_icon(sp, x, H - 23)
    text(sp, x + 14, H - 21.5, x + 160, H - 11, "atenção", BODY, "Semibold", 7, C["warn"])
    text(sp, W - M - 200, H - 21.5, W - M, H - 11, "frente · 1/2", BODY, "Regular", 7, C["mute"], "right")


STEPS = [
    ("Ímãs nas placas", True, "passo1",
     "Um ímã 4 × 2 em cada placa, no **rasgo da face da emenda**, rente à face. Antes de colar, encoste a placa E na D "
     "(frente com frente, trás com trás): os ímãs têm de se **atrair**. Marque o lado e cole com 1 gota.",
     "A placa E tem as hastes do engate; a D, o receptáculo."),
    ("Cremalheiras no berço", False, "passo2",
     "O rasgo em cauda de andorinha é aberto só em cima: a cremalheira entra **por baixo**, no trilho do berço, e corre "
     "livre (é a espera de 12°). A de trás leva a **nervura da trava virada para fora**.", None),
    ("Placas nas cremalheiras", False, "passo3",
     "Com tudo embaixo (fechado), deslize cada par de placas **de lado**, no sentido dos dentes, até o engate da emenda "
     "dar clique. O dente de cima de cada setor vai no **1º vão da cremalheira** (contando de cima).", None),
    ("Conjunto na base", False, "passo4",
     "Desça berço, cremalheiras e placas juntos na base, fechados. Ao passar pela parede de trás, a nervura da "
     "cremalheira dá um **clique** no ressalto da trava.", None),
    ("Portas", False, "passo5",
     "Encaixe cada porta **por cima, fechada**. As placas entram nela e encostam no teto e na lateral da porta.",
     "Não abra as portas ainda: sem a dobradiça elas soltam."),
    ("Pinos das placas", False, "passo6",
     "**2 pinos por placa** (8 no total), por fora, pela parede da porta, na frente e atrás. A haste entra 4 mm na placa e "
     "a cabeça fica rente no rebaixo. **Ainda sem cola.**", None),
    ("Dobradiças com fita", False, "passo7",
     "Com a caixa fechada, encaixe cada dobradiça nos rebaixos da lateral: a aba com **4 nós vai na base** (embaixo) e a "
     "**face lisa** (a que ficou na mesa) vai para dentro. Prenda as duas abas com **fita crepe**.", None),
    ("Teste", False, "passo8",
     "Abra e feche devagar: até 12° só a cremalheira anda; depois o berço sobe junto (36 mm). Perto de 75° vem o "
     "**clique da trava** e a 78° as portas descansam nas **orelhas**. Fechada, o engate segura.",
     "Prendeu? Confira o passo 3 (dente de cima no 1º vão)."),
    ("Cole e finalize", True, "passo9",
     "Caixa fechada e travada: tire a fita de uma aba por vez e cole com poucas gotas no rebaixo, **longe do canal dos "
     "nós**, 30 s. Depois, 1 gota em cada pino das placas. Por fim: forro, divisória e pés de silicone.",
     "Cola nos nós trava a dobradiça. Pouca cola: o vapor embranquece o ABS."),
]
# chamadas dos passos: (ponto ou pontos da cena, ponta da linha em fracao da imagem, texto). O canto de cima a
# direita (x > 0,66, y < 0,15) e do selo COLA / SEM COLA.
STEP_LABELS = {
    "passo1": [("ima", 0.03, 0.22, "ímã 4 × 2"), ("hastes", 0.03, 0.88, "hastes (placa E)"),
               ("recept", 0.97, 0.86, "receptáculo\n(placa D)")],
    "passo2": [("nervura", 0.97, 0.80, "nervura da trava\n(para fora)"), ("trilho", 0.03, 0.62, "trilho em cauda\nde andorinha")],
    "passo3": [("engate", 0.03, 0.42, "engate da emenda")],
    "passo4": [("trava", 0.97, 0.48, "clique da\ntrava")],
    "passo7": [("aba4", 0.03, 0.86, "aba com 4 nós:\nna base"), ("lisa", 0.03, 0.30, "face lisa\npara dentro")],
    "passo8": [("orelha", 0.97, 0.88, "batente: orelhas"), ("berco", 0.97, 0.30, "berço e cartas\nsobem 36 mm")],
    "passo9": [(("abaA", "abaB"), 0.03, 0.78, "cola nas\nabas, longe\ndos nós"), ("pino", 0.03, 0.30, "1 gota em\ncada pino")],
}


def page_back():
    sp = 1
    box(sp, 0, 0, W, 50, fill=C["navy"])
    box(sp, 0, 50, W, 53, fill=C["gold"])
    text(sp, M, 15, 360, 38, "Montagem em 9 passos", HEAD, "Bold", 19, C["white"])
    text(sp, 330, 14, W - M, 25, "TESTE TUDO ANTES DE COLAR", HEAD, "Bold", 8.6, C["gold"], "right", track=120)
    text(sp, 300, 27, W - M, 38, "Cola só nos passos 1 e 9 · as setas mostram para onde cada peça vai",
         BODY, "Regular", 7.4, "#c9d1dc", "right")
    gx, gy, top, bot = 8.0, 8.0, 62.0, H - 32
    cw = (W - 2 * M - 2 * gx) / 3
    ch = (bot - top - 2 * gy) / 3
    for k, (title, glue, scn, body, warn) in enumerate(STEPS):
        r, c = divmod(k, 3)
        x, y = M + c * (cw + gx), top + r * (ch + gy)
        box(sp, x, y, x + cw, y + ch, fill=C["soft"], radius=7)
        numdot(sp, x + 7, y + 7, k + 1, 22)
        bw = 50 if glue else 58
        text(sp, x + 34, y + 10, x + cw - 8, y + 26, title, HEAD, "Bold", 10.4, C["navy"])
        badge(sp, x + cw - bw - 7, y + 33, glue)
        iw = cw - 10
        im = Img(sp, scn, x + 5, y + 31, iw)
        sc = SC[scn]
        arrows(sp, im, sc)
        for key, fx, fy, lab in STEP_LABELS.get(scn, []):
            # (fx, fy) e a ponta da linha; o texto fica todo acima dela (fy < 0,5) ou abaixo, entao a linha nao o corta
            tx, ty = x + 5 + fx * iw, y + 31 + fy * im.h
            for k_ in key if isinstance(key, tuple) else (key,):
                line(sp, im.pt(sc["points"][k_]), (tx, ty), C["ink"], 0.55, start="circleSolid")
            y0_, y1_, vj = (ty - 26, ty - 1.5, "bottom") if fy < 0.5 else (ty + 1.5, ty + 26, "top")
            x0_, x1_, al = (tx - 1, tx + 70, "left") if fx < 0.5 else (tx - 70, tx + 1, "right")
            text(sp, x0_, y0_, x1_, y1_, lab, BODY, "Semibold", 6.4, C["ink"], al, lead=7.6, vjust=vj)
        ty = y + 31 + im.h + 4
        text(sp, x + 8, ty, x + cw - 8, y + ch - (22 if warn else 6), body, BODY, "Regular", 7.15, C["ink"], lead=8.9)
        if warn:
            warn_icon(sp, x + 8, y + ch - 20.5)
            text(sp, x + 21, y + ch - 21, x + cw - 8, y + ch - 4, warn, BODY, "Semibold", 6.7, C["warn"], lead=8.0)
    line(sp, (M, H - 26), (W - M, H - 26), C["line"], 0.6)
    text(sp, M, H - 20, 420, H - 9, "Ajustes de folga, verificação e o porquê de cada detalhe: README › Versão D e GUIA_IMPRESSAO_3D.md",
         BODY, "Regular", 7, C["mute"])
    text(sp, W - M - 150, H - 20, W - M, H - 9, "verso · 2/2", BODY, "Regular", 7, C["mute"], "right")


def build():
    global CAMS
    CAMS = json.loads((IMG / "cameras.json").read_text(encoding="utf-8"))
    L.clear()
    cmd("file.new", width=W, height=H, pages=2, facingPages=False, margins=M, title="Caixa D · Asas — manual de montagem")
    page_front()
    page_back()
    script = OUT / "D_manual_roteiro.txt"
    script.write_text("\n".join(L) + "\n", encoding="utf-8")
    pdf, doc = OUT / "D_manual_montagem.pdf", OUT / "D_manual_montagem.designcraft"
    r = subprocess.run([DCLI, "script", str(script), "--save", str(doc), "--export", str(pdf)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    if r.returncode:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    for k, nm in ((0, "frente"), (1, "verso")):
        r = subprocess.run([DCLI, "run", "--in", str(doc), "--page", str(k), "--scale", "2", "--export",
                            str(ROOT / "images" / "D" / f"D_manual_{nm}.png")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        if r.returncode:
            sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    print(f"{len(L)} comandos -> {pdf.name}, {doc.name}, images/D/D_manual_frente.png e _verso.png")


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--render" in sys.argv or not (IMG / "cameras.json").exists():
        render(set(names[0].split(",")) if names else None)
    build()
