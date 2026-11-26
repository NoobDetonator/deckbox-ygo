"""Versao C (elevador) no FreeCAD: gera todas as pecas como solidos Part a partir da mesma cinematica da V2.

Rodar dentro do FreeCAD (console Python ou MCP):
    exec(open(r"<repo>/cad/C-elevador-freecad/gerar_c_freecad.py", encoding="utf-8").read())
A cinematica (lei de elevacao, ranhura de came, pontos do gancho e do batente) vem de cad/C-elevador-v2/gerar_c2.py:
mudou um parametro la, rode este de novo. Salva C_elevador.FCStd nesta pasta.
"""
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = Path(r"E:/Projetos/03 - 3D/ygo box/deckbox-ygo/cad/C-elevador-freecad")
sys.path.insert(0, str(HERE.parent / "C-elevador-v2"))
sys.dont_write_bytecode = True
import gerar_c2 as g  # noqa: E402  (regrava os JSON da V2 com o mesmo conteudo)

P, n = g.P, g.n
W, D, H, split, Hy, Hz = g.W, g.D, g.H, g.split, g.Hy, g.Hz
x_co, x_ki, x_ko, x_si = n["x_co"], n["x_ki"], n["x_ko"], n["x_si"]
in_x, in_y, cy, z_c0 = n["in_x"], n["in_y"], n["cy"], n["z_c0"]
L1, L2 = g.L1, g.L2
E0, Cc, QY, QZ = g.E0, g.Cc, g.QY, g.QZ
pin_d, cam_clr = P["pin_d"], P["cam_clr"]
cav_y0 = Hy - (-E0[0] + g.ARM_HW + 1.2)
cav_y1 = D / 2 - P["fl_t"]
cav_z0 = Hz - (-E0[1] + P["tg_h"] - 5 + 1)
tg_y, tg_z0 = Hy + E0[0], Hz + E0[1] - (P["tg_h"] - 5)
mag_h = P["mag_stack"] * P["mag_t"] + 0.1
mag_x, mag_y = (x_ko + x_si) / 2, (-D / 2 + cav_y0) / 2
scr_yf, scr_xb = (-D / 2 + P["sh_m"] + cav_y0) / 2, x_ko - P["fl_in"] / 2
SIDES = (1, -1)


# ---------------- helpers ----------------
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def xr(x0, x1, s):
    return (x0, x1) if s > 0 else (-x1, -x0)


def sbox(s, x0, x1, y0, y1, z0, z1):
    a, b = xr(x0, x1, s)
    return box(a, b, y0, y1, z0, z1)


def cylx(s, r, x0, x1, y, z):
    a, b = xr(x0, x1, s)
    return Part.makeCylinder(r, b - a, V(a, y, z), V(1, 0, 0))


def cylz(d, h, x, y, z0):
    return Part.makeCylinder(d / 2, h, V(x, y, z0))


def polyx(s, pts, x0, x1):
    """Poligono no plano YZ (pontos relativos ao eixo H) extrudado na faixa X do lado s."""
    a, b = xr(x0, x1, s)
    vs = [V(a, Hy + p, Hz + q) for p, q in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]])).extrude(V(b - a, 0, 0))


def stadium_x(s, pts, r, x0, x1):
    """Faixa de raio r em volta de uma curva (pontos relativos a H): contorno 2D exato, sem dobras."""
    # offset 2D de uma POLILINHA com cantos em arco (join 0): sai valido. Na BSpline o offset dobra nas curvas
    # fechadas do "J" e sai invalido; uniao de discos (2D ou 3D) trava ou derruba o OCC
    a, b = xr(x0, x1, s)
    outline = Part.makePolygon([V(a, Hy + p, Hz + q) for p, q in pts]).makeOffset2D(r, 0, False, False)
    return Part.Face(outline).extrude(V(b - a, 0, 0))


def extrude_union(faces, dx):
    f2d = faces[0].multiFuse(faces[1:]).removeSplitter()
    sol = [fc.extrude(V(dx, 0, 0)) for fc in f2d.Faces]
    return sol[0] if len(sol) == 1 else sol[0].multiFuse(sol[1:]).removeSplitter()


