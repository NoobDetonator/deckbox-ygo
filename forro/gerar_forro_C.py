#!/usr/bin/env python3
"""Molde de corte do forro do BERÇO da versão C (elevador), em tamanho real (A4 paisagem, 300 dpi).

    python forro/gerar_forro_C.py

Só o berço, onde ficam as cartas: fundo, frente (com o recorte em U), traseira e 2 laterais.
As medidas vêm do gerador do modelo (cad/C-elevador/gerar_came.py), então acompanham qualquer
mudança na caixa. Saídas: forro/forro_C_veludo_0-5mm.pdf (imprimir) e images/forro_C_veludo_0-5mm.png.
"""
import contextlib
import io
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cad" / "C-elevador"))
with contextlib.redirect_stdout(io.StringIO()):
    import gerar_came as g            # ponytail: o import reescreve o script do modelo, com o mesmo conteúdo

T = 0.5                               # espessura do veludo adesivo (mm)
TECIDO = "veludo adesivo de 0,5 mm"
SIDE_PLAY = 0.4                       # peça um pouco menor que o vão, para não embolar nos cantos
STOP = 0.5                            # as paredes param 0,5 mm abaixo da borda do berço
U_CLR = 0.5                           # o recorte em U do tecido fica 0,5 mm maior que o da parede
R_CUT = 0.8                           # cantos arredondados do corte

n, p = g.n, g.p
IN_X, IN_Y = p["in_x"], p["in_y"]                         # interior do berço
FLOOR = n["z_c0"] + g.P["crad_f"]                         # piso do berço
RIM = n["split"] - 0.5                                    # borda do berço
U_R = g.P["u_w"] / 2                                      # recorte em U da frente: meia-lua de raio u_w/2
U_C = RIM - g.P["u_d"] + U_R                              # centro da meia-lua (z)

WALL_H = (RIM - STOP) - (FLOOR + T)                       # do fundo forrado até 0,5 abaixo da borda
UR = U_R + U_CLR                                          # recorte do tecido
U_TOP = (RIM - STOP) - U_C                                # do topo da peça ao centro da meia-lua
PIECES = [  # nome, qtd, largura, altura, ordem, tem recorte em U
    ("FRENTE", 1, IN_X - SIDE_PLAY, WALL_H, "2º · largura toda · parede do recorte", True),
    ("TRASEIRA", 1, IN_X - SIDE_PLAY, WALL_H, "2º · largura toda", False),
    ("LATERAL", 2, IN_Y - 2 * T - SIDE_PLAY, WALL_H, "3º · entre frente e traseira", False),
    ("FUNDO", 1, IN_X - SIDE_PLAY, IN_Y - SIDE_PLAY, "1º · no piso do berço", False),
]

DPI = 300
MM = DPI / 25.4
PW, PH = round(297 * MM), round(210 * MM)
FD = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
INK, GREY, RED, GOLD = (31, 42, 68), (100, 108, 122), (227, 0, 27), (200, 150, 30)
cm = lambda v: f"{v / 10:.2f}".replace(".", ",") + " cm"
mmt = lambda v: f"{v:.1f}".replace(".", ",") + " mm"


def F(w, s):
    try:
        return ImageFont.truetype(str(FD / f"Montserrat-{w}.ttf"), s)
    except OSError:                    # sem Montserrat: Arial do Windows
        return ImageFont.truetype("arialbd.ttf" if w in ("Bold", "SemiBold") else "arial.ttf", s)


def arrow(d, a, b, col=INK):
    """Cota interna: linha com setas nas duas pontas."""
    d.line([a, b], fill=col, width=3)
    ux, uy = (b[0] - a[0]), (b[1] - a[1])
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    for tip, s in ((a, 1), (b, -1)):
        bx, by = tip[0] + s * ux * 30, tip[1] + s * uy * 30
        d.polygon([tip, (bx - uy * 10, by + ux * 10), (bx + uy * 10, by - ux * 10)], fill=col)


