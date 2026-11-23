#!/usr/bin/env python3
"""Manual de montagem e desenho ortografico da versao C (A4 paisagem, 300 dpi).

    python manual/gerar_manual.py            # renderiza as cenas no solidcraft-cli e monta tudo
    python manual/gerar_manual.py --cache    # reaproveita as renderizacoes da ultima vez (so mudou texto)

Saidas: manual/C_manual_montagem.pdf e as duas folhas tecnicas em images/C_folha_*.png.
O solidcraft-cli vem de SOLIDCRAFT_CLI (ou do caminho padrao em render.py); a fonte e a Montserrat.
"""
import math, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from cenas import SC_, render_all, rx, LID_N, MAG_X, MAG_Y, n, g, Hy, Hz, S_SHEET1, S_SHEET2
from render import OUT

DPI, PW, PH = 300, 3508, 2480
MM = DPI / 25.4
FD = str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts/Montserrat-")
_fc = {}


def F(w, s):
    if (w, s) not in _fc:
        _fc[(w, s)] = ImageFont.truetype(FD + w + ".ttf", s)
    return _fc[(w, s)]


INK, GOLD, GREY, LINE = (31, 42, 68), (200, 150, 30), (100, 108, 122), (196, 203, 213)
ARROW, RED, SOFT, WHITE = (226, 96, 32), (178, 40, 48), (243, 245, 248), (255, 255, 255)
N_PAGES = 12
TITLE = "DECK BOX YGO  ·  VERSÃO C — ELEVADOR"
mm = lambda v: v * MM
fmt = lambda v, k=1: f"{v:.{k}f}".replace(".", ",")


# ----------------------------------------------------------------------------- utilidades
def wrap(d, text, font, width):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=font) > width and line:
            out.append(line)
            line = w
        else:
            line = t
    return out + [line]


def text_block(d, x, y, lines, font, fill=INK, width=None, gap=1.35, bullet=None):
    """Escreve paragrafos (lista); devolve o y final."""
    lh = font.size * gap
    for para in lines:
        ind = 0
        if bullet:
            d.text((x, y), bullet, font=font, fill=GOLD)
            ind = d.textlength(bullet + " ", font=font)
        for k, ln in enumerate(wrap(d, para, font, width - ind)):
            d.text((x + ind, y), ln, font=font, fill=fill)
            y += lh
        y += font.size * 0.45
    return y


def arrow(d, p1, p2, w=16, col=ARROW, outline=True):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    hl, hw = min(2.8 * w, 0.6 * L), 1.25 * w
    bx, by = x2 - ux * hl, y2 - uy * hl
    poly = [(x1 + nx * w / 2, y1 + ny * w / 2), (bx + nx * w / 2, by + ny * w / 2), (bx + nx * hw, by + ny * hw), (x2, y2),
            (bx - nx * hw, by - ny * hw), (bx - nx * w / 2, by - ny * w / 2), (x1 - nx * w / 2, y1 - ny * w / 2)]
    if outline:
        d.polygon(poly, outline=WHITE, width=10)
    d.polygon(poly, fill=col)


class Pic:
    """Renderizacao com a projecao da camera; desenhe setas antes de recortar."""
    def __init__(self, name):
        self.cam = SC_[name][0]
        self.im = Image.open(os.path.join(OUT, name + ".png")).convert("RGB")
        self.ox = self.oy = 0
        self.d = ImageDraw.Draw(self.im)

    def p(self, P):
        x, y = self.cam(P)
        return (x - self.ox, y - self.oy)

    def arrow(self, P1, P2, w=18):
        arrow(self.d, self.p(P1), self.p(P2), w)
        return self

    def crop(self, m=24):
        a = np.asarray(self.im.convert("L"))
        ys, xs = np.where(a < 248)
        x0, y0 = max(0, xs.min() - m), max(0, ys.min() - m)
        x1, y1 = min(self.im.width, xs.max() + m), min(self.im.height, ys.max() + m)
        self.im = self.im.crop((x0, y0, x1, y1))
        self.ox += x0
        self.oy += y0
        self.d = ImageDraw.Draw(self.im)
        return self


def fit(page, pic, x, y, w, h, maxs=1.0, align="c"):
    """Cola a imagem escalada para caber em (x,y,w,h); devolve P(3D) -> ponto na pagina."""
    s = min(w / pic.im.width, h / pic.im.height, maxs)
    im = pic.im.resize((max(1, int(pic.im.width * s)), max(1, int(pic.im.height * s))), Image.LANCZOS)
    px = x + (w - im.width) / 2 if align == "c" else x
    py = y + (h - im.height) / 2
    page.paste(im, (int(px), int(py)))
    return lambda P: (px + s * pic.p(P)[0], py + s * pic.p(P)[1]), (px, py, im.width, im.height)


def place(page, pic, P, at):
    """Cola em escala 1 com o ponto 3D P caindo em 'at' (pagina). Para as folhas com escala."""
    x, y = pic.p(P)
    ox, oy = at[0] - x, at[1] - y
    page.paste(pic.im, (int(round(ox)), int(round(oy))))
    return lambda Q: (ox + pic.p(Q)[0], oy + pic.p(Q)[1])


def new_page(num, section):
    page = Image.new("RGB", (PW, PH), WHITE)
    d = ImageDraw.Draw(page)
    d.text((mm(14), mm(9)), TITLE, font=F("Bold", 30), fill=GREY)
    t = f"{section}   {num} / {N_PAGES}"
    d.text((PW - mm(14) - d.textlength(t, font=F("SemiBold", 30)), mm(9)), t, font=F("SemiBold", 30), fill=GREY)
    d.line([(mm(14), mm(15)), (PW - mm(14), mm(15))], fill=LINE, width=3)
    return page, d