def fan_x(s, pts, x0, x1):
    """Poligono possivelmente auto-intersectante como uniao 2D de triangulos em leque a partir do ultimo ponto."""
    a, b = xr(x0, x1, s)
    c = pts[-1]
    tris = [Part.Face(Part.makePolygon([V(a, Hy + u, Hz + w) for u, w in (c, p, q, c)])) for p, q in zip(pts[:-1], pts[1:-1])
            if abs((p[0] - c[0]) * (q[1] - c[1]) - (p[1] - c[1]) * (q[0] - c[0])) > 1e-6]
    return extrude_union(tris, b - a)


def _vert_edges(shape, xys, tol=1e-3):
    out = []
    for e in shape.Edges:
        if e.Curve.TypeId != "Part::GeomLine":
            continue
        p0, p1 = e.Vertexes[0].Point, e.Vertexes[-1].Point
        if abs(p0.x - p1.x) < 1e-6 and abs(p0.y - p1.y) < 1e-6 and any(abs(p0.x - x) < tol and abs(p0.y - y) < tol for x, y in xys):
            out.append(e)
    return out


def fillet_z(shape, r, xys):
    return shape.makeFillet(r, _vert_edges(shape, xys))


def chamfer_x(shape, dist, y, z, xmin=-1e9, xmax=1e9):
    es = [e for e in shape.Edges if e.Curve.TypeId == "Part::GeomLine"
          and all(abs(v.Y - y) < 1e-3 and abs(v.Z - z) < 1e-3 for v in e.Vertexes)
          and xmin <= e.CenterOfMass.x <= xmax]
    return shape.makeChamfer(dist, es)


def cut(shape, tools):
    return shape.cut(Part.makeCompound(tools)).removeSplitter() if tools else shape


def fuse(shape, tools):
    return shape.fuse(tools).removeSplitter() if tools else shape


def csk_hole(origin, direction, depth, d=2.3, d_cs=4.2):
    """Furo de passagem com escareado de 90 graus; origin na face, direction para dentro."""
    o, u = V(*origin), V(*direction)
    h_cs = (d_cs - d) / 2
    return Part.makeCompound([Part.makeCylinder(d / 2, depth + 0.5, o - u * 0.5, u),
                              Part.makeCone(d_cs / 2, d / 2, h_cs, o, u),
                              Part.makeCylinder(d_cs / 2, 1.0, o - u * 1.0, u)])


def rounded_rect(w, d, r, z0, z1):
    return fillet_z(box(-w / 2, w / 2, -d / 2, d / 2, z0, z1), r, [(sx * w / 2, sy * d / 2) for sx in (1, -1) for sy in (1, -1)])


# ---------------- CORPO ----------------
core = box(-W / 2, W / 2, -D / 2, D / 2, 0, split)
core = fillet_z(core, P["r_out"], [(sx * W / 2, sy * D / 2) for sx in (1, -1) for sy in (1, -1)])
core = chamfer_x(core, P["bed_ch"], -D / 2, 0)
core = cut(core, [box(-x_ki, x_ki, -D / 2 + P["core_t"], Hy, P["base_t"], split + 1)])
core = fillet_z(core, 1.0, [(sx * x_ki, yy) for sx in (1, -1) for yy in (-D / 2 + P["core_t"], Hy)])
cuts, joins = [], []
for s in SIDES:
    cuts += [sbox(s, x_si, W / 2 + 1, -D / 2 + P["sh_m"], D / 2 + 1, P["sh_z0"], split + 1),
             sbox(s, x_ko - P["fl_in"], W / 2 + 1, D / 2 - P["fl_t"], D / 2 + 1, P["sh_z0"], split + 1),
             sbox(s, x_ko, x_si + 0.01, cav_y0, cav_y1 + 0.01, cav_z0, split + 1),
             sbox(s, x_ki - 0.5, x_ko + 0.5, tg_y - P["tg_w"] / 2 - P["rail_clr"], tg_y + P["tg_w"] / 2 + P["rail_clr"],
                  tg_z0 - P["rail_clr"], split + 1),
             cylx(s, (pin_d - P["pin_press"]) / 2, x_ko - P["pin_bl"], x_ko + 0.5, Hy, Hz),
             cylx(s, (pin_d - P["pin_press"]) / 2, x_ko - P["pin_bl"], x_ko + 0.5, Hy + QY, Hz + QZ),
             cylz(P["mag_d"] + P["mag_clr"], mag_h + 1, s * mag_x, mag_y, split - mag_h)]
    cuts += [cylx(s, 1.2 + P["weld_clr"], x_si - 2, x_si + 0.5, y, 20) for y in (-D / 2 + 8, D / 2 - 8)]
    cuts += [cylx(s, 0.8, x_si - 7.5, x_si + 0.5, scr_yf, z) for z in (split - 14, 16)]
    cuts += [Part.makeCylinder(0.8, P["back_t"] - P["fl_t"] - 0.4 + 0.5, V(s * scr_xb, Hy + 0.4, Hz + dz), V(0, 1, 0)) for dz in (5.0, -8.0)]
    joins.append(polyx(s, g.stop, x_ko - 0.2, L1[1]))
