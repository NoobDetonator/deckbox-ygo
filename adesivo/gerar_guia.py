#!/usr/bin/env python3
"""Gera o gabarito do adesivo da tampa em SVG (escala 1:1, mm, A4 paisagem).

Uma faixa para as 4 laterais (emendas escondidas na traseira, com sobreposição) e uma peça
para o topo, para as versões A e B. Se a faixa não cabe na folha, ela sai em duas partes.
As medidas vêm dos parâmetros do modelo em cad/*/_build.json: se você mudar o tamanho da
caixa, ajuste aqui e rode de novo:  python adesivo/gerar_guia.py
"""
import math
from pathlib import Path

# ---- medidas do modelo (mm) ----
W, D = 71.6, 78.6            # largura e profundidade externas (W = in_x + 2*wall, D = in_y + wall + wall_front)
R = 4.0                      # raio dos cantos verticais (r_out)
TOP_CH, REVEAL = 1.0, 0.4    # chanfro do topo da tampa / chanfro na linha de divisão
LID_H = 34.5                 # altura da tampa (H - split)
# parte da traseira ocupada pela dobradiça: meia largura e altura acima da divisão
HINGE = {
    "A": {"half_x": W / 2 - R, "top": 4.64,   # nós + reforços a 45° da dobradiça integrada
          "nome": "versão A (dobradiça integrada)"},
    "B": {"half_x": 28.2, "top": 25.2,        # ressalto da dobradiça colada (pad_l/2, pad_h + pad_t)
          "nome": "versão B (dobradiça colada)"},
}
# ---- folgas do adesivo e folha ----
MARGIN = 0.3      # longe das quinas dos chanfros, para a borda não levantar
CLEAR = 0.5       # folga em volta da dobradiça
OVERLAP = 5.0     # cada emenda passa 5 mm por cima
BLEED = 2.0       # sangria: estenda a arte até aqui
SAFE = 2.0        # área segura: textos e detalhes importantes dentro dela
TOP_INSET = 0.5   # peça do topo um pouco menor que a face plana
R_CUT = 1.0       # cantos arredondados no recorte (o adesivo não rasga nem levanta)
SHEET_W, SHEET_MARGIN = 297.0, 10.0

FLAT_W, FLAT_D = W - 2 * R, D - 2 * R
ARC = math.pi * R / 2
PERIM = 2 * (FLAT_W + FLAT_D) + 4 * ARC
BAND_LO = REVEAL + MARGIN                 # borda de baixo, acima da divisão
BAND_HI = LID_H - TOP_CH - MARGIN         # borda de cima
BAND_H = BAND_HI - BAND_LO
LENGTH = PERIM + OVERLAP

# a faixa começa no meio da traseira e segue para a esquerda de quem olha a traseira
FACES = []  # (nome, início, fim) ao longo da faixa; None = canto arredondado
s = 0.0
for nome, comp in [("TRASEIRA", FLAT_W / 2), (None, ARC), ("LATERAL ESQUERDA", FLAT_D), (None, ARC),
                   ("FRENTE", FLAT_W), (None, ARC), ("LATERAL DIREITA", FLAT_D), (None, ARC),
                   ("TRASEIRA", FLAT_W / 2), ("TRASEIRA", OVERLAP)]:
    FACES.append((nome, s, s + comp))
    s += comp


def pieces():
    """Uma peça se couber na folha; senão duas, com a segunda emenda no canto traseiro direito."""
    room = SHEET_W - 2 * SHEET_MARGIN - 2 * BLEED
    if LENGTH <= room:
        return [(0.0, LENGTH)]
    s1 = PERIM - FLAT_W / 2
    assert s1 <= room, "nem a parte 1 cabe na folha"
    return [(0.0, s1), (s1 - OVERLAP, LENGTH)]


def piece_outline(a, b, notches, c):
    """Contorno (horário na tela, y para baixo) do trecho [a, b] da faixa, com os recortes embaixo."""
    cuts = sorted({a, b} | {e for n in notches for e in n if a < e < b})
    level = lambda m: BAND_H - c if any(lo <= m <= hi for lo, hi in notches) else BAND_H
    pts = [(a, 0.0), (b, 0.0)]
    for i in range(len(cuts) - 1, 0, -1):
        lv = level((cuts[i - 1] + cuts[i]) / 2)
        pts += [(cuts[i], lv), (cuts[i - 1], lv)]
    clean = []
    for p in pts:                                   # tira pontos repetidos
        if not clean or abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    if abs(clean[0][0] - clean[-1][0]) < 1e-9 and abs(clean[0][1] - clean[-1][1]) < 1e-9:
        clean.pop()
    out = []                                        # tira pontos no meio de um lado reto
    n = len(clean)
    for i in range(n):
        p0, p1, p2 = clean[i - 1], clean[i], clean[(i + 1) % n]
        if (abs(p0[0] - p1[0]) < 1e-9 and abs(p1[0] - p2[0]) < 1e-9) or (abs(p0[1] - p1[1]) < 1e-9 and abs(p1[1] - p2[1]) < 1e-9):
            continue
        out.append(p1)
    return out


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