def step_head(d, x, y, num, title, w):
    f = F("ExtraBold", 150)
    d.text((x, y - 30), str(num), font=f, fill=GOLD)
    tx = x + d.textlength(str(num), font=f) + 34
    d.text((tx, y + 18), title, font=F("Bold", 66), fill=INK)
    return y + 150


def badge(d, x, y, text, r=34, fill=INK, fg=WHITE, font=None):
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    font = font or F("Bold", int(r * 1.1))
    d.text((x, y), text, font=font, fill=fg, anchor="mm")


def pin_icon(d, x, y, L, D=3.0, s=MM, col=(120, 126, 136)):
    """Pino de aco desenhado em escala s (px/mm), centrado em (x, y), horizontal."""
    l, h = L * s, D * s
    x0, y0 = x - l / 2, y - h / 2
    for k in range(int(h)):
        v = math.cos((k / h - 0.35) * math.pi)
        c = tuple(int(min(255, ci + 90 * max(0, v))) for ci in col)
        d.line([(x0, y0 + k), (x0 + l, y0 + k)], fill=c)
    d.rectangle([x0, y0, x0 + l, y0 + h], outline=(60, 64, 72), width=2)


def hw_tag(d, x, y, count, L, label):
    """Etiqueta de ferragem: '4×' + pino em tamanho real + legenda."""
    w = mm(L) + 330
    d.rounded_rectangle([x, y, x + w, y + 120], radius=24, fill=SOFT)
    d.text((x + 26, y + 60), f"{count}×", font=F("ExtraBold", 58), fill=INK, anchor="lm")
    pin_icon(d, x + 150 + mm(L) / 2, y + 48, L)
    d.text((x + 150, y + 84), label, font=F("SemiBold", 28), fill=GREY)
    return w


# ----------------------------------------------------------------------------- cotas
def _txt_rot(page, text, font, center, angle):
    im = Image.new("RGBA", (int(font.getlength(text)) + 20, font.size + 24), (255, 255, 255, 0))
    ImageDraw.Draw(im).text((10, 4), text, font=font, fill=INK)
    im = im.rotate(angle, expand=True)
    page.paste(im, (int(center[0] - im.width / 2), int(center[1] - im.height / 2)), im)


def _head(d, tip, ux, uy, L=34, W=10):
    nx, ny = -uy, ux
    b = (tip[0] - ux * L, tip[1] - uy * L)
    d.polygon([tip, (b[0] + nx * W, b[1] + ny * W), (b[0] - nx * W, b[1] - ny * W)], fill=INK)


def dim_h(page, d, a, b, y, text, font=None):
    """Cota horizontal entre os pontos a e b (pagina), linha em y."""
    font = font or F("Medium", 40)
    for p in (a, b):
        s = 1 if y > p[1] else -1
        d.line([(p[0], p[1] + s * 12), (p[0], y + s * 18)], fill=INK, width=2)
    d.line([(a[0], y), (b[0], y)], fill=INK, width=3)
    _head(d, (a[0], y), -1, 0)
    _head(d, (b[0], y), 1, 0)
    tw = d.textlength(text, font=font)
    cx = (a[0] + b[0]) / 2
    d.text((cx - tw / 2, y - font.size - 14), text, font=font, fill=INK)


def dim_v(page, d, a, b, x, text, font=None, side=-1):
    font = font or F("Medium", 40)
    for p in (a, b):
        s = 1 if x > p[0] else -1
        d.line([(p[0] + s * 12, p[1]), (x + s * 18, p[1])], fill=INK, width=2)
    d.line([(x, a[1]), (x, b[1])], fill=INK, width=3)
    top, bot = min(a[1], b[1]), max(a[1], b[1])
    _head(d, (x, top), 0, -1)
    _head(d, (x, bot), 0, 1)
    _txt_rot(page, text, font, (x + side * (font.size / 2 + 16), (top + bot) / 2), 90)


def center_mark(d, p, r=26):
    d.line([(p[0] - r - 16, p[1]), (p[0] + r + 16, p[1])], fill=INK, width=2)
    d.line([(p[0], p[1] - r - 16), (p[0], p[1] + r + 16)], fill=INK, width=2)
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=INK, width=3)


def leader(d, p, q, text, font=None, anchor="r"):
    """Linha de chamada do ponto p (peca) ate q (texto)."""
    font = font or F("SemiBold", 38)
    d.line([p, q], fill=WHITE, width=10)                 # halo: a linha aparece sobre as pecas escuras
    d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], fill=WHITE)
    d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=INK)
    d.line([p, q], fill=INK, width=3)
    tw = d.textlength(text, font=font)
    end = (q[0] - 20 - tw, q[1]) if anchor == "r" else (q[0] + 20 + tw, q[1])
    d.line([q, (end[0] if anchor == "l" else q[0] - 10, q[1])], fill=INK, width=3)
    tx = q[0] - 20 - tw if anchor == "r" else q[0] + 20
    d.text((tx, q[1] - font.size - 6), text, font=font, fill=INK)