cuts += [cylz(P["foot_d"], P["foot_h"] + 1, sx * (W / 2 - P["foot_e"]), sy * (D / 2 - P["foot_e"]), -1) for sx in (1, -1) for sy in (1, -1)]
core = fuse(cut(core, cuts), joins)
# texto do fundo, espelhado para ler por baixo, baixo-relevo de bt_d
FONT = "C:/Windows/Fonts/arialbd.ttf"
for txt, size, y in (("DECK BOX", 6.0, P["bt_y"]), ("90 CARTAS \u00b7 ABS", 3.5, -P["bt_y"])):
    faces = [Part.Face(Part.Wire(w)) for ch in Part.makeWireString(txt, FONT, size) for w in ch]
    letters = Part.makeCompound([f.extrude(V(0, 0, 1 + P["bt_d"])) for f in faces])
    # contornos internos (furo do "A", "B"...) viram solidos sobrepostos: a uniao XOR por paridade sai com cut/fuse em pares
    solids = sorted(letters.Solids, key=lambda s: -s.Volume)
    glyph = None
    for s in solids:
        if glyph is None:
            glyph = s
        elif glyph.common(s).Volume > 1e-6 and abs(glyph.common(s).Volume - s.Volume) < 1e-6:
            glyph = glyph.cut(s)    # contido em outro: e um furo de letra
        else:
            glyph = glyph.fuse(s)
    bb = glyph.BoundBox
    glyph.translate(V(-(bb.XMin + bb.XMax) / 2, y - (bb.YMin + bb.YMax) / 2, -1))
    glyph = glyph.mirror(V(0, 0, 0), V(0, 1, 0))   # tombando a caixa para a frente (giro em X) o texto le direito
    core = core.cut(glyph)

# ---------------- PAINEIS ----------------
wc = P["weld_clr"]
shells = {}
for s in SIDES:
    sh = fuse(sbox(s, x_si, W / 2, -D / 2 + P["sh_m"] + wc, D / 2, P["sh_z0"] + wc, split),
              [sbox(s, x_ko - P["fl_in"] + wc, x_si + 0.1, D / 2 - P["fl_t"], D / 2, P["sh_z0"] + wc, split)])
    sh = fillet_z(sh, P["r_out"], [(s * W / 2, D / 2)])
    sh = fuse(sh, [sbox(s, x_ko + wc, x_si + 0.1, cav_y0 + wc, cav_y1 + 0.05, split - g.CAP_T, split)])
    sc = [sbox(s, x_ko - 0.2, L2[0], Hy - (g.RING_OUT - 0.2), D / 2 + 1, split - 3, split + 1)]
    for y, z in ((Hy, Hz), (Hy + QY, Hz + QZ)):
        sc += [cylx(s, (pin_d - P["shell_press"]) / 2, x_si - 0.5, W / 2 + 0.5, y, z),
               cylx(s, P["head_d"] / 2 + 0.2, W / 2 - P["head_t"] - 0.1, W / 2 + 0.5, y, z)]
    sc += [csk_hole((s * W / 2, scr_yf, z), (-s, 0, 0), P["shell_t"]) for z in (split - 14, 16)]
    sc += [csk_hole((s * scr_xb, D / 2, Hz + dz), (0, -1, 0), P["fl_t"]) for dz in (5.0, -8.0)]
    sh = fuse(cut(sh, sc), [cylx(s, 1.2, x_si - 1.6, x_si + 0.2, y, 20) for y in (-D / 2 + 8, D / 2 - 8)])
    shells[s] = sh
# linha de sombra e entalhe traseiro (giro da tampa)
gap = box(-W / 2 - 5, W / 2 + 5, -D / 2 - 5, D / 2 + 5, split - P["sg_h"], split + 1).cut(
    rounded_rect(W - 2 * P["sg_d"], D - 2 * P["sg_d"], P["r_out"] - P["sg_d"], split - P["sg_h"] - 1, split + 2))
