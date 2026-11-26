"""Lado Blender do animar_d.py: le o roteiro (JSON), monta a cena com os STLs e renderiza cada quadro.
    blender -b --factory-startup --python blender_d.py -- roteiro.json
Cada peca vem do STL na posicao montada (fechada); a pose de cada quadro e giro em Y em volta de um pivo + translacao.
"""
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector

spec = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "MATERIAL"
sh.show_cavity, sh.cavity_type = True, "BOTH"
sh.show_object_outline, sh.object_outline_color = True, (0.08, 0.08, 0.1)
sh.show_specular_highlight = True
scene.display.render_aa = "16"
scene.render.film_transparent = True
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"


def material(hexcol):
    m = bpy.data.materials.get(hexcol)
    if m is None:
        lin = [(c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
               for c in bytes.fromhex(hexcol.lstrip("#"))]
        m = bpy.data.materials.new(hexcol)
        m.diffuse_color = (*lin, 1.0)
    return m


def finish(obj, name, color):
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(material(color))
    return obj


GROUP = {}
for name, (path, color) in spec["bodies"].items():
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    new = (set(bpy.data.objects) - before).pop()
    GROUP[finish(new, name, color).name] = name
for ex in spec["extras"]:                       # imas e parafusos: cilindros e cones no lugar montado
    rot = {"X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0), "Z": (0, 0, 0)}[ex["axis"]]
    if ex["kind"] == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(radius=ex["r"], depth=ex["h"], location=ex["center"], rotation=rot, vertices=32)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=ex["r"], radius2=ex["r2"], depth=ex["h"], location=ex["center"], rotation=rot, vertices=32)
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    GROUP[finish(o, ex["name"], ex["color"]).name] = ex["group"]

# corte (vista do mecanismo): copias cortadas no plano y = cut, ficando o lado de tras. Giro em Y e subida em Z nao
# mexem em y, entao cortar uma vez na pose montada vale para todos os quadros.
cut = spec["cut"]
bpy.ops.mesh.primitive_cube_add(size=1)
cutter = bpy.context.active_object
cutter.scale, cutter.location = (2000, 2000, 2000), (0, cut["y"] + 1000, 0)
cutter.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
for name in cut["bodies"]:
    src = bpy.data.objects[name]
    c = bpy.data.objects.new(name + "_cut", src.data.copy())
    scene.collection.objects.link(c)
    m = c.modifiers.new("cut", "BOOLEAN")
    m.operation, m.solver, m.object = "INTERSECT", "EXACT", cutter
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(c.evaluated_get(dg))
    c.modifiers.clear()
    c.data = mesh
    GROUP[c.name] = GROUP[name]

cams = {}
for name, cs in spec["cameras"].items():
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    cam.data.type, cam.data.ortho_scale = "ORTHO", cs["ortho_scale"]
    cam.data.clip_start, cam.data.clip_end = 1, 5000
    eye, tgt = Vector(cs["eye"]), Vector(cs["target"])
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
    cams[name] = (cam, cs["res"])


def pose_matrix(p):
    px, pz = p.get("pivot", (0, 0))
    piv = Vector((px, 0, pz))
    return (Matrix.Translation(Vector(p.get("t", (0, 0, 0)))) @ Matrix.Translation(piv)
            @ Matrix.Rotation(math.radians(p.get("rot", 0)), 4, "Y") @ Matrix.Translation(-piv))


for i, fr in enumerate(spec["frames"]):
    cam, res = cams[fr["cam"]]
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    vis = set(fr["visible"])
    for o in scene.objects:
        if o.type != "MESH" or o is cutter:
            continue
        o.hide_render = o.name not in vis
        o.matrix_world = pose_matrix(fr["poses"].get(GROUP[o.name], {}))
    scene.render.filepath = fr["out"]
    bpy.ops.render.render(write_still=True)
    if i % 20 == 0:
        print(f"quadro {i + 1}/{len(spec['frames'])}", flush=True)
print("fim", flush=True)
