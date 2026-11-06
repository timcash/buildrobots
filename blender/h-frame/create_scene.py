"""Build the editable H-frame hero from the War Machine Blender reference.

Open war-machine.blend in Blender 5.1 background mode and run this script.
Pass the destination .blend path after --.
"""

from math import cos, pi, sin, tau
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def linear_rgb(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)


def finish(name, hex_color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*linear_rgb(hex_color), 1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def group(name):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


def add_object(collection, name, data=None, parent=None):
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.parent = parent
    return obj


def finish_mesh(obj, collection, mat, bevel):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        edge = obj.modifiers.new("Machined edges", 'BEVEL')
        edge.width = bevel
        edge.segments = 3
        obj.modifiers.new("Face normals", 'WEIGHTED_NORMAL')


def block(collection, name, xyz, size, mat, bevel=0.005, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name, obj.parent = name, parent
    for vertex in obj.data.vertices:
        for axis, extent in enumerate(size):
            vertex.co[axis] *= extent
    finish_mesh(obj, collection, mat, bevel)
    return obj


def drum(collection, name, xyz, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=80, radius=radius, depth=depth, location=xyz)
    obj = bpy.context.object
    obj.name = name
    finish_mesh(obj, collection, mat, 0.004)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def keyframe_interpolation(obj, interpolation):
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = interpolation
                        key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'


def copy_station_mesh(original, collection, material, parent=None):
    part = add_object(collection, original.name, original.data.copy(), parent)
    part.matrix_basis = source_world[original].copy()
    if parent:
        part.matrix_basis = source_world[original.parent].inverted() @ part.matrix_basis
    else:
        part.location -= pivot
    if material:
        part.data.materials.clear()
        part.data.materials.append(material)
    return part


def copy_arm(role, tool_meshes):
    collection = group(f"{role} Rosie 1400 rig")
    controls = {}

    def copy_control(original):
        if original not in controls:
            parent = None if original.name.endswith(" / base") else copy_control(original.parent)
            joint = original.name.rsplit(" / ", 1)[-1]
            control = add_object(collection, f"{role} · {joint}", parent=parent)
            control.empty_display_type = 'PLAIN_AXES'
            control.empty_display_size = 0.08
            if parent:
                control.matrix_basis = source_world[original.parent].inverted() @ source_world[original]
            else:
                control.matrix_basis = source_world[original].copy()
                control.location -= pivot
            controls[original] = control
        return controls[original]

    for original in source.collection.children[f"{role} Rosie 1400"].objects:
        if original.type == 'MESH':
            name = original.name.removeprefix("Loader - ")
            material = ink if name.startswith(("2010N33", "A6M", "1-01-02-base-plate")) else arm_finish
            copy_station_mesh(original, collection, material, copy_control(original.parent))
    for original, material in tool_meshes:
        copy_station_mesh(original, collection, material, copy_control(original.parent))


source = bpy.data.scenes["22 - War Machine ISO"]
bpy.context.window.scene = source
source.frame_set(1)
bpy.context.view_layer.update()
source_world = {obj: obj.matrix_world.copy() for obj in source.objects}
scene = bpy.data.scenes.new("Dual Rosie workcell | two-bay H-frame index")
bpy.context.window.scene = scene
scene["Reference"] = "AMR War Machine ISO: dual Rosie arms, deck, loader tooling and H-frame"
scene["Scope"] = "Illustrative model. Not engineering data. Not to scale."

rig = group("01  |  J9 index")
cad = group("02  |  Positioner CAD")
fixtures = group("03  |  Fixtures and illustrative workpieces")
base = group("04  |  Stationary foundation")
studio = group("05  |  Studio")
pivot = Vector((1.7525, 0.686, 0))
index = add_object(rig, "J9 · 180 degree bay exchange")
index.empty_display_type = 'ARROWS'
index.empty_display_size = 0.32

blue = finish("Cobalt powder coat · #1f5fd6", "1f5fd6", 0.15, 0.34)
ink = finish("Ink · #1a1a1a", "1a1a1a", 0.15, 0.37)
steel = finish("Satin machined steel", "89949e", 0.67, 0.31)
clamp = finish("Blackened fixture steel", "495666", 0.38, 0.31)
blank = finish("Bright cold-rolled workpiece", "bbc6cd", 0.53, 0.28)
paper = finish("Paper studio · #ebebeb", "ebebeb", 0, 0.64)
deck = finish("Satin machine deck", "879399", 0.28, 0.49)
arm_finish = finish("Rosie · slate powder coat", "53687a", 0.18, 0.38)

for source_name, collection in (("Positioner", cad), ("Weld fixturing", fixtures)):
    for original in source.collection.children[source_name].objects:
        if original.type != 'MESH':
            continue
        indexed = collection == fixtures or (original.parent and original.parent.name != "Positioner")
        if original.name.startswith(("T28-32212", "h-frame adaptor", "centre brace")):
            material = blue
        elif collection == fixtures:
            material = steel if "bolt" in original.name or "spindle" in original.name else clamp
        else:
            material = steel if indexed else ink
        part = add_object(collection, original.name, original.data.copy(), index if indexed else None)
        part.matrix_basis = source_world[original].copy()
        part.location -= pivot
        part.data.materials.clear()
        part.data.materials.append(material)

for name in ("Table", "Base and deck", "Robot base"):
    for original in source.collection.children[name].objects:
        if original.type == 'MESH':
            material = ink if name == "Robot base" else deck
            copy_station_mesh(original, base, material)
block(base, "Recessed deck floor", (-0.497, 0, -0.161), (3.17, 2.23, 0.080), clamp)

# Keep the native weld head, loader gripper and stands. Both arms are
# parked clear of the illustrated J9 sweep.
tooling = source.collection.children["Loader tooling and stands"].objects
for original in tooling:
    if original.parent is None:
        copy_station_mesh(original, base, ink)
copy_arm("Welder", [
    (obj, None) for obj in source.collection.children["MIG welding head - website asset"].objects
    if obj.type == 'MESH'
])
copy_arm("Loader", [(obj, steel) for obj in tooling if obj.parent])
staged_parts = source.collection.children["ANIMATION - workpieces and weld beads"].objects
for shape in ("plate", "web"):
    original = staged_parts[f"Cycle part 0 / {shape}"]
    copy_station_mesh(original, fixtures, blank).name = f"Rear stand · workpiece {shape}"
    front = copy_station_mesh(original, fixtures, blank)
    front.name = f"Front stand · workpiece {shape}"
    front.location.y -= 1.70

# Two captured T-joint blanks make the bay exchange readable as the fixture moves.
for bay, x in (("A", -0.50), ("B", 0.50)):
    block(fixtures, f"Bay {bay} · workpiece plate", (x, 0, 0.749), (0.15, 0.56, 0.022), blank, 0.002, index)
    block(fixtures, f"Bay {bay} · workpiece web", (x, 0, 0.793), (0.016, 0.56, 0.068), blank, 0.002, index)
    side = -1 if x < 0 else 1
    block(fixtures, f"Bay {bay} · identification plate", (x + side * 0.103, -0.55, 0.631),
          (0.008, 0.14, 0.067), ink, 0.004, index)
    for stripe in range(1 if bay == "A" else 2):
        block(fixtures, f"Bay {bay} · identification stripe {stripe + 1}",
              (x + side * 0.108, -0.568 + stripe * 0.037, 0.631), (0.003, 0.014, 0.043), blank, 0.001, index)

block(base, "Skid · lower flange", (0, 0, -0.054), (1.20, 0.81, 0.10), ink, 0.022)
block(base, "Skid · top mounting plate", (0, 0, -0.014), (1.14, 0.75, 0.054), clamp, 0.011)
drum(base, "Fixed central bearing housing", (0, 0, 0.102), 0.245, 0.181, ink)
drum(base, "Bearing shoulder", (0, 0, 0.215), 0.208, 0.057, steel)
for x in (-0.48, 0.48):
    for y in (-0.28, 0.28):
        drum(base, f"Anchor fastener {x:+.2f} {y:+.2f}", (x, y, 0.023), 0.028, 0.022, steel)
block(studio, "Studio ground", (0, 0, -0.218), (200, 200, 0.03), paper, 0)

# Two equal indexes with stationary dwell at each bay. Frame 193 is the
# closure reference, so the encoder uses frames 1–192 exactly once.
for frame, angle in ((1, 0), (23, 0), (81, pi), (119, pi), (177, tau), (193, tau)):
    index.rotation_euler.z = angle
    index.keyframe_insert("rotation_euler", frame=frame, group="J9 index")
keyframe_interpolation(index, 'BEZIER')

world = bpy.data.worlds.new("Neutral studio fill")
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.79, 0.84, 0.92, 1)
background.inputs["Strength"].default_value = 0.38
scene.world = world
for name, xyz, power, size in (
    ("Key softbox", (-3.8, -4.0, 5.5), 1125, 4.3),
    ("Fill softbox", (3.2, -1.5, 3.0), 440, 3.4),
    ("Rim softbox", (-1.0, 3.4, 4.8), 950, 3.2),
):
    lamp = bpy.data.lights.new(name, 'AREA')
    lamp.energy, lamp.size = power, size
    light = add_object(studio, name, lamp)
    light.location = xyz
    aim(light, (0, 0, 0.3))

camera_data = bpy.data.cameras.new("Hero camera")
camera_data.type, camera_data.ortho_scale = 'ORTHO', 5.35
camera = add_object(studio, "Hero camera", camera_data)
scene.camera = camera
# Give the closure keys neighbors on both sides so their tangents match.
for frame in range(-3, 198, 4):
    phase = tau * (frame - 1) / 192
    camera.location = (2.05 + 0.48 * sin(phase), -7.5, 5.0 + 0.25 * cos(phase))
    aim(camera, (-0.08, -0.06, 0.44))
    camera.keyframe_insert("location", frame=frame, group="Periodic camera")
    camera.keyframe_insert("rotation_euler", frame=frame, group="Periodic camera")
keyframe_interpolation(camera, 'BEZIER')

for other in list(bpy.data.scenes):
    if other != scene:
        bpy.data.scenes.remove(other)
# Release the input collections before saving so the hero has no external assets.
bpy.data.orphans_purge(do_recursive=True)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 10
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 5
scene.render.use_persistent_data = True
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 192
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = '//frames/h-frame_'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.timeline_markers.new("Bay A · locked", frame=1)
scene.timeline_markers.new("Index A to B", frame=23)
scene.timeline_markers.new("Bay B · locked", frame=81)
scene.timeline_markers.new("Index B to A", frame=119)
scene.timeline_markers.new("Bay A · locked", frame=177)
scene.frame_set(1)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.color_type = 'MATERIAL'

destination = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