notch = box(-W / 2 - 1, W / 2 + 1, Hy, D / 2 + 1, Hz + P["h_b"] - 2.8, split + 1)
core = cut(core, [gap, notch])
shells = {s: cut(sh, [gap, notch]) for s, sh in shells.items()}

# ---------------- BERCO ----------------
cyo0, cyo1 = cy - in_y / 2 - P["crad_t"], cy + in_y / 2 + P["crad_t"]
cradle = box(-x_co, x_co, cyo0, cyo1, z_c0, split - 0.5)
cradle = fillet_z(cradle, 1.6, [(sx * x_co, yy) for sx in (1, -1) for yy in (cyo0, cyo1)])
cradle = chamfer_x(cradle, 0.6, cyo0, z_c0)
u_z = split - 0.5 - P["u_d"] + P["u_w"] / 2
cradle = cut(cradle, [box(-in_x / 2, in_x / 2, cy - in_y / 2, cy + in_y / 2, z_c0 + P["crad_f"], split),
                      box(-P["u_w"] / 2, P["u_w"] / 2, cyo0 - 1, cy - in_y / 2 + 0.1, u_z, split + 1),
                      Part.makeCylinder(P["u_w"] / 2, P["crad_t"] + 1.1, V(0, cyo0 - 1, u_z), V(0, 1, 0))])
tongues, yokes = [], []
for s in SIDES:
    tg = sbox(s, x_co - 0.2, L1[1], tg_y - P["tg_w"] / 2, tg_y + P["tg_w"] / 2, tg_z0, tg_z0 + P["tg_h"])
    es = [e for e in tg.Edges if e.Curve.TypeId == "Part::GeomLine"
          and all(abs(v.X - s * L1[1]) < 1e-3 and abs(v.Z - tg_z0) < 1e-3 for v in e.Vertexes)]
    tongues.append(tg.makeChamfer(L1[1] - x_co - 0.05, es))
    yokes.append(sbox(s, x_co - 0.5, L1[1] + 0.5, Hy + min(g.e_ys) - g.SLOT_W / 2, Hy + max(g.e_ys) + g.SLOT_W / 2,
                      Hz + E0[1] - g.SLOT_W / 2, Hz + E0[1] + g.SLOT_W / 2 + g.YOKE_SLACK))
cradle = cut(fuse(cradle, tongues), yokes)

# ---------------- TAMPA ----------------
lid = box(-W / 2, W / 2, -D / 2, D / 2, split, H)
lid = fillet_z(lid, P["r_out"], [(sx * W / 2, sy * D / 2) for sx in (1, -1) for sy in (1, -1)])
lid = chamfer_x(lid, P["reveal"], -D / 2, split)
lid = chamfer_x(lid, P["top_ch"], -D / 2, H)
lid = cut(lid, [box(-(W / 2 - P["lid_t"]), W / 2 - P["lid_t"], -D / 2 + P["lid_t"], D / 2 - P["lid_t"], split - 1, H - P["roof_t"])])
zt = H - P["roof_t"] + 0.5
lid = fuse(lid, [sbox(s, L1[0], W / 2 - P["lid_t"] + 0.5, y0, y1, split, zt) for s in SIDES
                 for y0, y1 in ((-D / 2 + P["lid_t"] - 0.5, cav_y0), (Hy - 14, Hy - 4))])
lid = cut(lid, [cylz(P["mag_d"] + P["mag_clr"], mag_h + 1, s * mag_x, mag_y, split - 1) for s in SIDES]
          + [polyx(s, g.mort, L1[0] - 1, L1[1] + 0.1) for s in SIDES])

