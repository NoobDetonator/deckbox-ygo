#!/usr/bin/env python3
"""Gera cad/token/token_build.json: card Token paramétrico (59 x 86 x 2,8 mm) para o SolidCraft.

    python cad/token/gerar_token.py
    solidcraft-cli run cad/token/token_build.json --save cad/token/token.sc

As cotas principais (card, moldura, janelas, alturas Z, textos, cavidades, entalhes, número de
estrelas) são parâmetros do .sc. Os desenhos finos (estrela, losangos, brasão) acompanham a
posição das janelas, mas a forma deles sai daqui: mude abaixo e gere de novo.
"""
import json
import math
import sys
from pathlib import Path

steps, stages = [], []
FONTE = "Impact"  # pesada e estreita: "ATK / ?" com 3,2 mm cabe ao lado da cavidade de 10 mm


def cmd(c, **p):
    steps.append({"command": c, "params": p})


def stage(nome):
    stages.append((nome, len(steps)))


def par(name, expr, comment, fav=False, **kw):
    cmd("parameters.add", name=name, expression=expr, comment=comment, **({"favorite": True} if fav else {}), **kw)


def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def pt(x, y, ax=None, ay=None):
    """Ponto de esboço; com âncora (parâmetro) o ponto fica fixo e acompanha o parâmetro."""
    sx = f(x) if ax is None else f"{ax} + {f(x)}"
    sy = f(y) if ay is None else f"{ay} + {f(y)}"
    return [sx, sy]


def poly(pts, **kw):
    cmd("sketch.line", points=pts, closed=True, **kw)


def rect(cy, w, h):
    return [[f"-{w}/2", f"{cy} - {h}/2"], [f"{w}/2", f"{cy} - {h}/2"],
            [f"{w}/2", f"{cy} + {h}/2"], [f"-{w}/2", f"{cy} + {h}/2"]]


def sketch(nome, offset):
    cmd("sketch.create", plane="XY", offset=offset, name=nome)


def fim():
    cmd("sketch.finish")


# ---------------- parâmetros ----------------
stage("parametros")
par("W", "59 mm", "largura do card (tamanho japonês)")
par("H", "86 mm", "altura do card")
par("T", "2.8 mm", "espessura total = topo da moldura")
par("r_canto", "2 mm", "raio dos cantos no plano XY")
par("ch_base", "0.4 mm", "chanfro 45° na base, contra pé de elefante", True)
par("borda", "3 mm", "largura da moldura externa, medida no nível da face")
par("z_face", "2 mm", "SUPOSIÇÃO (a spec não diz): nível da face entre as janelas; a moldura desce até aqui num chanfro 45°", True)
par("z_jan", "1.4 mm", "fundo das janelas")
par("z_rel", "2.6 mm", "topo dos relevos (TOKEN, estrelas, ATK/DEF, divisória)")
par("margem", "5 mm", "do título e do status até a borda do card")
par("tit_l", "49 mm", "caixa de título: largura")
par("tit_a", "8 mm", "caixa de título: altura")
par("arte_l", "47 mm", "janela de arte: largura")
par("arte_a", "44 mm", "janela de arte: altura")
par("arte_topo", "20 mm", "do topo do card ao topo da janela de arte")
par("st_l", "49 mm", "caixa de status: largura")
par("st_a", "14 mm", "caixa de status: altura")
par("tok_h", "5 mm", "altura das maiúsculas de TOKEN")
par("stat_h", "3.2 mm", "altura das maiúsculas de ATK / DEF")
par("n_est", "4", "número de estrelas (nível)", True, unit="")
par("est_p", "5.5 mm", "passo entre estrelas")
par("dado_d", "10 mm", "diâmetro das cavidades do dado", True)
par("dado_p", "0.6 mm", "profundidade das cavidades, a partir do fundo da janela")
par("ent_p", "0.4 mm", "profundidade dos entalhes de orientação no topo da moldura")
par("tit_y", "H/2 - margem - tit_a/2", "centro da caixa de título")
par("arte_y", "H/2 - arte_topo - arte_a/2", "centro da janela de arte")
par("st_y", "-(H/2 - margem - st_a/2)", "centro da caixa de status")
par("est_y", "tit_y - tit_a/2 - 3.5 mm", "linha das estrelas")

# valores padrão (para desenhar os detalhes finos nas posições certas)
TIT_L, ARTE_L, ARTE_A = 49, 47, 44

# ---------------- corpo ----------------
stage("corpo")
sketch("Esb_Card", 0)
poly([["-W/2", "-H/2"], ["W/2", "-H/2"], ["W/2", "H/2"], ["-W/2", "H/2"]])
fim()
cmd("solid.extrude", sketch="Esb_Card", distance="T", name="Card", body_name="Token")
cmd("solid.fillet", edges=[[29.5, 43, 1.4], [-29.5, 43, 1.4], [29.5, -43, 1.4], [-29.5, -43, 1.4]],
    radius="r_canto", name="Cantos")