def text_rot(page, xy, text, font, col=INK):
    im = Image.new("RGBA", (int(font.getlength(text)) + 16, font.size + 20), (255, 255, 255, 0))
    ImageDraw.Draw(im).text((8, 4), text, font=font, fill=col)
    im = im.rotate(90, expand=True)
    page.paste(im, (int(xy[0] - im.width / 2), int(xy[1] - im.height / 2)), im)


def piece(page, d, x, y, nome, w, h, ordem, u):
    """Desenha uma peça com o canto superior esquerdo em (x, y) mm."""
    X, Y, Wp, Hp = x * MM, y * MM, w * MM, h * MM
    if u:   # contorno com o recorte em U no meio da borda de cima
        cx = X + Wp / 2
        uy = Y + U_TOP * MM
        pts = [(X, Y), (cx - UR * MM, Y), (cx - UR * MM, uy)]
        pts += [(cx - UR * MM * math.cos(math.radians(a)), uy + UR * MM * math.sin(math.radians(a))) for a in range(0, 181, 5)]
        pts += [(cx + UR * MM, Y), (X + Wp, Y), (X + Wp, Y + Hp), (X, Y + Hp), (X, Y)]
        d.line(pts, fill=RED, width=5, joint="curve")
    else:
        d.rounded_rectangle([X, Y, X + Wp, Y + Hp], radius=R_CUT * MM, outline=RED, width=5)
    # cotas internas: largura embaixo, altura a esquerda
    yb = Y + Hp - 7 * MM
    arrow(d, (X + 1.5 * MM, yb), (X + Wp - 1.5 * MM, yb))
    d.text((X + Wp / 2, yb - 12), cm(w), font=F("Bold", 44), fill=INK, anchor="md")
    d.text((X + Wp / 2, yb + 14), f"({mmt(w)})", font=F("Medium", 30), fill=GREY, anchor="ma")
    xl = X + 7 * MM
    arrow(d, (xl, Y + 1.5 * MM), (xl, Y + Hp - 1.5 * MM))
    text_rot(page, (xl - 34, Y + Hp / 2), cm(h), F("Bold", 44))
    text_rot(page, (xl + 30, Y + Hp / 2), f"({mmt(h)})", F("Medium", 30), GREY)
    cy = Y + Hp * (0.55 if u else 0.42)
    d.text((X + Wp / 2 + 3 * MM, cy), nome, font=F("Bold", 52), fill=INK, anchor="mm")
    d.text((X + Wp / 2 + 3 * MM, cy + 62), ordem, font=F("Medium", 28), fill=GREY, anchor="mm")
    if u:   # cotas do recorte
        cx, uy = X + Wp / 2, Y + U_TOP * MM
        arrow(d, (cx - UR * MM, Y - 4 * MM), (cx + UR * MM, Y - 4 * MM), GOLD)
        d.text((cx, Y - 5.5 * MM), f"recorte {cm(2 * UR)}", font=F("Bold", 30), fill=GOLD, anchor="md")
        arrow(d, (cx, Y + 0.8 * MM), (cx, uy + UR * MM - 0.8 * MM), GOLD)
        d.multiline_text((cx + UR * MM + 24, (Y + uy + UR * MM) / 2), cm(U_TOP + UR) + "\nde fundo", font=F("Bold", 30),
                         fill=GOLD, anchor="lm", spacing=6)


