#!/usr/bin/env python3
"""Gera o gabarito do adesivo da tampa em SVG (escala 1:1, mm, A4 paisagem).

Uma faixa contínua para as 4 laterais (emenda escondida na traseira, com sobreposição)
e uma peça para o topo, para as versões A e B. As medidas vêm dos parâmetros do modelo
em cad/*/_build.json: se você mudar W, D, r_out, split, H ou a dobradiça, ajuste aqui e
rode de novo:  python adesivo/gerar_guia.py
"""
import math
from pathlib import Path

# ---- medidas do modelo (mm) ----
W, D = 69.6, 67.6            # largura e profundidade externas
R = 4.0                      # raio dos cantos verticais (r_out)
TOP_CH, REVEAL = 1.0, 0.4    # chanfro do topo da tampa / chanfro na linha de divisão
LID_H = 30.5                 # altura da tampa (H - split)
# parte da traseira ocupada pela dobradiça: meia largura e altura acima da divisão
HINGE = {
    "A": {"half_x": W / 2 - R, "top": 4.64,   # nós + reforços a 45° da dobradiça integrada
          "nome": "versão A (dobradiça integrada)"},
    "B": {"half_x": 28.4, "top": 25.4,        # ressalto da dobradiça colada (pad_l/2, pad_h + pad_t)
          "nome": "versão B (dobradiça colada)"},
}
# ---- folgas do adesivo ----
MARGIN = 0.3      # longe das quinas dos chanfros, para a borda não levantar
CLEAR = 0.5       # folga em volta da dobradiça
OVERLAP = 5.0     # o fim da faixa passa por cima do começo
BLEED = 2.0       # sangria: estenda a arte até aqui
SAFE = 2.0        # área segura: textos e detalhes importantes dentro dela
TOP_INSET = 0.5   # peça do topo um pouco menor que a face plana
R_CUT = 1.0       # cantos arredondados no recorte (o adesivo não rasga nem levanta)

FLAT_W, FLAT_D = W - 2 * R, D - 2 * R
ARC = math.pi * R / 2
PERIM = 2 * (FLAT_W + FLAT_D) + 4 * ARC
BAND_LO = REVEAL + MARGIN                 # altura da borda de baixo acima da divisão
BAND_HI = LID_H - TOP_CH - MARGIN         # altura da borda de cima
BAND_H = BAND_HI - BAND_LO
LENGTH = PERIM + OVERLAP

# faixa: começa no meio da traseira e segue para a esquerda de quem olha a traseira
FACES = []  # (nome, início, fim) ao longo da faixa
s = 0.0
for nome, comp in [("TRASEIRA", FLAT_W / 2), (None, ARC), ("LATERAL ESQUERDA", FLAT_D), (None, ARC),
                   ("FRENTE", FLAT_W), (None, ARC), ("LATERAL DIREITA", FLAT_D), (None, ARC),
                   ("TRASEIRA", FLAT_W / 2)]:
    FACES.append((nome, s, s + comp))
    s += comp
assert abs(s - PERIM) < 1e-9


def rounded_path(pts, r_convex, r_concave=None):
    """Polígono fechado (horário na tela, cantos de 90°) com os cantos arredondados."""
    r_concave = r_convex if r_concave is None else r_concave
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1 = ((p1[0] - p0[0]), (p1[1] - p0[1])); l1 = math.hypot(*d1); d1 = (d1[0] / l1, d1[1] / l1)
        d2 = ((p2[0] - p1[0]), (p2[1] - p1[1])); l2 = math.hypot(*d2); d2 = (d2[0] / l2, d2[1] / l2)
        convex = d1[0] * d2[1] - d1[1] * d2[0] > 0
        rr = min(r_convex if convex else r_concave, l1 / 2, l2 / 2)
        cmd = "L" if out else "M"
        if rr < 0.01:
            out.append(f"{cmd}{p1[0]:.3f},{p1[1]:.3f}")
            continue
        a = (p1[0] - d1[0] * rr, p1[1] - d1[1] * rr)
        b = (p1[0] + d2[0] * rr, p1[1] + d2[1] * rr)
        out.append(f"{cmd}{a[0]:.3f},{a[1]:.3f} A{rr:.3f},{rr:.3f} 0 0 {1 if convex else 0} {b[0]:.3f},{b[1]:.3f}")
    return " ".join(out) + " Z"


def offset(pts, d):
    """Desloca um polígono ortogonal (horário na tela) para fora (d > 0) ou para dentro."""
    n = len(pts)
    res = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1]); e2 = (p2[0] - p1[0], p2[1] - p1[1])
        n1 = (e1[1] / math.hypot(*e1), -e1[0] / math.hypot(*e1))
        n2 = (e2[1] / math.hypot(*e2), -e2[0] / math.hypot(*e2))
        res.append((p1[0] + (n1[0] + n2[0]) * d, p1[1] + (n1[1] + n2[1]) * d))
    return res


