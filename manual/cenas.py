"""Cenas do manual: camera, comandos, corpos visiveis e cores. Cada cena vira r/<nome>.png."""
import math, sys, os
from concurrent.futures import ThreadPoolExecutor
from render import *

S_SHEET1 = 0.5 * 300 / 25.4          # 1:2 em 300 dpi
S_SHEET2 = 300 / 25.4                # 1:1
S_ST = 9.0                           # passos (depois a pagina escala)
ISO = (-math.pi / 4, math.atan(1 / math.sqrt(2)))
ST = (-0.7, 0.42)                    # vista 3/4 dos passos

OLD = "color=#dfe4ea"
COL = {"Core": "#26324f", "ShellR": "#26324f", "ShellL": "#26324f", "Cradle": "#7a2433", "Lid": "#c9971f",
       "CrankR": "#2f7fc1", "CrankL": "#2f7fc1", "LeverR": "#2e9a6f", "LeverL": "#2e9a6f", "Deck": "#d8cfbd",
       "Divider": "#26324f"}
PIN = "#3a3f47"
for b in ("AxleR", "AxleL", "PivotR", "PivotL", "CpinR", "CpinL", "EpinR", "EpinL"):
    COL[b] = PIN
LIGHT = "color=#f5f7fa"
ASM = ["Core", "Cradle", "Lid", "CrankR", "CrankL", "LeverR", "LeverL", "AxleR", "AxleL", "PivotR", "PivotL",
       "CpinR", "CpinL", "EpinR", "EpinL", "ShellR", "ShellL"]
SIDE_R = ["Core", "Cradle", "Lid", "CrankR", "LeverR", "AxleR", "PivotR", "CpinR", "EpinR"]


def colors(new, old=()):
    c = {b: f"color={COL[b]}" for b in new if b in COL}
    c.update({b: OLD for b in old})
    return c


def rx(P, deg, oy=Hy, oz=Hz):
    """Ponto girado em X em volta de (oy, oz), mesma convencao do solid.move."""
    t = math.radians(deg)
    y, z = P[1] - oy, P[2] - oz
    return (P[0], oy + y * math.cos(t) - z * math.sin(t), oz + y * math.sin(t) + z * math.cos(t))


LID_N = (0, math.sin(math.radians(-110)), -math.cos(math.radians(-110)))   # normal da face interna da tampa a 110 graus


def mags():
    """4 imas: 2 no corpo (MagB*) e 2 na tampa (MagT*), na posicao fechada."""
    out = []
    for s, tag in ((1, "R"), (-1, "L")):
        out.append(cyl(f"MagB{tag}", 4, 2, (s * MAG_X, MAG_Y, n["split"] - MAG_H)))
        out.append(cyl(f"MagT{tag}", 4, 2, (s * MAG_X, MAG_Y, n["split"] + 0.1)))
    return out


def feet():
    fx, fy = n["W"] / 2 - n["foot_e"], n["D"] / 2 - n["foot_e"]
    return [cyl(f"Foot{i}", 8, 2, (sx * fx, sy * fy, n["foot_h"] - 2)) for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]


MAGS = ["MagBR", "MagBL", "MagTR", "MagTL"]
FEET = ["Foot0", "Foot1", "Foot2", "Foot3"]
MAGC = {m: "color=#b0353c" for m in MAGS}
FEETC = {f: "color=#2b2b2b" for f in FEET}

E_EXPL = 14     # deslocamento das pecas explodidas (mm), varia por passo