def sheet_frame(page, d, folha, titulo, escala):
    d.rectangle([mm(20), mm(10), PW - mm(10), PH - mm(10)], outline=INK, width=6)
    x0, y0, x1, y1 = PW - mm(10) - mm(140), PH - mm(10) - mm(32), PW - mm(10), PH - mm(10)
    d.rectangle([x0, y0, x1, y1], fill=WHITE, outline=INK, width=5)
    d.line([(x0, y0 + mm(12)), (x1, y0 + mm(12))], fill=INK, width=3)
    d.line([(x0, y0 + mm(22)), (x1, y0 + mm(22))], fill=INK, width=3)
    for xx in (x0 + mm(35), x0 + mm(70), x0 + mm(105)):
        d.line([(xx, y0 + mm(22)), (xx, y1)], fill=INK, width=3)
    lab, val = F("Medium", 24), F("Bold", 34)
    d.text((x0 + 24, y0 + 16), "DECK BOX YGO — VERSÃO C (ELEVADOR)", font=F("Bold", 40), fill=INK)
    d.text((x0 + 24, y0 + mm(12) + 14), titulo, font=F("SemiBold", 40), fill=INK)
    cells = [("ESCALA", escala), ("UNIDADE", "mm"), ("MATERIAL", "ABS"), ("FOLHA", folha)]
    for k, (l, v) in enumerate(cells):
        cx = x0 + mm(35) * k + 20
        d.text((cx, y0 + mm(22) + 10), l, font=lab, fill=GREY)
        d.text((cx, y0 + mm(22) + 44), v, font=val, fill=INK)
    # simbolo do 1o diedro: tronco de cone (estreito a esquerda) e os circulos a direita
    sx, sy = x1 - mm(30), y0 + mm(6)
    d.text((sx - 30, sy), "1º DIEDRO", font=lab, fill=GREY, anchor="rm")
    d.polygon([(sx, sy - 18), (sx + 74, sy - 36), (sx + 74, sy + 36), (sx, sy + 18)], outline=INK, width=4)
    d.line([(sx - 12, sy), (sx + 86, sy)], fill=INK, width=2)
    cx = sx + 150
    d.ellipse([cx - 36, sy - 36, cx + 36, sy + 36], outline=INK, width=4)
    d.ellipse([cx - 18, sy - 18, cx + 18, sy + 18], outline=INK, width=4)
    d.line([(cx - 48, sy), (cx + 48, sy)], fill=INK, width=2)
    d.line([(cx, sy - 48), (cx, sy + 48)], fill=INK, width=2)
    return (x0, y0)


def view_label(d, x, y, text, sub=None):
    d.text((x, y), text, font=F("Bold", 36), fill=INK, anchor="mt")
    if sub:
        d.text((x, y + 48), sub, font=F("Medium", 28), fill=GREY, anchor="mt")


