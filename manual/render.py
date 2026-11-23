"""Renderizacao ortografica da versao C pelo solidcraft-cli, com projecao conhecida (para setas e cotas)."""
import io, contextlib, json, math, subprocess, sys, os
import numpy as np
from PIL import Image

import tempfile
from pathlib import Path

CAD = Path(__file__).resolve().parent.parent / "cad" / "C-elevador"
sys.path.insert(0, str(CAD))
with contextlib.redirect_stdout(io.StringIO()):
    import gerar_came as g          # numeros do mecanismo (e reescreve o script do modelo, igual)

CLI = os.environ.get("SOLIDCRAFT_CLI", str(Path.home() / "Desktop/programas/cad/solidcraft-portable/app/"
                                             "solidcraft-0.40.1-windows-x64-portable/solidcraft-cli.exe"))
SC = str(CAD / "C_elevador.sc")
OUT = os.path.join(tempfile.gettempdir(), "deckbox_manual_C")
os.makedirs(OUT, exist_ok=True)
n = g.n
Hy, Hz = n["Hy"], n["Hz"]
MAG_X = (n["x_ko"] + n["x_si"]) / 2
MAG_Y = (-n["D"] / 2 + Hy - (-g.E0[0] + g.ARM_HW + 1.2)) / 2
MAG_H = 2.1


class Cam:
    """Camera quase ortografica (fov minusculo a 20 m): pixel = centro + s * (d.r, -d.u)."""
    def __init__(self, target, yaw, pitch, w, h, s):
        self.t, self.yaw, self.pitch, self.w, self.h, self.s = np.array(target, float), yaw, pitch, w, h, s
        self.dist = 20000.0
        self.fov = 2 * math.atan(h / s / 2 / self.dist)
        e = np.array([-math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
        r = np.cross([0, 0, 1], e)
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(e, self.r)

    def json(self):
        return json.dumps({"target": [float(v) for v in self.t], "yaw": self.yaw, "pitch": self.pitch,
                           "distance": self.dist, "fov": self.fov})

    def __call__(self, P):
        d = np.array(P, float) - self.t
        return (self.w / 2 + self.s * float(d @ self.r), self.h / 2 - self.s * float(d @ self.u))


def whiten(path):
    """Fundo em degrade do renderizador -> branco (mistura pela distancia ao fundo de cada linha)."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    bg = (a[:, :3].mean(axis=1) + a[:, -3:].mean(axis=1)) / 2          # fundo de cada linha (bordas)
    diff = np.abs(a - bg[:, None, :]).max(axis=2)
    alpha = np.clip(diff / 22.0, 0, 1)[..., None]
    out = a + (1 - alpha) * (255 - bg[:, None, :])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)


def mv(bodies, v):
    return [{"command": "solid.move", "params": {"bodies": bodies, "translate": [float(c) for c in v]}}] if any(abs(c) > 1e-9 for c in v) else []


def rot_x(bodies, deg, oy, oz):
    """Gira em X em volta de (oy, oz) numerico (o solid.move gira na origem)."""
    return g.turn(bodies, deg, f"{oy}", f"{oz}")


def cyl(name, d, h, base, axis="Z"):
    return {"command": "solid.cylinder", "params": {"diameter": d, "height": h, "axis": axis, "base": [float(c) for c in base],
                                                     "operation": "new", "body_name": name}}


def _shot(out, cam, sp, colors, quality):
    args = [CLI, "snapshot", sp, "--in", SC, "--out", out, "--width", str(cam.w), "--height", str(cam.h),
            "--camera", cam.json(), "--no-grid", "--no-axes", "--quality", quality]
    for b, c in colors.items():
        args += ["--body", f"{b}:{c}"]
    r = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(out + ": " + r.stderr[-600:])


def snap(name, cam, cmds, vis, colors=None, quality="fine"):
    """Renderiza e troca o fundo por branco usando uma 2a passada com tudo magenta como mascara."""
    out = os.path.join(OUT, name + ".png")
    sp = out + ".json"
    cmds = cmds + [{"command": "browser.visibility", "params": {"visible": True, "items": vis, "isolate": True}}]
    json.dump({"commands": cmds}, open(sp, "w"))
    _shot(out, cam, sp, colors or {}, quality)
    _shot(out + ".m.png", cam, sp, {b: "color=#ff00ff" for b in vis}, quality)
    a = np.asarray(Image.open(out).convert("RGB")).astype(float)
    m = np.asarray(Image.open(out + ".m.png").convert("RGB")).astype(float)
    mag = np.clip((np.minimum(m[..., 0], m[..., 2]) - m[..., 1] - 25) / 45, 0, 1)
    dark = np.clip((150 - m.max(axis=2)) / 50, 0, 1)
    alpha = np.maximum(mag, dark)[..., None]
    Image.fromarray(np.clip(a * alpha + 255 * (1 - alpha), 0, 255).astype(np.uint8)).save(out)
    os.remove(out + ".m.png")
    return out