# ---------------- MANIVELAS (camada 1) e BALANCINS (camada 2) ----------------
cranks, levers = {}, {}
slot_rel = g.slot_world
for s in SIDES:
    c = fuse(polyx(s, g.ring_outline(), *L1), [polyx(s, g.arm, *L1), polyx(s, g.tenon, *L1),
                                                 cylx(s, g.CRANK_HUB_R, *L1, Hy, Hz),
                                                 cylx(s, g.CRANK_HW, *L1, Hy + Cc[0], Hz + Cc[1])])
    cranks[s] = cut(c, [cylx(s, pin_d / 2 + P["hinge_clr"], L1[0] - 0.5, L1[1] + 0.5, Hy, Hz),
                        cylx(s, (pin_d - P["pin_press"]) / 2, L1[0] - 0.5, L1[1] + 0.5, Hy + Cc[0], Hz + Cc[1])])
    lv = fuse(stadium_x(s, slot_rel, g.R_BAND, *L2), [polyx(s, g.out_arm, *L2), fan_x(s, g.gusset, *L2),
                                                     cylx(s, g.LEV_HUB_R, *L2, Hy + E0[0], Hz + E0[1]),
                                                     cylx(s, g.LEV_HUB_R, *L2, Hy + QY, Hz + QZ)])
    levers[s] = cut(lv, [stadium_x(s, slot_rel, g.SLOT_W / 2, L2[0] - 0.5, L2[1] + 0.5),
                         cylx(s, pin_d / 2 + P["hinge_clr"], L2[0] - 0.5, L2[1] + 0.5, Hy + QY, Hz + QZ),
                         cylx(s, (pin_d - P["pin_press"]) / 2, L2[0] - 0.5, L2[1] + 0.5, Hy + E0[0], Hz + E0[1])])

# ---------------- PINOS O3 ----------------
pins = {}
for s in SIDES:
    t = "R" if s > 0 else "L"
    for nome, y, z in (("Axle", Hy, Hz), ("Pivot", Hy + QY, Hz + QZ)):
        pins[nome + t] = fuse(cylx(s, pin_d / 2, x_ko - P["pin_bl"] + 0.1, W / 2 - P["head_t"] - 0.1, y, z),
                              [cylx(s, P["head_d"] / 2, W / 2 - P["head_t"] - 0.1, W / 2 - 0.1, y, z)])
    pins["Cpin" + t] = cylx(s, pin_d / 2, L1[0], L2[1] - cam_clr, Hy + Cc[0], Hz + Cc[1])
    pins["Epin" + t] = cylx(s, pin_d / 2, L1[0] + cam_clr, L2[1], Hy + E0[0], Hz + E0[1])

# ---------------- DIVISORIA (no lugar, na frente do deck) e DECK (so para checagem) ----------------
deck_y1 = cy + in_y / 2 - P["liner_t"]
deck_y0 = deck_y1 - P["n_cards"] * P["card_t"]
z_floor = z_c0 + P["crad_f"] + P["liner_t"]
dw = in_x - 2 * P["liner_t"] - 2 * P["div_gap"]
divider = fuse(box(-dw / 2, dw / 2, deck_y0 - P["div_t"], deck_y0, z_floor, z_floor + P["card_h"] - 7),
               [box(-P["tab_w"] / 2, P["tab_w"] / 2, deck_y0 - P["div_t"], deck_y0, z_floor + P["card_h"] - 8, z_floor + P["card_h"] + 1)])
deck = box(-P["card_w"] / 2, P["card_w"] / 2, deck_y0, deck_y1, z_floor, z_floor + P["card_h"])

# ---------------- documento ----------------
COLORS = {"Core": (0.12, 0.16, 0.27), "ShellR": (0.15, 0.2, 0.31), "ShellL": (0.15, 0.2, 0.31), "Lid": (0.83, 0.63, 0.09),
          "Cradle": (0.48, 0.13, 0.19), "Divider": (0.66, 0.2, 0.18), "CrankR": (0.6, 0.64, 0.68), "CrankL": (0.6, 0.64, 0.68),
          "LeverR": (0.75, 0.78, 0.8), "LeverL": (0.75, 0.78, 0.8), "Deck": (0.91, 0.89, 0.82)}
BODIES = {"Core": core, "ShellR": shells[1], "ShellL": shells[-1], "Lid": lid, "Cradle": cradle, "CrankR": cranks[1],
          "CrankL": cranks[-1], "LeverR": levers[1], "LeverL": levers[-1], "Divider": divider, "Deck": deck, **pins}

doc = App.getDocument("C_elevador") if "C_elevador" in App.listDocuments() else App.newDocument("C_elevador")
for o in list(doc.Objects):
    doc.removeObject(o.Name)
for name, shp in BODIES.items():
    o = doc.addObject("Part::Feature", name)
    o.Shape = shp
    o.Visibility = name != "Deck"   # sem isso, gerado no freecadcmd, tudo abre oculto
    if App.GuiUp:
        o.ViewObject.ShapeColor = COLORS.get(name, (0.36, 0.38, 0.41))
doc.recompute()
doc.saveAs(str(HERE / "C_elevador.FCStd"))
REPORT = {k: (round(v.Volume, 1), v.isValid(), len(v.Solids)) for k, v in BODIES.items()}
print(REPORT)
