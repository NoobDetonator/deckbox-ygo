#!/usr/bin/env python3
"""Gera o gabarito de corte do forro interno em SVG (escala 1:1, mm, A4 paisagem).

Peças: fundo, 4 paredes do corpo, teto da tampa e 4 paredes da tampa, para dois tecidos
(feltro de 1 mm e veludo/flocado de 0,5 mm). As medidas vêm do interior da caixa impressa
(cad/*/_build.json). Se você mudar o tamanho da caixa, ajuste aqui e rode de novo:
    python forro/gerar_forro.py
"""
from pathlib import Path

# ---- interior da caixa impressa (mm) ----
IN_X, IN_Y = 66.0, 66.8      # largura e profundidade internas (in_x, in_y)
FLOOR_Z = 2.0                # fundo (base_t)
LIP_TOP = 69.0               # topo do lábio (split + lip_h): aqui ficam os ímãs do corpo
LEDGE = 69.3                 # degrau interno da tampa (split + lip_h + fit): ímãs da tampa
CEIL = 96.5                  # teto da tampa (H - roof_t)
FILLET = 1.0                 # filete do fundo e do teto com as paredes
# ---- regras do forro ----
STOP = 0.5                   # as paredes param antes do lábio / degrau (não cobrir os ímãs)
SIDE_PLAY = 0.4              # um pouco menor que o vão, para não embolar nos cantos
R_CUT = 1.0
TECIDOS = {"feltro_1mm": (1.0, "feltro adesivo de 1 mm"), "veludo_0-5mm": (0.5, "veludo / flocado adesivo de 0,5 mm")}


def pieces(t):
    """(nome, quantidade, largura, altura, nota) de cada peça para um tecido de espessura t."""
    flat_x, flat_y = IN_X - 2 * FILLET, IN_Y - 2 * FILLET            # parte plana do fundo e do teto
    front_w = IN_X - SIDE_PLAY                                       # frente/traseira: largura toda
    side_w = IN_Y - 2 * t - SIDE_PLAY                                # laterais: entre frente e traseira
    body_h = (LIP_TOP - STOP) - (FLOOR_Z + t)                         # do fundo forrado até 0,5 abaixo do lábio
    lid_h = (CEIL - t) - (LEDGE + STOP)                              # do teto forrado até 0,5 acima do degrau
    return [
        ("FUNDO", 1, flat_x, flat_y, "1º: no fundo do corpo"),
        ("CORPO frente/traseira", 2, front_w, body_h, "2º: largura toda"),
        ("CORPO lateral", 2, side_w, body_h, "3º: entre frente e traseira"),
        ("TETO DA TAMPA", 1, flat_x, flat_y, "1º: no teto da tampa"),
        ("TAMPA frente/traseira", 2, front_w, lid_h, "2º: largura toda"),
        ("TAMPA lateral", 2, side_w, lid_h, "3º: entre frente e traseira"),
    ]


def svg(key):
    t, nome_tecido = TECIDOS[key]
    ps = pieces(t)
    css = """
    .corte{fill:none;stroke:#e3001b;stroke-width:0.25}
    text{font-family:Arial,Helvetica,sans-serif;fill:#333}
    .t{font-size:3px}.h{font-size:4.2px;font-weight:bold}.p{font-size:2.8px;fill:#555;text-anchor:middle}.q{font-size:2.3px;fill:#888;text-anchor:middle}
    """
    corte, textos = [], []
    gap, x0 = 3.0, 12.0
    # linha 1: paredes do corpo · linha 2: paredes da tampa · linha 3: fundo e teto + legenda
    rows = [[p for p in ps if p[0].startswith("CORPO")], [p for p in ps if p[0].startswith("TAMPA")],
            [p for p in ps if p[0] in ("FUNDO", "TETO DA TAMPA")]]
    y = 26.0
    for row in rows:
        x, hmax = x0, 0.0
        for nome, qtd, w, h, nota in row:
            for k in range(qtd):
                corte.append(f'<rect class="corte" x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{R_CUT}" ry="{R_CUT}"/>')
                textos.append(f'<text class="p" x="{x + w / 2:.2f}" y="{y + h / 2:.2f}">{nome}</text>')
                textos.append(f'<text class="q" x="{x + w / 2:.2f}" y="{y + h / 2 + 4:.2f}">{w:.1f} × {h:.1f} mm · {nota}</text>')
                x += w + gap
            hmax = max(hmax, h)
        last_x, last_y = x, y
        y += hmax + 7
    assert y <= 210 and all(x0 + sum((p[2] + gap) * p[1] for p in row) <= 297 for row in rows), "não cabe na folha"
    lx, ly = last_x + 8, last_y + 4
    info = [
        f"Tecido: {nome_tecido} (espessura {t:g} mm)",
        f"Interior da caixa: {IN_X:g} × {IN_Y:g} mm",
        "Vermelho = corte. Todas as peças: lado do adesivo para a parede.",
        "Ordem: fundo / teto, depois frente e traseira, por último as laterais.",
        "As paredes param 0,5 mm antes do topo do lábio e do degrau",
        "da tampa: não cubra essas faces, é onde ficam os ímãs.",
        "Sem adesivo no tecido? Use cola spray ou fita dupla face fina.",
    ]
    for i, s in enumerate(info):
        textos.append(f'<text class="t" x="{lx:.1f}" y="{ly + i * 5:.1f}">{s}</text>')
    rx0, ry0 = lx, ly + len(info) * 5 + 6
    textos.append(f'<line x1="{rx0}" y1="{ry0}" x2="{rx0 + 50}" y2="{ry0}" stroke="#000" stroke-width="0.3"/>')
    for k in range(6):
        textos.append(f'<line x1="{rx0 + 10 * k}" y1="{ry0 - (2 if k % 5 == 0 else 1.2)}" x2="{rx0 + 10 * k}" y2="{ry0}" stroke="#000" stroke-width="0.2"/>')
    textos.append(f'<text class="t" x="{rx0 + 53}" y="{ry0 + 1}">50 mm — confira com uma régua</text>')
    textos.append(f'<text class="h" x="12" y="14">Forro interno — {nome_tecido}</text>')
    textos.append('<text class="t" x="12" y="20">Imprima em TAMANHO REAL (100 %, sem "ajustar à página"), recorte as peças e use como molde no tecido.</text>')
    layer = lambda lab, ident, items: f'<g inkscape:groupmode="layer" inkscape:label="{lab}" id="{ident}">' + "\n".join(items) + "</g>"
    doc = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="297mm" height="210mm" viewBox="0 0 297 210">',
           f"<style>{css}</style>", '<rect x="0" y="0" width="297" height="210" fill="#fff"/>',
           layer("Corte", "corte", corte), layer("Textos", "textos", textos), "</svg>"]
    return "\n".join(doc), ps


if __name__ == "__main__":
    import xml.dom.minidom
    here = Path(__file__).resolve().parent
    for key, (t, _) in TECIDOS.items():
        text, ps = svg(key)
        xml.dom.minidom.parseString(text.encode("utf-8"))  # SVG bem formado
        d = {p[0]: p for p in ps}
        # conferência: laterais + forro da frente e da traseira cabem na profundidade; paredes cabem no vão
        assert d["CORPO lateral"][2] + 2 * t <= IN_Y and d["CORPO frente/traseira"][2] <= IN_X
        assert abs(d["CORPO lateral"][3] - (LIP_TOP - STOP - FLOOR_Z - t)) < 1e-9
        (here / f"forro_{key}.svg").write_text(text, encoding="utf-8")
        print(key, [(p[0], p[1], round(p[2], 1), round(p[3], 1)) for p in ps])