def band_outline(x0, y0, hx, notch):
    """Contorno da faixa (y para baixo: topo da tampa em cima). hx: meia largura livre da dobradiça."""
    L, h, c = LENGTH, BAND_H, notch
    if c <= 0:
        pts = [(0, 0), (L, 0), (L, h), (0, h)]
    else:
        pts = [(0, 0), (L, 0), (L, h - c), (PERIM - hx, h - c), (PERIM - hx, h), (hx, h), (hx, h - c), (0, h - c)]
    return [(x0 + x, y0 + y) for x, y in pts]


def rrect(x, y, w, h, r):
    return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{r:.3f}" ry="{r:.3f}"/>'


def svg(ver):
    hg = HINGE[ver]
    hx = min(hg["half_x"] + CLEAR, FLAT_W / 2)                  # largura do recorte da dobradiça
    notch = max(0.0, hg["top"] + CLEAR - BAND_LO)                 # altura do recorte
    bx, by = 12.0, 32.0                                           # posição da faixa na folha
    band = band_outline(bx, by, hx, notch)
    css = """
    .corte{fill:none;stroke:#e3001b;stroke-width:0.25}
    .sangria{fill:none;stroke:#00a0e3;stroke-width:0.2;stroke-dasharray:1.5 1}
    .segura{fill:none;stroke:#2bb34a;stroke-width:0.2;stroke-dasharray:1 1}
    .guia{fill:none;stroke:#8a8a8a;stroke-width:0.15;stroke-dasharray:0.8 0.8}
    .sobre{fill:#8a8a8a;fill-opacity:0.18;stroke:none}
    text{font-family:Arial,Helvetica,sans-serif;fill:#333}
    .t{font-size:3px}.s{font-size:2.2px;fill:#666}.h{font-size:4.2px;font-weight:bold}.f{font-size:2.6px;fill:#8a8a8a;text-anchor:middle}
    """
    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
             'width="297mm" height="210mm" viewBox="0 0 297 210">')
    L.append(f"<style>{css}</style>")
    L.append('<rect x="0" y="0" width="297" height="210" fill="#fff"/>')
    L.append('<g inkscape:groupmode="layer" inkscape:label="Arte" id="arte"><!-- coloque a arte aqui, até a linha azul --></g>')

    # sangria
    L.append('<g inkscape:groupmode="layer" inkscape:label="Sangria" id="sangria">')
    L.append(f'<path class="sangria" d="{rounded_path(offset(band, BLEED), R_CUT + BLEED, max(R_CUT - BLEED, 0))}"/>')
    tw, th, tr = W - 2 * (TOP_CH + TOP_INSET), D - 2 * (TOP_CH + TOP_INSET), R - TOP_CH - TOP_INSET
    tx, ty = bx, by + BAND_H + 22
    L.append(rrect(tx - BLEED, ty - BLEED, tw + 2 * BLEED, th + 2 * BLEED, tr + BLEED).replace("<rect", '<rect class="sangria"'))
    L.append("</g>")

    # área segura: uma caixa por face plana, fora da dobradiça
    L.append('<g inkscape:groupmode="layer" inkscape:label="Area segura" id="segura">')
    for nome, a, b in FACES:
        if not nome:
            continue
        top, bot = by + SAFE, by + BAND_H - SAFE
        if nome == "TRASEIRA" and notch > 0:
            bot = by + BAND_H - notch - SAFE
        if bot - top > 1:
            L.append(f'<rect class="segura" x="{bx + a + SAFE:.3f}" y="{top:.3f}" width="{b - a - 2 * SAFE:.3f}" height="{bot - top:.3f}"/>')
    L.append(rrect(tx + SAFE, ty + SAFE, tw - 2 * SAFE, th - 2 * SAFE, max(tr - SAFE, 0.5)).replace("<rect", '<rect class="segura"'))
    L.append("</g>")

    # guias: cantos arredondados, centros das faces, sobreposição
    L.append('<g inkscape:groupmode="layer" inkscape:label="Guias" id="guias">')
    for nome, a, b in FACES:
        if nome is None:  # canto arredondado: começo e fim da curva
            for u in (a, b):
                L.append(f'<line class="guia" x1="{bx + u:.3f}" y1="{by - 3:.3f}" x2="{bx + u:.3f}" y2="{by + BAND_H + 3:.3f}"/>')
    for nome, a, b in FACES:
        if nome in ("FRENTE", "LATERAL ESQUERDA", "LATERAL DIREITA"):
            m = bx + (a + b) / 2
            L.append(f'<line class="guia" x1="{m:.3f}" y1="{by - 4:.3f}" x2="{m:.3f}" y2="{by - 1:.3f}"/>')
            L.append(f'<line class="guia" x1="{m:.3f}" y1="{by + BAND_H + 1:.3f}" x2="{m:.3f}" y2="{by + BAND_H + 4:.3f}"/>')
            L.append(f'<text class="f" x="{m:.3f}" y="{by - 5:.3f}">{nome}</text>')
    L.append(f'<text class="f" x="{bx + FLAT_W / 4:.3f}" y="{by - 5:.3f}">TRASEIRA</text>')
    L.append(f'<text class="f" x="{bx + PERIM - FLAT_W / 4:.3f}" y="{by - 5:.3f}">TRASEIRA</text>')
    ov_h = BAND_H - notch
    L.append(f'<rect class="sobre" x="{bx + PERIM:.3f}" y="{by:.3f}" width="{OVERLAP:.3f}" height="{ov_h:.3f}"/>')
    L.append(f'<rect class="sobre" x="{bx:.3f}" y="{by:.3f}" width="{OVERLAP:.3f}" height="{ov_h:.3f}"/>')
    L.append(f'<line class="guia" x1="{bx + PERIM:.3f}" y1="{by - 3:.3f}" x2="{bx + PERIM:.3f}" y2="{by + BAND_H + 3:.3f}"/>')
    L.append(f'<text class="s" x="{bx:.3f}" y="{by + BAND_H + 7:.3f}">começo: meio da traseira (fica por baixo)</text>')
    L.append(f'<text class="s" x="{bx + LENGTH:.3f}" y="{by + BAND_H + 7:.3f}" text-anchor="end">fim: {OVERLAP:g} mm de sobreposição por cima do começo</text>')
    L.append(f'<text class="f" x="{tx + tw / 2:.3f}" y="{ty + th / 2:.3f}">TOPO</text>')
    L.append(f'<text class="f" x="{tx + tw / 2:.3f}" y="{ty + th + 5.5:.3f}">FRENTE (este lado vai para a frente)</text>')
    L.append("</g>")

    # corte
    L.append('<g inkscape:groupmode="layer" inkscape:label="Corte" id="corte">')
    L.append(f'<path class="corte" d="{rounded_path(band, R_CUT)}"/>')
    L.append(rrect(tx, ty, tw, th, tr).replace("<rect", '<rect class="corte"'))
    L.append("</g>")

    # textos e régua
    L.append('<g inkscape:groupmode="layer" inkscape:label="Textos" id="textos">')
    L.append(f'<text class="h" x="12" y="14">Adesivo da tampa — {hg["nome"]}</text>')
    L.append('<text class="t" x="12" y="20">Imprima em TAMANHO REAL (100 %, sem "ajustar à página") e confira a régua de 50 mm.</text>')
    lx, ly = 100, by + BAND_H + 22
    info = [
        f"Faixa: {LENGTH:.1f} × {BAND_H:.1f} mm (contorno {PERIM:.1f} + {OVERLAP:g} de sobreposição)",
        f"Topo: {tw:.1f} × {th:.1f} mm, cantos R{tr:g}",
        "Vermelho = corte · Azul tracejado = sangria (estenda a arte até ela)",
        "Verde tracejado = área segura · Cinza = começo e fim dos cantos arredondados",
        f"Recorte embaixo, na traseira = espaço da dobradiça ({2 * hx:.1f} × {notch:.1f} mm)",
        "Aplicar: comece no meio da traseira, com a borda de cima logo abaixo",
        "do chanfro do topo, e dê a volta; o fim passa por cima do começo.",
        "Use vinil adesivo (fosco ou brilho) e, se possível, laminação por cima.",
    ]
    for i, t in enumerate(info):
        L.append(f'<text class="t" x="{lx}" y="{ly + i * 5:.1f}">{t}</text>')
    rx0, ry0 = lx, ly + len(info) * 5 + 6
    L.append(f'<line x1="{rx0}" y1="{ry0}" x2="{rx0 + 50}" y2="{ry0}" stroke="#000" stroke-width="0.3"/>')
    for k in range(6):
        L.append(f'<line x1="{rx0 + 10 * k}" y1="{ry0 - (2 if k % 5 == 0 else 1.2)}" x2="{rx0 + 10 * k}" y2="{ry0}" stroke="#000" stroke-width="0.2"/>')
    L.append(f'<text class="t" x="{rx0 + 53}" y="{ry0 + 1}">50 mm — confira com uma régua</text>')
    L.append("</g></svg>")
    return "\n".join(L), {"comprimento": LENGTH, "altura": BAND_H, "recorte_larg": 2 * hx, "recorte_alt": notch,
                          "topo": (tw, th, tr), "faixa_acima_dobradica": BAND_H - notch}


if __name__ == "__main__":
    import xml.dom.minidom
    # conferência: contorno da tampa e altura da faixa batem com o modelo
    assert abs(PERIM - 267.533) < 0.01 and abs(BAND_H - 28.5) < 1e-9, (PERIM, BAND_H)
    here = Path(__file__).resolve().parent
    for v in ("A", "B"):
        text, info = svg(v)
        xml.dom.minidom.parseString(text.encode("utf-8"))  # SVG bem formado
        assert info["faixa_acima_dobradica"] > 2, "faixa fina demais acima da dobradiça"
        (here / f"adesivo_tampa_{v}.svg").write_text(text, encoding="utf-8")
        print(v, {k: (round(x, 2) if isinstance(x, float) else tuple(round(y, 2) for y in x)) for k, x in info.items()})