# ----------------------------------------------------------------------------- paginas
def p_capa():
    page = Image.new("RGB", (PW, PH), WHITE)
    d = ImageDraw.Draw(page)
    d.rectangle([0, PH - mm(16), PW, PH], fill=INK)
    d.text((mm(14), PH - mm(8)), "Modelo paramétrico em SolidCraft  ·  cad/C-elevador  ·  impressão 3D em ABS, sem suporte",
           font=F("Medium", 34), fill=(210, 216, 228), anchor="lm")
    x = mm(16)
    d.text((x, mm(22)), "DECK BOX YGO", font=F("Bold", 54), fill=GOLD)
    d.text((x - 8, mm(30)), "Versão C", font=F("ExtraBold", 230), fill=INK)
    d.text((x - 4, mm(54)), "Elevador", font=F("Light", 200), fill=INK)
    d.text((x, mm(78)), "Manual de montagem e desenho técnico", font=F("SemiBold", 58), fill=GREY)
    y = text_block(d, x, mm(92), ["Ao abrir a tampa, um mecanismo escondido nas laterais ergue as cartas 22 mm acima da borda. "
                                   "Ao fechar, elas descem juntas e os ímãs seguram a tampa."], F("Regular", 44), width=mm(125))
    specs = [("Medidas", "92,8 × 78,6 × 101,0 mm"), ("Capacidade", "90 cartas com sleeve duplo + divisória"),
             ("Peças impressas", "10 (2 manivelas e 2 balancins)"), ("Ferragens", "8 pinos de aço Ø3, 4 ímãs 4 × 2, 4 pés"),
             ("Tempo de montagem", "~1 h + 24 h de cura da acetona")]
    y += mm(6)
    for k, v in specs:
        d.text((x, y), k.upper(), font=F("Bold", 28), fill=GREY)
        d.text((x + mm(48), y - 8), v, font=F("SemiBold", 42), fill=INK)
        y += mm(9.5)
    y += mm(4)
    d.text((x, y), "NESTE MANUAL", font=F("Bold", 28), fill=GOLD)
    y += mm(6)
    toc = [("2", "Vistas ortográficas"), ("3", "Mecanismo"), ("4", "Peças impressas"), ("5", "Ferragens e preparo"),
           ("6–11", "Montagem passo a passo"), ("12", "Uso e cuidados")]
    for i, (pg, t) in enumerate(toc):
        cx = x + (i % 2) * mm(66)
        cy = y + (i // 2) * mm(7.5)
        d.text((cx, cy), pg, font=F("Bold", 36), fill=GOLD)
        d.text((cx + mm(14), cy), t, font=F("Medium", 36), fill=INK)
    a = Pic("c_closed").crop()
    b = Pic("c_open").crop()
    fit(page, a, mm(150), mm(70), mm(62), mm(115))
    fit(page, b, mm(212), mm(18), mm(78), mm(168))
    d.text((mm(181), mm(186)), "fechada", font=F("SemiBold", 36), fill=GREY, anchor="mt")
    d.text((mm(251), mm(186)), "aberta: o berço sobe 22 mm", font=F("SemiBold", 36), fill=GREY, anchor="mt")
    return page


def p_folha1():
    page = Image.new("RGB", (PW, PH), WHITE)
    d = ImageDraw.Draw(page)
    fr, lf, tp = Pic("o_front"), Pic("o_left"), Pic("o_top")
    W2, D2, H, split = n["W"] / 2, n["D"] / 2, n["H"], n["split"]
    X0, ZB = mm(48), mm(86)                    # canto esquerdo/fundo da vista frontal
    PF = place(page, fr, (-W2, 0, 0), (X0, ZB))
    PL = place(page, lf, (0, D2, 0), (X0 + mm(46.4 + 34), ZB))
    PT = place(page, tp, (-W2, D2, 50.5), (X0, ZB + mm(30)))
    iso = Pic("o_iso").crop()
    fit(page, iso, mm(178), mm(16), mm(104), mm(138))
    sheet_frame(page, d, "1 / 2", "CONJUNTO — VISTAS ORTOGRÁFICAS", "1:2")
    # cotas
    dim_h(page, d, PT((-W2, -D2, 50)), PT((W2, -D2, 50)), PT((0, -D2, 50))[1] + mm(12), fmt(n["W"]))
    dim_v(page, d, PF((-W2, 0, 0)), PF((-W2, 0, H)), PF((-W2, 0, 0))[0] - mm(12), fmt(H))
    xr = PF((W2, 0, 0))[0] + mm(10)
    dim_v(page, d, PF((W2, 0, 0)), PF((W2, 0, split)), xr, fmt(split), side=1)
    dim_v(page, d, PF((W2, 0, split)), PF((W2, 0, H)), xr, fmt(H - split), side=1)
    dim_h(page, d, PL((0, D2, 0)), PL((0, -D2, 0)), PL((0, 0, 0))[1] + mm(12), fmt(n["D"]))
    view_label(d, PF((0, 0, 0))[0], PF((0, 0, H))[1] - mm(13), "VISTA FRONTAL")
    view_label(d, PL((0, 0, 0))[0], PL((0, 0, H))[1] - mm(13), "VISTA LATERAL ESQUERDA")
    view_label(d, PT((0, 0, 50))[0], PT((0, -D2, 50))[1] + mm(19), "VISTA SUPERIOR")
    view_label(d, mm(230), mm(155), "PERSPECTIVA ISOMÉTRICA", "tampa aberta a 110°, berço erguido — sem escala")
    notes = ["Cotas externas da caixa montada, com os painéis laterais.", "Interior do berço: 66,4 × 67,2 mm (com forro de 1 mm).",
             "Projeção no 1º diedro (ABNT NBR 10067)."]
    text_block(d, mm(26), mm(181), notes, F("Medium", 30), fill=GREY, width=mm(118), gap=1.2, bullet="•")
    return page


def p_folha2():
    page = Image.new("RGB", (PW, PH), WHITE)
    d = ImageDraw.Draw(page)
    a, b = Pic("m_closed"), Pic("m_open")
    D2 = n["D"] / 2
    GY = mm(158)                                   # linha do chao das duas vistas
    PA = place(page, a, (0, -D2, 0), (mm(56), GY))
    PB = place(page, b, (0, -D2, 0), (mm(165), GY))
    sheet_frame(page, d, "2 / 2", "MECANISMO — VISTA LATERAL SEM O PAINEL", "1:1")
    X = 45
    H_, Q_ = (X, Hy, Hz), (X, Hy + g.QY, Hz + g.QZ)
    C_ = (X, Hy + g.Cc[0], Hz + g.Cc[1])
    E_ = (X, Hy + g.E0[0], Hz + g.E0[1])
    # chamadas a esquerda, cada uma na altura da sua peca
    xl = mm(52)
    for P, zl, t in (((X, -12, 96), 106, "tampa"), ((X, -26, 82), 92, "berço"), (C_, 76, "pino da manivela"),
                     ((X, 12, 59.2), 62, "balancim"), (E_, 48, "garfo do berço"), ((X, 0, 14), 16, "corpo")):
        leader(d, PA(P), (xl, PA((X, 0, zl))[1]), t, font=F("SemiBold", 36))
    # H e Q: marcas de centro e cotas em serie a direita
    for p, t, dz in ((H_, "H", 5.5), (Q_, "Q", -5.5)):
        center_mark(d, PA(p), r=20)
        q = PA((X, D2 + 4.5, p[2] + dz))
        d.ellipse([q[0] - 26, q[1] - 26, q[0] + 26, q[1] + 26], fill=WHITE, outline=INK, width=3)
        d.text(q, t, font=F("Bold", 32), fill=INK, anchor="mm")
    xr = PA((X, D2, 0))[0] + mm(8)
    dim_v(page, d, PA((X, D2, 0)), PA(Q_), xr, fmt(Q_[2]), side=1)
    dim_v(page, d, PA(Q_), PA(H_), xr, fmt(H_[2] - Q_[2]), side=1)
    view_label(d, PA((X, 0, 0))[0], GY + mm(5), "FECHADA (0°)", "H: eixo da tampa  ·  Q: pivô do balancim")
    # vista aberta: angulo (com halo branco), curso do berco e altura total
    h = PB(H_)
    r = mm(16)
    for wdt, col in ((16, WHITE), (6, ARROW)):
        d.arc([h[0] - r, h[1] - r, h[0] + r, h[1] + r], 180, 290, fill=col, width=wdt)
    d.line([h, (h[0] - r - 20, h[1])], fill=WHITE, width=10)
    d.line([h, (h[0] - r - 20, h[1])], fill=ARROW, width=4)
    end = (h[0] + r * math.cos(math.radians(-70)), h[1] + r * math.sin(math.radians(-70)))
    _head(d, end, math.cos(math.radians(20)), math.sin(math.radians(20)), 30, 12)
    lb = (h[0] - mm(7), h[1] - r - mm(9))
    d.rounded_rectangle([lb[0] - 80, lb[1] - 36, lb[0] + 80, lb[1] + 36], radius=14, fill=WHITE)
    d.text(lb, "110°", font=F("Bold", 46), fill=ARROW, anchor="mm")
    top_c, lift = 88.067, g.L(110)
    lmax = max(g.L(t) for t in range(111))
    x_c = PB((X, -D2, 0))[0] - mm(7)
    dim_v(page, d, PB((X, -37, top_c)), PB((X, -37, top_c + lift)), x_c, fmt(lift))
    zmax = max(rx((0, y, z), -110)[2] for y in (-D2, D2) for z in (n["split"], n["H"]))
    lx = PB((X, -10, 0))[0]
    d.text((lx, PB((X, 0, 146))[1]), "ABERTA (110°, NO BATENTE)", font=F("Bold", 36), fill=INK, anchor="mt")
    text_block(d, lx - mm(32), PB((X, 0, 146))[1] + 50,
               [f"Berço: sobe {fmt(lmax)} mm até 95° e assenta {fmt(lift)} mm no batente.",
                f"Altura com a tampa aberta: {fmt(zmax)} mm."], F("Medium", 28), fill=GREY, width=mm(64), gap=1.2)
    tab = [("Tampa", "0–25°", "25–95°", "95–110°"), ("Berço", "parado", f"sobe {fmt(lmax)} mm", "desce 0,6 mm")]
    tx, ty = mm(26), mm(178)
    for i, row in enumerate(tab):
        for j, c in enumerate(row):
            d.text((tx + j * mm(27), ty + i * mm(6.5)), c, font=F("Bold" if i == 0 or j == 0 else "Medium", 32),
                   fill=INK if i == 0 or j == 0 else GREY)
    d.text((tx, ty + mm(14)), "Curva de subida desenhada na ranhura do balancim.", font=F("Medium", 28), fill=GREY)
    return page


def p_pecas():
    page, d = new_page(4, "PEÇAS")
    d.text((mm(14), mm(21)), "Peças impressas", font=F("Bold", 80), fill=INK)
    d.text((mm(14), mm(33)), "Os STLs de stl/C-elevador já estão na posição de impressão. Nenhuma peça precisa de suporte.",
           font=F("Medium", 38), fill=GREY)
    parts = [("A", "Corpo", "p_core", 1, "C_corpo.stl"), ("B", "Berço", "p_cradle", 1, "C_berco.stl"),
             ("C", "Tampa", "p_lid", 1, "C_tampa.stl"), ("D", "Divisória", "p_divider", 1, "C_divisoria.stl"),
             ("E", "Painel direito", "p_shellr", 1, "C_painel_direito.stl"), ("F", "Painel esquerdo", "p_shelll", 1, "C_painel_esquerdo.stl"),
             ("G", "Manivela", "p_crank", 2, "C_manivela_x2.stl"), ("H", "Balancim", "p_lever", 2, "C_balancim_x2.stl")]
    cw, ch = (PW - mm(28)) / 4, mm(68)
    for i, (L, name, sc, q, f) in enumerate(parts):
        x, y = mm(14) + (i % 4) * cw, mm(44) + (i // 4) * (ch + mm(4))
        d.rounded_rectangle([x + 10, y, x + cw - 10, y + ch], radius=30, fill=WHITE, outline=LINE, width=4)
        fit(page, Pic(sc).crop(), x + 40, y + 40, cw - 80, ch - mm(20))
        badge(d, x + 70, y + 70, L, r=40, fill=GOLD)
        d.text((x + 40, y + ch - mm(15)), name, font=F("Bold", 46), fill=INK)
        d.text((x + cw - 40, y + ch - mm(15)), f"×{q}", font=F("ExtraBold", 50), fill=GOLD, anchor="ra")
        d.text((x + 40, y + ch - mm(7.5)), f, font=F("Medium", 30), fill=GREY)
    notes = ["Manivelas e balancins: 100 % de preenchimento e 4 perímetros. Ligue a compensação de pé de elefante, "
             "para a primeira camada não estreitar a ranhura e os furos.",
             "As duas manivelas são a mesma peça (uma vai virada), e os dois balancins também.",
             "Sem vareta de aço? Imprima C_pino_longo_x4 e C_pino_curto_x4 deitados, camada de 0,1 mm e 100 % de preenchimento."]
    text_block(d, mm(14), mm(187), notes[:1], F("Medium", 32), fill=GREY, width=mm(130), gap=1.25, bullet="•")
    text_block(d, mm(152), mm(187), notes[1:], F("Medium", 32), fill=GREY, width=mm(132), gap=1.25, bullet="•")
    return page


def p_ferragens():
    page, d = new_page(5, "FERRAGENS")
    d.text((mm(14), mm(21)), "Ferragens", font=F("Bold", 80), fill=INK)
    d.text((mm(14), mm(33)), "Tamanho real: imprima esta página em 100 % e confira os pinos sobre o papel.", font=F("Medium", 38), fill=GREY)
    y = mm(48)
    rows = [("4×", 9.3, "Pino de aço Ø3 × 9,3 mm", "eixos da tampa e pivôs. Mais longo, o painel não assenta."),
            ("4×", 6.4, "Pino de aço Ø3 × 6,4 mm", "pinos da manivela e da ponta do balancim.")]
    for c, L, t, sub in rows:
        d.rounded_rectangle([mm(14), y, mm(140), y + mm(26)], radius=30, fill=SOFT)
        d.text((mm(20), y + mm(13)), c, font=F("ExtraBold", 80), fill=GOLD, anchor="lm")
        pin_icon(d, mm(42) + mm(L) / 2, y + mm(13), L)
        d.text((mm(62), y + mm(6)), t, font=F("Bold", 42), fill=INK)
        text_block(d, mm(62), y + mm(13), [sub], F("Medium", 32), fill=GREY, width=mm(74), gap=1.2)
        y += mm(30)
    # ima e pe
    d.rounded_rectangle([mm(14), y, mm(140), y + mm(26)], radius=30, fill=SOFT)
    d.text((mm(20), y + mm(13)), "4×", font=F("ExtraBold", 80), fill=GOLD, anchor="lm")
    cx, cy = mm(46), y + mm(13)
    d.ellipse([cx - mm(2), cy - mm(2), cx + mm(2), cy + mm(2)], fill=(150, 156, 166), outline=(60, 64, 72), width=2)
    d.rectangle([cx + mm(5), cy - mm(1), cx + mm(9), cy + mm(1)], fill=(150, 156, 166), outline=(60, 64, 72), width=2)
    d.text((mm(62), y + mm(6)), "Ímã de neodímio 4 × 2 mm", font=F("Bold", 42), fill=INK)
    text_block(d, mm(62), y + mm(13), ["N35, dois no corpo e dois na tampa (furos Ø4,2 × 2,1)."], F("Medium", 32), fill=GREY, width=mm(74), gap=1.2)
    y += mm(30)
    d.rounded_rectangle([mm(14), y, mm(140), y + mm(26)], radius=30, fill=SOFT)
    d.text((mm(20), y + mm(13)), "4×", font=F("ExtraBold", 80), fill=GOLD, anchor="lm")
    cx = mm(46)
    cy = y + mm(13)
    d.ellipse([cx - mm(4), cy - mm(4), cx + mm(4), cy + mm(4)], fill=(60, 62, 66))
    d.text((mm(62), y + mm(6)), "Pé de silicone Ø8 mm", font=F("Bold", 42), fill=INK)
    text_block(d, mm(62), y + mm(13), ["adesivo, nos 4 rebaixos do fundo."], F("Medium", 32), fill=GREY, width=mm(74), gap=1.2)
    y += mm(32)
    d.text((mm(14), y), "VOCÊ TAMBÉM VAI USAR", font=F("Bold", 30), fill=GOLD)
    mats = ["Cola instantânea (CA)", "Acetona e pincel", "Lixa 220 e álcool", "Lubrificante PTFE seco", "Fita crepe",
            "Feltro adesivo de 1 mm (forro)"]
    for i, m_ in enumerate(mats):
        d.text((mm(14) + (i % 2) * mm(64), y + mm(7) + (i // 2) * mm(7)), "•  " + m_, font=F("Medium", 36), fill=INK)
    # passo 1
    X = mm(156)
    step_head(d, X, mm(21), 1, "Prepare", mm(130))
    y = mm(42)
    # furo fixo x furo que gira, ampliado 12:1
    S = 12 * MM
    for k, (dia, t1, t2) in enumerate(((3.1, "Ø3,1 — pino fixo", "entra justo: uma gota de CA"),
                                       (3.4, "Ø3,4 — pino gira", "folga de 0,4: nunca cole"))):
        cx, cy = X + mm(30) + k * mm(66), y + mm(30)
        R, r = dia / 2 * S, 1.5 * S
        d.rounded_rectangle([cx - mm(28), cy - mm(26), cx + mm(28), cy + mm(26)], radius=30, fill=SOFT)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=WHITE, outline=INK, width=6)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(140, 146, 156), outline=(60, 64, 72), width=4)
        d.text((cx, cy + mm(30)), t1, font=F("Bold", 40), fill=INK, anchor="mt")
        d.text((cx, cy + mm(36)), t2, font=F("Medium", 34), fill=GREY, anchor="mt")
    d.text((X + mm(129), y - mm(1)), "ampliado 12:1", font=F("Medium", 28), fill=GREY, anchor="rb")
    tips = ["Lixe com lixa 220 as faces que vão ser coladas (painéis, rabo-de-andorinha da manivela) e limpe com álcool.",
            "Furo de pino fixo (Ø3,1): o pino entra justo e leva só uma gota de CA. Não prense: prensado racha os ressaltos finos.",
            "Furo onde o pino gira (Ø3,4): cubo da manivela e furo do pivô no balancim. Sem cola e sem rebarba.",
            "Passe uma lixa fina na ranhura do balancim e nas fendas do corpo se ficou rebarba da primeira camada."]
    text_block(d, X, y + mm(78), tips, F("Medium", 38), width=mm(128), bullet="•")
    return page


def step_page(num, section, steps):
    """steps: lista de (n, titulo, imagens [(Pic, peso)], textos, ferragem) — 1 ou 2 por pagina."""
    page, d = new_page(num, section)
    k = len(steps)
    cw = (PW - mm(28) - (k - 1) * mm(10)) / k
    for i, (sn, title, pics, texts, hw) in enumerate(steps):
        x = mm(14) + i * (cw + mm(10))
        if not title:
            continue
        if i:
            d.line([(x - mm(5), mm(24)), (x - mm(5), PH - mm(14))], fill=LINE, width=3)
        y = step_head(d, x, mm(21), sn, title, cw)
        fnt = F("Medium", 38)
        # altura do texto
        tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        th = sum(len(wrap(tmp, t, fnt, cw - 60)) * fnt.size * 1.35 + fnt.size * 0.45 for t in texts)
        img_h = PH - mm(14) - y - th - mm(6)
        if hw:
            hx = x
            for c, L, lab in hw:
                hx += hw_tag(d, hx, y, c, L, lab) + 30
            y += 150
            img_h -= 150
        tot = sum(p[1] for p in pics)
        if len(pics) == 1 or k == 1:
            xx = x
            for pic, wgt, cap in pics:
                ww = cw * wgt / tot
                fit(page, pic, xx, y, ww, img_h)
                if cap:
                    d.text((xx + ww / 2, y + img_h - 10), cap, font=F("SemiBold", 34), fill=GREY, anchor="ms")
                xx += ww
        else:                                    # duas imagens empilhadas
            yy = y
            for pic, wgt, cap in pics:
                hh = img_h * wgt / tot
                fit(page, pic, x, yy, cw, hh - 20)
                if cap:
                    badge(d, x + 40, yy + 40, cap, r=34, fill=GOLD)
                yy += hh
        text_block(d, x, PH - mm(14) - th, texts, fnt, width=cw - 60, bullet="•")
    return page, d


def p_steps():
    W2, D2 = n["W"] / 2, n["D"] / 2
    pages = []
    s2 = Pic("s2").arrow((0, -D2, 126), (0, -D2, 96)).crop()
    s3 = Pic("s3")
    for sx in (1, -1):
        s3.arrow((sx * 22, 30, 60), (sx * 35, 30, 60), 16)
    s3.crop()
    pages.append(step_page(6, "MONTAGEM", [
        (2, "Berço no corpo", [(s2, 1, None)],
         ["Desça o berço no corpo, por cima. As duas línguas laterais entram nas fendas do corpo.",
          "Ele tem de descer sozinho, pelo peso. Se agarrar, lixe as línguas; não force."], None),
        (3, "Manivelas na tampa", [(s3, 1, None)],
         ["Com a tampa de cabeça para baixo, encaixe o rabo-de-andorinha de cada manivela na orelha da tampa, por dentro, "
          "empurrando para fora.", "Uma gota de acetona no encaixe e 10 min para secar.",
          "As duas manivelas são a mesma peça: a do outro lado vai virada."], None)])[0])
    s4 = Pic("s4").arrow((0, -D2, 140), (0, -D2, 99)).crop()
    s5 = Pic("s5")
    for z in (Hz, Hz + g.QZ):
        s5.arrow((66, Hy, z), (50, Hy, z), 20)
    s5.crop()
    pages.append(step_page(7, "MONTAGEM", [
        (4, "Tampa no corpo", [(s4, 1, None)],
         ["Feche a tampa sobre o corpo, com as manivelas para trás.",
          "Na lateral, o cubo de cada manivela fica alinhado com o furo do eixo."], None),
        (5, "Eixo e pivô", [(s5, 1, None)],
         ["De cada lado: um pino no furo do eixo (atravessa o corpo e o cubo da manivela) e um no furo do pivô, logo abaixo.",
          "Uma gota de CA só na ponta que entra no corpo. A ponta de fora fica livre: o painel encaixa nela.",
          "Repita do lado esquerdo."], [(4, 9.3, "Ø3 × 9,3")])])[0])
    C_ = (0, Hy + g.Cc[0], Hz + g.Cc[1])
    E_ = (0, Hy + g.E0[0], Hz + g.E0[1])
    s6 = Pic("s6").arrow((58, C_[1], C_[2]), (46.5, C_[1], C_[2]), 18).crop()
    s7a = Pic("s7a").arrow((52.5, E_[1], E_[2]), (45.5, E_[1], E_[2]), 16).crop()
    s7b = Pic("s7b")
    s7b.arrow((68, Hy, Hz + g.QZ), (48, Hy, Hz + g.QZ), 18).arrow((66, E_[1], E_[2]), (48, E_[1], E_[2]), 18).crop()
    pages.append(step_page(8, "MONTAGEM", [
        (6, "Pino da manivela", [(s6, 1, None)],
         ["Cole um pino de 6,4 mm no furo da ponta de cada manivela (Ø3,1, uma gota de CA).",
          "Ele aponta para fora: vai correr na ranhura do balancim.", "Repita do lado esquerdo."], [(2, 6.4, "Ø3 × 6,4")]),
        (7, "Balancim", [(s7a, 0.8, "a"), (s7b, 1.2, "b")],
         ["a) Cole um pino de 6,4 mm na ponta do braço, apontando para dentro.",
          "b) Encaixe o balancim no pivô. Ao mesmo tempo, o pino da manivela entra na ranhura e o pino da ponta entra no garfo do berço.",
          "O furo do pivô no balancim gira: sem cola."], [(2, 6.4, "Ø3 × 6,4")])])[0])
    s8 = Pic("s8").arrow((80, -5, 40), (50, -5, 40), 20).arrow((-80, -5, 40), (-50, -5, 40), 20).crop()
    m = [Pic(f"s8_{t}").crop() for t in (0, 60, 110)]
    page, d = new_page(9, "MONTAGEM")
    y = step_head(d, mm(14), mm(21), 8, "Teste a seco", mm(130))
    fit(page, s8, mm(14), y, mm(118), PH - y - mm(16))
    xs = mm(140)
    d.text((xs, y - mm(2)), "O que você deve ver, pelo lado (painel tirado só no desenho):", font=F("SemiBold", 38), fill=INK)
    caps = [("0°", "fechada: berço embaixo"), ("60°", f"subindo: +{fmt(g.L(60))} mm"), ("110°", f"no batente: +{fmt(g.L(110))} mm")]
    cw = mm(48)
    for i, (pic, (a_, b_)) in enumerate(zip(m, caps)):
        x = xs + i * cw
        fit(page, pic, x, y + mm(8), cw - 20, mm(84))
        d.text((x + cw / 2, y + mm(96)), a_, font=F("ExtraBold", 54), fill=GOLD, anchor="mt")
        d.text((x + cw / 2, y + mm(104)), b_, font=F("Medium", 32), fill=GREY, anchor="mt")
    texts = ["Encaixe os painéis pelos pinos-guia e prenda com fita crepe, ainda sem cola.",
             "Com o deck dentro, abra e feche umas 20 vezes. Até uns 25° o berço fica parado, depois sobe suave e, no fim, "
             "desce um pouco e a tampa fica aberta sozinha.",
             "Raspou ou travou? Ajuste cam_clr ou rail_clr no modelo e reimprima só aquela peça."]
    text_block(d, xs, y + mm(116), texts, F("Medium", 38), width=PW - xs - mm(18), bullet="•")
    pages.append(page)
    s9 = Pic("s9").crop()
    s10 = Pic("s10")
    for sx in (1, -1):
        s10.arrow((sx * MAG_X, MAG_Y, n["split"] + 13), (sx * MAG_X, MAG_Y, n["split"] + 2), 14)
        R = rx((sx * MAG_X, MAG_Y, n["split"] + 1.1), -110)
        s10.arrow(tuple(R[i] + 13 * LID_N[i] for i in range(3)), tuple(R[i] + 3 * LID_N[i] for i in range(3)), 14)
    s10.crop()
    page, d = step_page(10, "MONTAGEM", [
        (9, "Solda dos painéis", [(s9, 1, None)],
         ["Lubrifique pinos e ranhuras com PTFE seco.",
          "Passe acetona com pincel só nas faces de contato da face interna do painel e encaixe pelos pinos-guia.",
          "Prenda por 10 min e deixe curar 24 h."], None),
        (10, "Ímãs", [(s10, 1, None)],
         ["Grude dois ímãs e marque com caneta as duas faces de fora da dupla. Separe: a face marcada vai para o fundo do furo, "
          "uma no corpo e outra na tampa. Faça o mesmo com o outro par.",
          "Uma gota de CA no fundo do furo (Ø4,2 × 2,1). O ímã fica 0,1 mm abaixo da face, sem encostar no da tampa."], None)])
    # aviso do passo 9
    x = mm(14)
    yb = mm(150)
    d.rounded_rectangle([x, yb, x + mm(125), yb + mm(17)], radius=24, fill=(250, 234, 234))
    d.text((x + 30, yb + mm(8.5)), "Depois disso a tampa não sai mais. Faça o teste a seco antes.", font=F("Bold", 36),
           fill=RED, anchor="lm")
    pages.append(page)
    s11 = Pic("s11")
    fx, fy = W2 - n["foot_e"], D2 - n["foot_e"]
    for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        s11.arrow((sx * fx, sy * fy, -11), (sx * fx, sy * fy, -2.5), 12)
    s11.crop()
    u = [Pic(f"u_{t}").crop() for t in (0, 55, 110)]
    page, d = step_page(11, "MONTAGEM", [
        (11, "Pés e forro", [(s11, 1, None)],
         ["Cole os 4 pés de silicone nos rebaixos do fundo.",
          "Forre o berço por dentro com feltro adesivo de 1 mm (veja \"Forro interno\" no README)."], None),
        ("", "", [], [], None)])
    # lado direito: pronto
    X = mm(14) + (PW - mm(28) - mm(10)) / 2 + mm(10)
    d.text((X, mm(21)), "Pronto!", font=F("ExtraBold", 150), fill=GOLD)
    d.text((X, mm(40)), "Abra pela frente: até 25° nada muda, depois as cartas sobem.", font=F("SemiBold", 40), fill=INK)
    cw = (PW - mm(14) - X) / 3
    for i, (pic, t) in enumerate(zip(u, ("0°", "55°", "110°"))):
        fit(page, pic, X + i * cw, mm(50), cw - 20, mm(110))
        d.text((X + i * cw + cw / 2, mm(166)), t, font=F("ExtraBold", 54), fill=GOLD, anchor="mt")
        lab = ("fechada", f"berço +{fmt(g.L(55))} mm", f"berço +{fmt(g.L(110))} mm")[i]
        d.text((X + i * cw + cw / 2, mm(176)), lab, font=F("Medium", 34), fill=GREY, anchor="mt")
    pages.append(page)
    return pages


def p_uso():
    page, d = new_page(12, "USO")
    d.text((mm(14), mm(21)), "Uso e cuidados", font=F("Bold", 80), fill=INK)
    pic = Pic("u_110").crop()
    fit(page, pic, mm(14), mm(36), mm(110), mm(158))
    X = mm(140)
    d.text((X, mm(40)), "NO DIA A DIA", font=F("Bold", 32), fill=GOLD)
    y = text_block(d, X, mm(48), [
        "Abra pela frente. Até uns 25° o berço fica parado: o teto da tampa se afasta das cartas antes de elas subirem.",
        "Aberta, a tampa fica parada no batente, a 110°. As cartas ficam 22 mm acima da borda.",
        "Para fechar, empurre a tampa: o berço desce junto e os ímãs seguram.",
        "Chiou ou ficou dura? Uma gota de PTFE seco nos pinos e nas ranhuras."], F("Medium", 40), width=mm(140), bullet="•")
    y += mm(6)
    d.text((X, y), "NÃO FAÇA", font=F("Bold", 32), fill=RED)
    y += mm(9)
    for t in ("Não force a tampa além do batente.", "Não levante a caixa pela tampa.",
              "Não empurre o deck para baixo com a caixa aberta."):
        badge(d, X + 30, y + 24, "×", r=30, fill=RED, font=F("Bold", 50))
        d.text((X + 90, y), t, font=F("SemiBold", 42), fill=INK)
        y += mm(10)
    text_block(d, X, y + mm(4), ["Essas cargas passam pela manivela e pelo balancim, peças de 3,2 mm de espessura. "
                                 "O mecanismo é feito para o peso do deck, não para alavanca."], F("Medium", 36), fill=GREY,
               width=mm(140))
    return page


def build():
    pages = [p_capa(), p_folha1(), p_folha2(), p_pecas(), p_ferragens()] + p_steps() + [p_uso()]
    assert len(pages) == N_PAGES, len(pages)
    here = Path(__file__).resolve().parent
    Image.init()  # registra o JPEG usado dentro do PDF
    pages[0].save(here / "C_manual_montagem.pdf", save_all=True, append_images=pages[1:], resolution=DPI, quality=82)
    for i, nome in ((1, "C_folha_ortografica"), (2, "C_folha_mecanismo")):
        pages[i].resize((1754, 1240), Image.LANCZOS).save(here.parent / "images" / f"{nome}.png", optimize=True)
    print("ok", len(pages), "paginas")


if __name__ == "__main__":
    if "--cache" not in sys.argv:
        render_all(force=True)
    build()