def scenes():
    sc = {}
    # ---- folha 1: vistas ortograficas 1:2 (traço claro) e perspectiva colorida
    light = {b: LIGHT for b in ("Core", "Lid", "ShellR", "ShellL")}
    vis = ["Core", "Lid", "ShellR", "ShellL"]
    sc["o_front"] = (Cam([0, 0, 50.5], 0, 0, 640, 700, S_SHEET1), [], vis, light)
    sc["o_left"] = (Cam([0, 0, 50.5], math.pi / 2, 0, 560, 700, S_SHEET1), [], vis, light)
    sc["o_top"] = (Cam([0, 0, 50.5], 0, math.pi / 2 - 1e-3, 640, 560, S_SHEET1), [], vis, light)
    sc["o_iso"] = (Cam([0, 18, 72], *ISO, 1600, 1800, 8.0), g.pose(110, 110), ASM + ["Deck"], {})
    # ---- folha 2: mecanismo de lado (1:1), sem o painel direito
    side = SIDE_R + ["Deck"]
    sc["m_closed"] = (Cam([0, 0, 50.5], -math.pi / 2, 0, 1100, 1400, S_SHEET2), [], side, {})
    sc["m_open"] = (Cam([0, 21, 72], -math.pi / 2, 0, 1600, 1900, S_SHEET2), g.pose(110, 110), side, {})
    # ---- capa
    sc["c_closed"] = (Cam([0, 0, 50], -0.62, 0.45, 1700, 1900, 13), [], ASM, {})
    sc["c_open"] = (Cam([0, 20, 70], -0.62, 0.45, 1900, 2300, 13), g.pose(110, 110), ASM + ["Deck"], {})
    # ---- pecas impressas (cada uma isolada)
    sc["p_core"] = (Cam([0, 0, 45], *ST, 1500, 1500, 8), [], ["Core"], colors(["Core"]))
    sc["p_cradle"] = (Cam([0, 0, 45], *ST, 1500, 1500, 8), [], ["Cradle"], colors(["Cradle"]))
    sc["p_lid"] = (Cam([0, 0, 95], -0.7, -0.6, 1600, 1300, 11), [], ["Lid"], colors(["Lid"]))
    sc["p_shellr"] = (Cam([41.8, 0, 46], math.pi / 2 - 0.55, 0.3, 1100, 1400, 12), [], ["ShellR"], colors(["ShellR"]))
    sc["p_shelll"] = (Cam([-41.8, 0, 46], -math.pi / 2 + 0.55, 0.3, 1100, 1400, 12), [], ["ShellL"], colors(["ShellL"]))
    sc["p_crank"] = (Cam([39, 28, 77], -math.pi / 2 + 0.35, 0.25, 900, 900, 24), [], ["CrankR"], colors(["CrankR"]))
    sc["p_lever"] = (Cam([42.5, 4, 66], -math.pi / 2 + 0.35, 0.25, 1700, 900, 18), [], ["LeverR"], colors(["LeverR"]))
    sc["p_divider"] = (Cam([93.2, 6.7, 1], *ST, 1400, 1200, 12), [], ["Divider"], colors(["Divider"]))
    # ---- passo 2: berco desce no corpo
    sc["s2"] = (Cam([0, 0, 110], *ST, 1900, 2300, S_ST), mv(["Cradle"], [0, 0, 130]), ["Core", "Cradle"],
                colors(["Cradle"], ["Core"]))
    # ---- passo 3: manivelas na orelha da tampa (vista de baixo)
    sc["s3"] = (Cam([0, 12, 82], -0.55, -0.55, 1900, 1500, S_ST), mv(["CrankR"], [-18, 0, 0]) + mv(["CrankL"], [18, 0, 0]),
                ["Lid", "CrankR", "CrankL"], colors(["Lid", "CrankR", "CrankL"]))
    # ---- passo 4: tampa (com manivelas) no corpo
    sc["s4"] = (Cam([0, 0, 90], *ST, 1900, 2200, S_ST), mv(["Lid", "CrankR", "CrankL"], [0, 0, 60]),
                ["Core", "Cradle", "Lid", "CrankR", "CrankL"], colors(["Lid", "CrankR", "CrankL"], ["Core", "Cradle"]))
    # ---- passos 5 a 7: lado direito de perto
    zc = Cam([58, 6, 52], -1.05, 0.3, 2100, 1800, 11)
    base = ["Core", "Cradle", "Lid", "CrankR"]
    sc["s5"] = (zc, mv(["AxleR", "PivotR"], [30, 0, 0]), base + ["AxleR", "PivotR"], colors(["AxleR", "PivotR"], base))
    b6 = base + ["AxleR", "PivotR"]
    sc["s6"] = (zc, mv(["CpinR"], [24, 0, 0]), b6 + ["CpinR"], colors(["CpinR"], b6))
    sc["s7a"] = (Cam([46, 4, 66], -math.pi / 2 + 0.45, 0.3, 1700, 1000, 14), mv(["EpinR"], [16, 0, 0]), ["LeverR", "EpinR"],
                 colors(["LeverR", "EpinR"]))
    b7 = b6 + ["CpinR"]
    sc["s7b"] = (Cam([58, 6, 52], -1.05, 0.3, 2100, 1800, 11), mv(["LeverR", "EpinR"], [30, 0, 0]), b7 + ["LeverR", "EpinR"],
                 colors(["LeverR", "EpinR"], b7))
    # ---- passo 8: paineis (teste a seco) e o mecanismo em 3 angulos
    b8 = [b for b in ASM if b not in ("ShellR", "ShellL")]
    sc["s8"] = (Cam([20, 0, 55], *ST, 2000, 1900, S_ST), mv(["ShellR"], [45, 0, 0]) + mv(["ShellL"], [-45, 0, 0]),
                b8 + ["ShellR", "ShellL"], colors(["ShellR", "ShellL"], b8))
    for t in (0, 60, 110):
        sc[f"s8_{t}"] = (Cam([0, 21, 72], -math.pi / 2, 0, 1600, 1900, 9), g.pose(t, t), side, {})
    # ---- passo 9: face interna do painel (acetona)
    sc["s9"] = (Cam([41.8, 0, 46], math.pi / 2 - 0.55, 0.3, 1100, 1400, 12), [], ["ShellR"], colors(["ShellR"]))
    # ---- passo 10: imas (tampa aberta), explodidos
    open_cmds = g.pose(110, 110)
    m_cmds = mags() + [{"command": "solid.move", "params": {"bodies": ["MagBR", "MagBL"], "translate": [0, 0, 16]}}] \
        + rot_x(["MagTR", "MagTL"], -110, Hy, Hz) \
        + [{"command": "solid.move", "params": {"bodies": ["MagTR", "MagTL"], "translate": [0, 16 * LID_N[1], 16 * LID_N[2]]}}]
    b10 = ["Core", "Cradle", "Lid", "CrankR", "CrankL", "LeverR", "LeverL", "ShellR", "ShellL", "AxleR", "PivotR", "CpinR", "EpinR"]
    c10 = colors([], b10)
    c10.update(MAGC)
    sc["s10"] = (Cam([0, 10, 95], -0.45, 0.6, 2000, 1800, S_ST), open_cmds + m_cmds, b10 + MAGS, c10)
    # ---- passo 11: pes (vista de baixo)
    f_cmds = feet() + [{"command": "solid.move", "params": {"bodies": FEET, "translate": [0, 0, -14]}}]
    c11 = {"Core": OLD, "ShellR": OLD, "ShellL": OLD, "Lid": OLD}
    c11.update(FEETC)
    sc["s11"] = (Cam([0, 0, 30], -0.7, -0.62, 1900, 1700, S_ST), f_cmds, ["Core", "ShellR", "ShellL", "Lid"] + FEET, c11)
    # ---- uso: fechada, abrindo, aberta
    for t in (0, 55, 110):
        sc[f"u_{t}"] = (Cam([0, 20, 70], -0.62, 0.45, 1900, 2300, 10), g.pose(t, t), ASM + ["Deck"], {})
    return sc


SC_ = scenes()


def render_all(names=None, force=False):
    todo = [k for k in SC_ if (names is None or k in names) and (force or not os.path.exists(os.path.join(OUT, k + ".png")))]

    def job(k):
        cam, cmds, vis, cols = SC_[k]
        snap(k, cam, cmds, vis, cols)
        return k
    with ThreadPoolExecutor(6) as ex:
        for k in ex.map(job, todo):
            print("ok", k, flush=True)


if __name__ == "__main__":
    render_all(sys.argv[1:] or None, force=True)