cmd("solid.chamfer", edges=[[0, -43, 0]], distance="ch_base", name="Chanfro_base")

# interior rebaixado até z_face; o taper de 45° faz o chanfro interno da moldura
stage("moldura")
sketch("Esb_Interior", "T")
k = "(borda - (T - z_face))"  # largura da moldura no topo
poly([[f"-(W/2 - {k})", f"-(H/2 - {k})"], [f"W/2 - {k}", f"-(H/2 - {k})"],
      [f"W/2 - {k}", f"H/2 - {k}"], [f"-(W/2 - {k})", f"H/2 - {k}"]])
fim()
cmd("solid.extrude", sketch="Esb_Interior", distance="T - z_face", direction="negative",
    taper="-45 deg", operation="cut", name="Interior")

stage("janelas")
sketch("Esb_Janelas", "z_face")
poly(rect("tit_y", "tit_l", "tit_a"))
poly(rect("arte_y", "arte_l", "arte_a"))
poly(rect("st_y", "st_l", "st_a"))
fim()
cmd("solid.extrude", sketch="Esb_Janelas", distance="z_face - z_jan", direction="negative",
    operation="cut", name="Janelas")

# ---------------- título ----------------
stage("token")
sketch("Esb_TOKEN", "z_jan")
cmd("sketch.text", text="TOKEN", at=["0", "tit_y"], height="tok_h", font=FONTE, align="center",
    vertical_align="middle")
fim()
# letras chanfradas: taper para dentro; corner "round" é o único que fecha o sólido nas curvas da fonte
cmd("solid.extrude", sketch="Esb_TOKEN", distance="z_rel - z_jan", taper="-12 deg", corner="round",
    operation="join", name="TOKEN")

# ---------------- estrelas facetadas ----------------
stage("estrelas")
R, r = 2.25, 1.0  # raio externo (diâmetro 4,5) e interno
est_x = TIT_L / 2 - R  # a da direita alinhada com a caixa de título
star = [pt(est_x + (R if i % 2 == 0 else r) * math.cos(math.radians(90 + 36 * i)) - TIT_L / 2,
           (R if i % 2 == 0 else r) * math.sin(math.radians(90 + 36 * i)), "tit_l/2", "est_y")
        for i in range(10)]
sketch("Esb_Estrela", "z_rel - 0.4 mm")
poly(star)
fim()
cmd("solid.extrude", sketch="Esb_Estrela", distance="z_rel - 0.4 mm - z_face", direction="negative",
    operation="join", name="Estrela_base")
sketch("Esb_Estrela_apice", "z_rel")
cmd("sketch.point", point=pt(est_x - TIT_L / 2, 0, "tit_l/2", "est_y"))
fim()
cmd("solid.loft", sections=[{"sketch": "Esb_Estrela"}, {"sketch": "Esb_Estrela_apice", "point": "p1"}],
    operation="join", name="Estrela_facetas")
cmd("solid.pattern.rectangular", features=["Estrela_base", "Estrela_facetas"], dir1=[-1, 0, 0],
    count1="n_est", spacing1="est_p", name="Estrelas")

# ---------------- janela de arte: losangos ----------------
stage("losangos")
PASSO, EXT = 4.0, 0.3  # passo entre nervuras; quanto entram na parede da janela
hx, hy = ARTE_L / 2 + EXT, ARTE_A / 2 + EXT


def clip(p, d):
    """Trecho da reta p + t*d dentro do retângulo |x|<=hx, |y|<=hy (Liang-Barsky)."""
    t0, t1 = -1e9, 1e9
    for pi, di, h in ((p[0], d[0], hx), (p[1], d[1], hy)):
        a, b = (-h - pi) / di, (h - pi) / di
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return None if t1 - t0 < 1.0 else [(p[0] + t * d[0], p[1] + t * d[1]) for t in (t0, t1)]


sketch("Esb_Losangos", "z_jan")
s = math.sqrt(0.5)
for d, n in (((s, s), (-s, s)), ((s, -s), (s, s))):
    for i in range(-20, 21):
        seg = clip((n[0] * i * PASSO, n[1] * i * PASSO), d)
        if seg:
            cmd("sketch.line", points=[pt(x, y, None, "arte_y") for x, y in seg], connect=False)
fim()
cmd("solid.extrude", sketch="Esb_Losangos", thin=True, thickness="0.8 mm", distance="0.3 mm",
    operation="join", name="Losangos")

# ---------------- brasão: olho de dragão num anel octogonal ----------------
stage("brasao")


def octo(apotema):
    rc = apotema / math.cos(math.radians(22.5))
    return [pt(rc * math.cos(math.radians(22.5 + 45 * i)), rc * math.sin(math.radians(22.5 + 45 * i)),
               None, "arte_y") for i in range(8)]