def build():
    page = Image.new("RGB", (PW, PH), "white")
    d = ImageDraw.Draw(page)
    d.text((12 * MM, 8 * MM), "Forro do berço — versão C (elevador)", font=F("Bold", 70), fill=INK)
    d.text((12 * MM, 16 * MM), f"{TECIDO.capitalize()}. Imprima em TAMANHO REAL (100 %, sem \"ajustar à página\"), "
           "recorte e use como molde no verso do tecido.", font=F("Medium", 36), fill=GREY)
    x, y = 12.0, 29.0
    for nome, qtd, w, h, ordem, u in PIECES[:3]:
        for _ in range(qtd):
            piece(page, d, x, y, nome, w, h, ordem, u)
            x += w + 4
    assert x - 4 <= 297 - 8, "a fileira de paredes não cabe na folha"
    nome, qtd, w, h, ordem, u = PIECES[3]
    y2 = y + WALL_H + 6
    piece(page, d, 12, y2, nome, w, h, ordem, u)
    assert y2 + h <= 210 - 8, "o fundo não cabe na folha"
    # legenda
    lx, ly = (12 + w + 12) * MM, y2 * MM
    num = lambda v: f"{v:g}".replace(".", ",")
    info = [("Peças", "1 fundo, 1 frente (com o recorte em U), 1 traseira, 2 laterais. Lado do adesivo para a parede."),
            ("Ordem", "1º o fundo. 2º frente e traseira, com a largura toda. 3º as laterais, entre elas."),
            ("Frente", "é a parede do recorte em U. Alinhe os recortes: o do tecido é 0,5 mm maior e fica para trás da borda."),
            ("Borda", "as paredes param 0,5 mm abaixo da borda do berço. Não dobre o tecido por cima: o berço corre "
                      "no corpo com 0,3 mm de folga e o tecido trava."),
            ("Interior", f"berço de {cm(IN_X)} × {cm(IN_Y)}, parede de {cm(RIM - FLOOR)}. Ele foi desenhado para forro de "
                         f"{num(g.P['liner_t'])} mm; com veludo de {num(T)} mm as cartas ficam {num(2 * (g.P['liner_t'] - T))} mm mais "
                         "soltas na largura e na profundidade.")]
    fb, fr = F("Bold", 34), F("Medium", 34)
    for k, v in info:
        d.text((lx, ly), k.upper(), font=F("Bold", 28), fill=GOLD)
        ly += 40
        line = ""
        for word in v.split():
            t = (line + " " + word).strip()
            if d.textlength(t, font=fr) > (297 - 12) * MM - lx and line:
                d.text((lx, ly), line, font=fr, fill=INK)
                ly += 46
                line = word
            else:
                line = t
        d.text((lx, ly), line, font=fr, fill=INK)
        ly += 62
    # regua de 10 cm para conferir a escala
    rx, ry = lx, (210 - 14) * MM
    d.line([(rx, ry), (rx + 100 * MM, ry)], fill=INK, width=4)
    for k in range(101):
        hh = 40 if k % 10 == 0 else 24 if k % 5 == 0 else 14
        d.line([(rx + k * MM, ry), (rx + k * MM, ry - hh)], fill=INK, width=3 if k % 10 == 0 else 2)
        if k % 10 == 0:
            d.text((rx + k * MM, ry + 10), str(k // 10), font=F("Medium", 28), fill=INK, anchor="ma")
    d.text((rx + 104 * MM, ry - 10), "10 cm: confira com uma régua", font=F("SemiBold", 32), fill=INK, anchor="lm")
    return page


if __name__ == "__main__":
    for nome, qtd, w, h, *_ in PIECES:
        print(f"{nome:9s} ×{qtd}  {w:5.1f} × {h:5.1f} mm  =  {cm(w)} × {cm(h)}")
    # conferência: as peças cabem no berço forrado
    assert PIECES[0][2] <= IN_X and PIECES[2][2] + 2 * T <= IN_Y and PIECES[3][3] <= IN_Y
    assert abs(WALL_H + FLOOR + T + STOP - RIM) < 1e-9 and U_TOP + UR < WALL_H / 2
    page = build()
    Image.init()
    page.save(HERE / "forro_C_veludo_0-5mm.pdf", resolution=DPI, quality=92)
    page.resize((2180, round(2180 * PH / PW)), Image.LANCZOS).save(HERE.parent / "images" / "forro_C_veludo_0-5mm.png", optimize=True)
    print("ok")