def rrect(x, y, w, h, r, cls):
    return f'<rect class="{cls}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{r:.3f}" ry="{r:.3f}"/>'


def svg(ver):
    hg = HINGE[ver]
    hx = min(hg["half_x"] + CLEAR, FLAT_W / 2)                   # meia largura do recorte da dobradiça
    notch = max(0.0, hg["top"] + CLEAR - BAND_LO)                 # altura do recorte
    notches = [(0.0, hx), (PERIM - hx, LENGTH)] if notch > 0 else []
    parts = pieces()
    css = """
    .corte{fill:none;stroke:#e3001b;stroke-width:0.25}
    .sangria{fill:none;stroke:#00a0e3;stroke-width:0.2;stroke-dasharray:1.5 1}
    .segura{fill:none;stroke:#2bb34a;stroke-width:0.2;stroke-dasharray:1 1}
    .guia{fill:none;stroke:#8a8a8a;stroke-width:0.15;stroke-dasharray:0.8 0.8}
    .sobre{fill:#8a8a8a;fill-opacity:0.18;stroke:none}
    text{font-family:Arial,Helvetica,sans-serif;fill:#333}
    .t{font-size:3px}.s{font-size:2.2px;fill:#666}.h{font-size:4.2px;font-weight:bold}.f{font-size:2.6px;fill:#8a8a8a;text-anchor:middle}
    .n{font-size:5px;font-weight:bold;fill:#e3001b}
    """
    tw, th, tr = W - 2 * (TOP_CH + TOP_INSET), D - 2 * (TOP_CH + TOP_INSET), R - TOP_CH - TOP_INSET
    bx = 12.0
    rows = [32.0, 32.0 + BAND_H + 18.0]
    place = [(bx, rows[0])] + [(bx, rows[1])] * (len(parts) - 1)
    tx = bx + (parts[1][1] - parts[1][0] + 15 if len(parts) > 1 else 0)
    ty = rows[1] if len(parts) > 1 else rows[0] + BAND_H + 22
    sang, segura, guias, corte, textos = [], [], [], [], []

    for k, ((a, b), (px, py)) in enumerate(zip(parts, place)):
        X = lambda u: px + (u - a)                                # posição na folha de um ponto da faixa
        outline = [(X(u), py + v) for u, v in piece_outline(a, b, notches, notch)]
        corte.append(f'<path class="corte" d="{rounded_path(outline, R_CUT)}"/>')
        sang.append(f'<path class="sangria" d="{rounded_path(offset(outline, BLEED), R_CUT + BLEED, max(R_CUT - BLEED, 0))}"/>')
        for nome, fa, fb in FACES:
            lo, hi = max(fa, a), min(fb, b)
            if hi - lo < 1e-6:
                continue
            if nome is None:                                      # canto arredondado: começo e fim
                for u in (fa, fb):
                    if a <= u <= b:
                        guias.append(f'<line class="guia" x1="{X(u):.3f}" y1="{py - 3:.3f}" x2="{X(u):.3f}" y2="{py + BAND_H + 3:.3f}"/>')
                continue
            bot = BAND_H - SAFE - (notch if nome == "TRASEIRA" and notch > 0 else 0)
            if hi - lo > 2 * SAFE + 1 and bot - SAFE > 1:
                segura.append(f'<rect class="segura" x="{X(lo) + SAFE:.3f}" y="{py + SAFE:.3f}" width="{hi - lo - 2 * SAFE:.3f}" height="{bot - SAFE:.3f}"/>')
            if hi - lo > 12:
                guias.append(f'<text class="f" x="{X((lo + hi) / 2):.3f}" y="{py - 5:.3f}">{nome}</text>')
        # sobreposições: o que fica por baixo e o que passa por cima
        for lo, hi in [(0, OVERLAP), (PERIM, LENGTH)] + ([(parts[0][1] - OVERLAP, parts[0][1])] if len(parts) > 1 else []):
            lo2, hi2 = max(lo, a), min(hi, b)
            if hi2 - lo2 > 1e-6:
                lvl = BAND_H - (notch if any(n0 <= (lo2 + hi2) / 2 <= n1 for n0, n1 in notches) else 0)
                guias.append(f'<rect class="sobre" x="{X(lo2):.3f}" y="{py:.3f}" width="{hi2 - lo2:.3f}" height="{lvl:.3f}"/>')
        if len(parts) > 1:
            textos.append(f'<text class="n" x="{px - 1:.3f}" y="{py - 4.5:.3f}" text-anchor="end">{k + 1}</text>')

    textos.append(f'<text class="s" x="{bx:.3f}" y="{rows[0] + BAND_H + 7:.3f}">começo: meio da traseira (fica por baixo)</text>')
    if len(parts) > 1:
        textos.append(f'<text class="s" x="{bx:.3f}" y="{rows[1] + BAND_H + 7:.3f}">parte 2: cole por último;</text>')
        textos.append(f'<text class="s" x="{bx:.3f}" y="{rows[1] + BAND_H + 10:.3f}">as pontas passam {OVERLAP:g} mm por cima da parte 1</text>')
    else:
        textos.append(f'<text class="s" x="{bx + LENGTH:.3f}" y="{rows[0] + BAND_H + 7:.3f}" text-anchor="end">fim: {OVERLAP:g} mm de sobreposição por cima do começo</text>')

    sang.append(rrect(tx - BLEED, ty - BLEED, tw + 2 * BLEED, th + 2 * BLEED, tr + BLEED, "sangria"))
    segura.append(rrect(tx + SAFE, ty + SAFE, tw - 2 * SAFE, th - 2 * SAFE, max(tr - SAFE, 0.5), "segura"))
    corte.append(rrect(tx, ty, tw, th, tr, "corte"))
    guias.append(f'<text class="f" x="{tx + tw / 2:.3f}" y="{ty + th / 2:.3f}">TOPO</text>')
    guias.append(f'<text class="f" x="{tx + tw / 2:.3f}" y="{ty + th + 5.5:.3f}">FRENTE (este lado vai para a frente)</text>')

    lx, ly = tx + tw + 14, ty + 4
    info = [
        f"Faixa: contorno {PERIM:.1f} mm × {BAND_H:.1f} mm de altura" + (f", em {len(parts)} partes" if len(parts) > 1 else f" + {OVERLAP:g} de sobreposição"),
        f"Topo: {tw:.1f} × {th:.1f} mm, cantos R{tr:g}",
        "Vermelho = corte · Azul tracejado = sangria (estenda a arte até ela)",
        "Verde tracejado = área segura · Cinza = cantos arredondados",
        f"Recorte embaixo, na traseira = espaço da dobradiça ({2 * hx:.1f} × {notch:.1f} mm)",
        "Aplicar: topo primeiro; depois a faixa, começando no meio da",
        "traseira, com a borda de cima logo abaixo do chanfro do topo.",
        "Use vinil adesivo (fosco ou brilho) e, se possível, laminação.",
    ]
    for i, t in enumerate(info):
        textos.append(f'<text class="t" x="{lx:.1f}" y="{ly + i * 5:.1f}">{t}</text>')
    rx0, ry0 = lx, ly + len(info) * 5 + 6
    textos.append(f'<line x1="{rx0}" y1="{ry0}" x2="{rx0 + 50}" y2="{ry0}" stroke="#000" stroke-width="0.3"/>')
    for k in range(6):
        textos.append(f'<line x1="{rx0 + 10 * k}" y1="{ry0 - (2 if k % 5 == 0 else 1.2)}" x2="{rx0 + 10 * k}" y2="{ry0}" stroke="#000" stroke-width="0.2"/>')
    textos.append(f'<text class="t" x="{rx0 + 53}" y="{ry0 + 1}">50 mm — confira com uma régua</text>')
    textos.append(f'<text class="h" x="12" y="14">Adesivo da tampa — {hg["nome"]}</text>')
    textos.append('<text class="t" x="12" y="20">Imprima em TAMANHO REAL (100 %, sem "ajustar à página") e confira a régua de 50 mm.</text>')

    layer = lambda lab, ident, items: f'<g inkscape:groupmode="layer" inkscape:label="{lab}" id="{ident}">' + "\n".join(items) + "</g>"
    doc = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="297mm" height="210mm" viewBox="0 0 297 210">',
           f"<style>{css}</style>", '<rect x="0" y="0" width="297" height="210" fill="#fff"/>',
           layer("Arte", "arte", ["<!-- coloque a arte aqui, até a linha azul -->"]),
           layer("Sangria", "sangria", sang), layer("Area segura", "segura", segura), layer("Guias", "guias", guias),
           layer("Corte", "corte", corte), layer("Textos", "textos", textos), "</svg>"]
    return "\n".join(doc), {"partes": [round(b - a, 2) for a, b in parts], "altura": BAND_H, "recorte": (2 * hx, notch),
                            "topo": (tw, th, tr), "faixa_acima_dobradica": BAND_H - notch}


if __name__ == "__main__":
    import xml.dom.minidom
    assert abs(PERIM - (2 * (W + D) - 8 * R + 2 * math.pi * R)) < 1e-9
    here = Path(__file__).resolve().parent
    for v in ("A", "B"):
        text, info = svg(v)
        xml.dom.minidom.parseString(text.encode("utf-8"))  # SVG bem formado
        assert info["faixa_acima_dobradica"] > 2, "faixa fina demais acima da dobradiça"
        assert all(p <= SHEET_W - 2 * SHEET_MARGIN - 2 * BLEED for p in info["partes"]), "parte maior que a folha"
        (here / f"adesivo_tampa_{v}.svg").write_text(text, encoding="utf-8")
        print(v, info)