sketch("Esb_Brasao", "z_jan")
poly(octo(14.0))
poly(octo(12.4))
fim()
cmd("solid.extrude", sketch="Esb_Brasao", profiles=[{"point": [0, 1 + 13.2]}], distance="T - z_jan",
    operation="join", name="Brasao_anel")
cmd("solid.extrude", sketch="Esb_Brasao", profiles=[{"point": [0, 1]}], distance="0.4 mm",
    operation="join", name="Brasao_base")

sketch("Esb_Olho", "z_jan + 0.4 mm")
cmd("sketch.arc.three_point", start=pt(-10.5, 0, None, "arte_y"), end=pt(10.5, 0, None, "arte_y"),
    through=pt(0, 5, None, "arte_y"))
cmd("sketch.arc.three_point", start=pt(-10.5, 0, None, "arte_y"), end=pt(10.5, 0, None, "arte_y"),
    through=pt(0, -5, None, "arte_y"))
fim()
cmd("solid.extrude", sketch="Esb_Olho", distance="0.3 mm", operation="join", name="Olho")

sketch("Esb_Iris", "z_jan + 0.7 mm")
cmd("sketch.circle.center", center=["0", "arte_y"], radius=4.2)
cmd("sketch.dimension", entities=["c1"], type="diameter", value="8.4 mm")
fim()
cmd("solid.extrude", sketch="Esb_Iris", distance="0.4 mm", operation="join", name="Iris")

sketch("Esb_Pupila", "z_jan + 1.1 mm")
cmd("sketch.arc.three_point", start=pt(0, -3.8, None, "arte_y"), end=pt(0, 3.8, None, "arte_y"),
    through=pt(1.0, 0, None, "arte_y"))
cmd("sketch.arc.three_point", start=pt(0, -3.8, None, "arte_y"), end=pt(0, 3.8, None, "arte_y"),
    through=pt(-1.0, 0, None, "arte_y"))
fim()
cmd("solid.extrude", sketch="Esb_Pupila", distance="0.4 mm", direction="negative", operation="cut",
    name="Pupila")

# ---------------- status: ATK / DEF, divisória e cavidades ----------------
stage("status")
sketch("Esb_Status", "z_jan")
cmd("sketch.text", text="ATK / ?", at=["-(st_l/2 - 1.9 mm - dado_d)", "st_y"], height="stat_h",
    font=FONTE, align="left", vertical_align="middle")
cmd("sketch.text", text="DEF / ?", at=["st_l/2 - 1.9 mm - dado_d", "st_y"], height="stat_h",
    font=FONTE, align="right", vertical_align="middle")
fim()
cmd("solid.extrude", sketch="Esb_Status", distance="z_rel - z_jan", operation="join", name="ATK_DEF")
cmd("solid.box", center=["0", "st_y", "(z_jan + z_rel)/2"], length="0.8 mm", width="st_a - 3 mm",
    height="z_rel - z_jan", operation="join", name="Divisoria")
for nome, sx in (("Dado_ATK", "-"), ("Dado_DEF", "")):
    cmd("solid.cylinder", base=[f"{sx}(st_l/2 - 0.9 mm - dado_d/2)", "st_y", "z_jan - dado_p"],
        diameter="dado_d", height="dado_p + 0.4 mm", operation="cut", name=nome)

# ---------------- entalhes de orientação no topo da moldura ----------------
stage("entalhes")
sketch("Esb_Entalhes", "T")
poly([["0", "H/2 - 0.5 mm"], ["-1.1", "H/2 - 2 mm"], ["1.1", "H/2 - 2 mm"]])  # ataque: aponta pra cima
for sx in ("", "-"):  # defesa: apontam para os lados (viram "pra cima" com o card deitado)
    poly([[f"{sx}(W/2 - 0.5 mm)", "arte_y"], [f"{sx}(W/2 - 2 mm)", "arte_y + 1.1"],
          [f"{sx}(W/2 - 2 mm)", "arte_y - 1.1"]])
fim()
cmd("solid.extrude", sketch="Esb_Entalhes", distance="ent_p", direction="negative", operation="cut",
    name="Entalhes")

# ---------------- saída ----------------
here = Path(__file__).resolve().parent
(here / "token_build.json").write_text(
    "{\"commands\": [\n" + ",\n".join(" " + json.dumps(s, ensure_ascii=False) for s in steps) + "\n]}\n",
    encoding="utf-8")
if len(sys.argv) > 1:  # etapas separadas, para testar uma de cada vez: gerar_token.py <pasta>
    out = Path(sys.argv[1])
    bounds = [i for _, i in stages] + [len(steps)]
    for k, (nome, a) in enumerate(stages):
        (out / f"{k:02d}_{nome}.json").write_text(json.dumps({"commands": steps[a:bounds[k + 1]]},
                                                             ensure_ascii=False), encoding="utf-8")
print(len(steps), "passos")
