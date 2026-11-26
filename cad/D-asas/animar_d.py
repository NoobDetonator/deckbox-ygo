#!/usr/bin/env python3
"""GIFs da caixa D: montagem passo a passo (images/D/D_montagem.gif) e funcionamento (images/D/D_funcionando.gif).
    python cad/D-asas/animar_d.py [--export]      # precisa do D_asas.sc (ver NOTAS.md) e do Blender
1. exporta cada peca do .sc em STL na posicao montada (cache em %TEMP%/D_anim; --export refaz);
2. calcula a pose de cada peca quadro a quadro com a mesma cinematica do modelo (travel, lift, giro das portas);
3. o Blender (blender_d.py) renderiza os quadros; aqui eles ganham fundo, legenda e o selo de cola, e viram GIF.
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
import gerar_d as d  # noqa: E402  (reescreve os JSON com o mesmo conteudo)
import geo_d as g  # noqa: E402

HERE = Path(__file__).resolve().parent
IMG = HERE.parent.parent / "images" / "D"
WORK = Path(tempfile.gettempdir()) / "D_anim"
from geo_d import CLI  # noqa: E402  (SOLIDCRAFT_CLI ou o primeiro caminho conhecido que existir)
BLENDER = next((b for b in (os.environ.get("BLENDER", ""), *(f"C:/Program Files/Blender Foundation/Blender {v}/blender.exe"
                                                           for v in ("5.3", "5.2", "4.4"))) if b and os.path.exists(b)), "blender")
FONT, FONT_B = "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"

P, p = g.P, g.p
XP, ZS, Dh = g.XP, g.ZS, p["Dh"]
OPEN = P["th_rest"]
COLORS = {"Base": "#1c2331", "DoorL": "#c9a227", "DoorR": "#c9a227", "Tray": "#7a2230", "Deck": "#e8e2d0",
          "RackF": "#c0c6cc", "RackB": "#c0c6cc", "HingeLA": "#3a4560", "HingeRA": "#3a4560", "HingeLB": "#e08a1e", "HingeRB": "#e08a1e",
          **{f"Plate{s}{f}": "#9aa3ad" for s in "LR" for f in "FB"}}
SIDE = {"L": -1, "R": 1}

# ---------------- extras: imas (1 por placa, na face da emenda) e pinos colados das placas (2 por placa) ----------------
EXTRAS, GROUPS = [], {b: [b] for b in COLORS}
SIDE_OF = {"DoorL": -1, "DoorR": 1, "HingeLB": -1, "HingeRB": 1, **{f"Plate{s}{f}": sg for s, sg in SIDE.items() for f in "FB"}}
PIN = d.PIN
for s, sg in SIDE.items():
    for f, fy in (("F", -1), ("B", 1)):
        ym = fy * (p["y_bi"] + p["y_bo"]) / 2
        name = f"Mag{s}{f}"
        EXTRAS.append(dict(name=name, group=name, kind="cyl", r=2.0, h=2.0, axis="X", color="#3b4048",
                           center=[sg * (-g.X_SEAM + 1.15), ym, g.Z_MAG]))   # 0,15 abaixo da face da emenda
        GROUPS[name], SIDE_OF[name] = [name], sg
        for k, (sx, sz) in enumerate(d.SCREW):
            grp = f"Pino{s}{f}{k}"
            y_face = fy * Dh                     # cabeca rente no rebaixo, haste pela parede ate 4 mm dentro da placa
            EXTRAS += [dict(name=grp + "h", group=grp, kind="cyl", r=PIN["head"] / 2, h=PIN["head_t"], axis="Y",
                            color="#e3bd45", center=[sg * sx, y_face - fy * PIN["head_t"] / 2, sz]),
                       dict(name=grp + "s", group=grp, kind="cyl", r=PIN["d"] / 2, h=PIN["l"], axis="Y",
                            color="#e3bd45", center=[sg * sx, y_face - fy * (PIN["head_t"] + PIN["l"] / 2), sz])]
            GROUPS[grp], SIDE_OF[grp] = [grp + "h", grp + "s"], sg

PLATES = [f"Plate{s}{f}" for s in "LR" for f in "FB"]
MAGS = [f"Mag{s}{f}" for s in "LR" for f in "FB"]
SCREWS = [f"Pino{s}{f}{k}" for s in "LR" for f in "FB" for k in range(len(d.SCREW))]
CORE = ["Tray", "RackF", "RackB"] + PLATES + MAGS
HINGES = ["HingeLA", "HingeLB", "HingeRA", "HingeRB"]


def side_of(name):
    return SIDE_OF[name]


def mech(t):
    """Poses do mecanismo com as portas a t graus (mesma cinematica do gerar_d.pose)."""
    out = {}
    for grp in ["DoorL", "DoorR", "HingeLB", "HingeRB"] + PLATES + MAGS + SCREWS:
        s = side_of(grp)
        # como no gerar_d.pose: esquerda -t em Y, direita +t (regra da mao direita: as duas sobem por fora)
        out[grp] = {"rot": s * t, "pivot": [s * XP, ZS]}
    for r in ("RackF", "RackB"):
        out[r] = {"t": [0, 0, g.travel(t)]}
    for u in ("Tray", "Deck"):
        out[u] = {"t": [0, 0, g.lift(t)]}
    return out


def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * u)


def moved(groups, v, u):
    """Grupos deslocados de v * (1 - u): chegam ao lugar em u = 1."""
    k = 1 - ease(u)
    return {grp: {"t": [v[0] * k, v[1] * k, v[2] * k]} for grp in groups}


def objs(groups):
    return [o for grp in groups for o in GROUPS[grp]]


# ---------------- roteiro da montagem ----------------
# (legenda, cola?, quadros, funcao u -> (grupos visiveis, poses), camera)
def s1(u):
    pose = {}
    for grp in PLATES:
        pose[grp] = {"t": [side_of(grp) * 14, 0, 0]}
    k = 1 - ease(u)
    for grp in MAGS:
        s = side_of(grp)
        pose[grp] = {"t": [s * 14 - s * 10 * k, 0, 16 * k]}
    return PLATES + MAGS, pose


def s3(u):
    pose = moved([x for x in PLATES + MAGS if x.endswith("F")], (0, -75, 0), u)
    pose.update(moved([x for x in PLATES + MAGS if x.endswith("B")], (0, 75, 0), u))
    return ["Tray", "RackF", "RackB"] + PLATES + MAGS, pose


def s7(u):
    pose = moved([x for x in SCREWS if x[5] == "F"], (0, -22, 0), u)
    pose.update(moved([x for x in SCREWS if x[5] == "B"], (0, 22, 0), u))
    return ["Base", "DoorL", "DoorR"] + CORE + SCREWS, pose


def s_hinge(u):
    pose = moved(["HingeLA", "HingeLB"], (-45, 0, 0), u)
    pose.update(moved(["HingeRA", "HingeRB"], (45, 0, 0), u))
    return ["Base", "DoorL", "DoorR"] + CORE + SCREWS + HINGES, pose


ALL = ["Base", "DoorL", "DoorR"] + HINGES + CORE + SCREWS
STEPS = [
    ("1 · Ímãs: 1 por placa, no rasgo da face da emenda, com uma gota de super bonder. Antes de colar, encoste a placa da "
     "esquerda na da direita (frente com frente, trás com trás) para conferir a polaridade.", True, 16, s1, "close"),
    ("2 · Cremalheiras no berço: entram por baixo no trilho em cauda de andorinha (o rasgo é aberto só em cima). "
     "Sem cola: elas correm 6,6 mm no trilho antes de levantar o berço.", False, 16,
     lambda u: (["Tray", "RackF", "RackB"], moved(["RackF", "RackB"], (0, 0, -80), u)), "mid"),
    ("3 · Placas: deslize cada par de lado, no sentido dos dentes, até o engate da emenda fechar. O dente de cima "
     "do setor vai no 1º vão da cremalheira (contando de cima).", False, 18, s3, "iso"),
    ("4 · Desça o conjunto na base, fechado. A nervura da cremalheira de trás passa pelo ressalto da trava (clique).",
     False, 16, lambda u: (["Base"] + CORE, moved(CORE, (0, 0, 95), u)), "iso"),
    ("5 · Portas: encaixe cada uma por cima, fechada. As placas entram nela e encostam no teto e na lateral "
     "da porta.", False, 16,
     lambda u: (["Base", "DoorL", "DoorR"] + CORE, moved(["DoorL", "DoorR"], (0, 0, 60), u)), "iso"),
    ("6 · Pinos das placas, ainda secos: 2 por placa, entram por fora pela parede da porta (frente e trás) e a "
     "cabeça fica rente no rebaixo. A cola vem só depois do teste.", False, 18, s7, "pins"),
    ("7 · Dobradiças: com a caixa fechada, encaixe cada uma nos rebaixos (os 4 nós do lado da base). Teste "
     "prendendo com fita crepe; depois cole as abas com pouco super bonder, longe dos nós.", True, 18, s_hinge, "hinge"),
]


def open_close(u, a, b):
    t = a + (b - a) * ease(u)
    return ALL + ["Deck"] * (a != 0 or b != OPEN), mech(t)


def deck_in(u):
    pose = mech(OPEN)
    pose["Deck"] = {"t": [0, 0, g.lift(OPEN) + 80 * (1 - ease(u))]}
    return ALL + ["Deck"], pose


FINAL = ("8 · Pronto: abra (as portas vêm juntas e o berço sobe 36 mm), coloque as cartas e feche. Deu certo? Uma "
         "gota de super bonder em cada pino das placas e os pés de silicone no fundo.", False)
STEPS += [(*FINAL, 18, lambda u: open_close(u, 0, OPEN), "iso"), (*FINAL, 14, deck_in, "iso"),
          (*FINAL, 18, lambda u: open_close(u, OPEN, 0), "iso")]


def cam(yaw, pitch, target, scale, res):
    eye = [target[0] - 900 * math.sin(yaw) * math.cos(pitch), target[1] - 900 * math.cos(yaw) * math.cos(pitch),
           target[2] + 900 * math.sin(pitch)]
    return {"eye": eye, "target": target, "ortho_scale": scale, "res": res}


CAMERAS = {"iso": cam(-0.55, 0.42, [0, 0, 62], 270, [840, 600]),
           "close": cam(-0.35, 0.3, [0, 0, 58], 175, [840, 600]),
           "mid": cam(-0.55, 0.42, [0, 0, 30], 200, [840, 600]),
           "pins": cam(-0.4, 0.22, [12, -Dh, 76], 105, [840, 600]),
           "hinge": cam(1.0, 0.3, [-28, 0, 55], 200, [840, 600]),
           "work_iso": cam(-0.55, 0.42, [0, 0, 78], 215, [620, 620]),
           "work_cut": {"eye": [0, -900, 72], "target": [0, 0, 72], "ortho_scale": 175, "res": [620, 620]}}
CUT_Y = p["y_co"] + P["rail_clr"] / 2
CUT_BODIES = ["Base", "DoorL", "DoorR", "Tray"]
BACK = ["PlateLB", "PlateRB", "RackB", "MagLB", "MagRB"]


def build_frames():
    frames, meta = [], []                       # meta: (gif, legenda, cola, duracao)
    for k, (cap, glue, n, fn, cm) in enumerate(STEPS):
        for i in range(n + 1):
            if i == 0 and k and STEPS[k - 1][0] == cap:
                continue                         # o passo 8 continua do quadro anterior
            vis, pose = fn(i / n)
            out = WORK / "frames" / f"m{len(frames):04d}.png"
            frames.append({"cam": cm, "visible": objs(vis), "poses": pose, "out": str(out)})
            hold = i == n and (k + 1 == len(STEPS) or STEPS[k + 1][0] != cap)
            meta.append(("montagem", out, cap, glue, 2600 if hold else (900 if i == 0 else 70)))
    angles = [OPEN * ease(i / 28) for i in range(29)]
    angles += angles[::-1][1:]
    for i, t in enumerate(angles):
        pose = mech(t)
        a = WORK / "frames" / f"w{i:03d}a.png"
        b = WORK / "frames" / f"w{i:03d}b.png"
        frames.append({"cam": "work_iso", "visible": objs(ALL) + ["Deck"], "poses": pose, "out": str(a)})
        frames.append({"cam": "work_cut", "visible": [x + "_cut" for x in CUT_BODIES] + objs(BACK), "poses": pose,
                       "out": str(b)})
        dur = 1500 if i in (0, 28) else 70
        meta.append(("funcionando", (a, b), t, None, dur))
    return frames, meta


def export_stls():
    stl = WORK / "stl"
    stl.mkdir(parents=True, exist_ok=True)
    bodies = list(COLORS)
    if "--export" not in sys.argv and all((stl / f"{b}.stl").exists() for b in bodies):
        return stl
    cmds = [{"command": "file.export_stl", "params": {"path": str(stl / f"{b}.stl"), "bodies": [b], "quality": "fine"}}
            for b in bodies]
    script = WORK / "export.json"
    script.write_text(json.dumps({"commands": cmds}), encoding="utf-8")
    r = subprocess.run([CLI, "run", str(script), "--in", str(HERE / "D_asas.sc"), "--quiet"], capture_output=True,
                       text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    if r.returncode:
        sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    return stl


# ---------------- composicao ----------------
def background(w, h):
    bg = Image.new("RGB", (w, h))
    dr = ImageDraw.Draw(bg)
    for y in range(h):
        c = [int(a + (b - a) * y / h) for a, b in zip((240, 243, 248), (206, 212, 223))]
        dr.line([(0, y), (w, y)], fill=tuple(c))
    return bg


def wrap(text, font, width, dr):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if dr.textlength(test, font=font) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = test
    return lines + [cur]


def caption_frame(render, cap, glue):
    im = Image.open(render).convert("RGBA")
    w, h = im.size
    bar = 92
    out = background(w, h + bar)
    out.paste(im, (0, 0), im)
    dr = ImageDraw.Draw(out)
    dr.rectangle([0, h, w, h + bar], fill=(28, 35, 49))
    f, fb = ImageFont.truetype(FONT, 17), ImageFont.truetype(FONT_B, 17)
    num, rest = cap.split(" · ", 1)
    lines = wrap(rest, f, w - 90, dr)
    dr.text((18, h + 12), num, font=ImageFont.truetype(FONT_B, 30), fill=(201, 162, 39))
    for i, ln in enumerate(lines[:3]):
        dr.text((64, h + 10 + i * 24), ln, font=f, fill=(236, 239, 244))
    tag, col = ("COLA", (214, 92, 40)) if glue else ("SEM COLA", (46, 140, 87))
    tw = dr.textlength(tag, font=fb)
    dr.rounded_rectangle([w - tw - 34, 14, w - 14, 46], radius=8, fill=col)
    dr.text((w - tw - 24, 18), tag, font=fb, fill="white")
    return out


def work_frame(a, b, t):
    ia, ib = Image.open(a).convert("RGBA"), Image.open(b).convert("RGBA")
    w, h = ia.width + ib.width, ia.height
    bar = 70
    out = background(w, h + bar)
    out.paste(ia, (0, 0), ia)
    out.paste(ib, (ia.width, 0), ib)
    dr = ImageDraw.Draw(out)
    dr.rectangle([0, h, w, h + bar], fill=(28, 35, 49))
    fb, f = ImageFont.truetype(FONT_B, 24), ImageFont.truetype(FONT, 17)
    lift = g.lift(t)
    dr.text((20, h + 8), f"portas a {t:4.1f}°   ·   berço +{lift:4.1f} mm", font=fb, fill=(236, 239, 244))
    phase = ("0–12°: só a cremalheira anda (espera): as portas se afastam das cartas antes de o berço subir"
             if t < P["dwell"] else "a cremalheira levanta o berço; perto de 75° a trava dá o clique e segura aberta")
    dr.text((20, h + 40), phase, font=f, fill=(190, 198, 210))
    f2 = ImageFont.truetype(FONT, 15)
    dr.text((ia.width + 14, 10), "corte logo atrás do berço: placas e cremalheira de trás", font=f2, fill=(70, 78, 92))
    return out


def save_gif(path, images, durations):
    small = [im.resize((im.width * 9 // 10, im.height * 9 // 10), Image.LANCZOS) if im.width > 1000 else im for im in images]
    sample = Image.new("RGB", (small[0].width, small[0].height * 4))
    for i, k in enumerate(range(0, len(small), max(1, len(small) // 4))[:4]):
        sample.paste(small[k], (0, i * small[0].height))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in small]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(f"{path.name}: {len(frames)} quadros, {path.stat().st_size / 1e6:.1f} MB")


def main():
    stl = export_stls()
    (WORK / "frames").mkdir(parents=True, exist_ok=True)
    frames, meta = build_frames()
    spec = {"bodies": {b: [str(stl / f"{b}.stl"), c] for b, c in COLORS.items()}, "extras": EXTRAS,
            "cameras": CAMERAS, "cut": {"y": CUT_Y, "bodies": CUT_BODIES}, "frames": frames}
    sp = WORK / "roteiro.json"
    sp.write_text(json.dumps(spec), encoding="utf-8")
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(HERE / "blender_d.py"), "--", str(sp)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    if r.returncode or "fim" not in r.stdout:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    mont = [(caption_frame(o, c, gl), du) for kind, o, c, gl, du in meta if kind == "montagem"]
    work = [(work_frame(*o, t), du) for kind, o, t, _, du in meta if kind == "funcionando"]
    save_gif(IMG / "D_montagem.gif", [m for m, _ in mont], [du for _, du in mont])
    save_gif(IMG / "D_funcionando.gif", [m for m, _ in work], [du for _, du in work])


if __name__ == "__main__":
    main()
