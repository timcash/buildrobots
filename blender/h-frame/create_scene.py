"""Build the editable H-frame hero from the War Machine Blender reference.

Open war-machine.blend in Blender 5.1 background mode and run this script.
Pass the destination .blend path after --.
"""

from math import cos, sin, tau
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


def import_objects(source_name, collection, material_for=None):
    for obj in source.collection.children[source_name].objects:
        collection.objects.link(obj)
        if obj.parent is None:
            obj.parent = origin
        material = material_for(obj) if material_for else None
        if material:
            obj.data.materials.clear()
            obj.data.materials.append(material)


def positioner_finish(obj):
    if obj.name.startswith(("T28-32212", "h-frame adaptor", "centre brace")):
        return blue
    return ink if obj.parent.name == "Positioner" else steel


def arm_material(obj):
    name = obj.name.removeprefix("Loader - ")
    return ink if name.startswith(("2010N33", "A6M", "1-01-02-base-plate")) else arm_finish


destination = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
if destination == Path(bpy.data.filepath).resolve():
    raise ValueError("Use a different path for the H-frame scene")

source = bpy.data.scenes["22 - War Machine ISO"]
source_fps_base = source.render.fps_base
bpy.context.window.scene = source
source.frame_set(1)
stationary = [
    (obj, obj.matrix_world.copy(), name == "Robot base")
    for name in ("Table", "Base and deck", "Robot base")
    for obj in source.collection.children[name].objects
]
scene = bpy.data.scenes.new("Dual Rosie workcell | production loop")
bpy.context.window.scene = scene
scene["Reference"] = "AMR War Machine ISO · gradient-cli 22f39a3479dccb01b3de83f70e40b2426f5e8825"
scene["Scope"] = "Illustrative model. Not to scale."
scene["Hero source frames"] = "601–1706, rendered at step 2"

rig = group("01  |  Editable production controls")
cad = group("02  |  Positioner CAD")
fixtures = group("03  |  Fixtures and workpieces")
base = group("04  |  Stationary foundation and loader stands")
studio = group("05  |  Studio")
welder = group("06  |  Welder Rosie 1400")
loader = group("07  |  Loader Rosie 1400")

# Translate the native cell into the existing hero's studio coordinates.
# Keep the original hierarchy and action slots, including light-data animation.
origin = add_object(rig, "War Machine · studio origin")
origin.location = (-1.7525, -0.686, 0)
import_objects("ANIMATION - editable joint controls", rig)
positioner = source.objects["Positioner"]
rig.objects.link(positioner)
rig.objects.link(positioner.parent)
positioner.parent.parent = origin

blue = finish("Cobalt powder coat · #1f5fd6", "1f5fd6", 0.15, 0.34)
ink = finish("Ink · #1a1a1a", "1a1a1a", 0.15, 0.37)
steel = finish("Satin machined steel", "89949e", 0.67, 0.31)
clamp = finish("Blackened fixture steel", "495666", 0.38, 0.31)
blank = finish("Bright cold-rolled workpiece", "bbc6cd", 0.53, 0.28)
paper = finish("Paper studio · #ebebeb", "ebebeb", 0, 0.64)
deck = finish("Satin machine deck", "879399", 0.28, 0.49)
arm_finish = finish("Rosie · slate powder coat", "53687a", 0.18, 0.38)

import_objects("Positioner", cad, positioner_finish)
import_objects("Weld fixturing", fixtures,
               lambda obj: steel if "bolt" in obj.name or "spindle" in obj.name else clamp)
import_objects("ANIMATION - workpieces and weld beads", fixtures,
               lambda obj: blank if obj.name.endswith((" / plate", " / web")) else None)
import_objects("Welder Rosie 1400", welder, arm_material)
import_objects("MIG welding head - website asset", welder)
import_objects("Loader Rosie 1400", loader, arm_material)
for obj in source.collection.children["Loader tooling and stands"].objects:
    collection, material = (loader, steel) if obj.parent else (base, ink)
    collection.objects.link(obj)
    if obj.parent is None:
        obj.parent = origin
    obj.data.materials.clear()
    obj.data.materials.append(material)

for obj, transform, robot_base in stationary:
    base.objects.link(obj)
    obj.parent = None
    obj.matrix_world = transform
    obj.location += origin.location
    obj.data.materials.clear()
    obj.data.materials.append(ink if robot_base else deck)
block(base, "Recessed deck floor", (-0.497, 0, -0.161), (3.17, 2.23, 0.080), clamp)

block(base, "Skid · lower flange", (0, 0, -0.054), (1.20, 0.81, 0.10), ink, 0.022)
block(base, "Skid · top mounting plate", (0, 0, -0.014), (1.14, 0.75, 0.054), clamp, 0.011)
drum(base, "Fixed central bearing housing", (0, 0, 0.102), 0.245, 0.181, ink)
drum(base, "Bearing shoulder", (0, 0, 0.215), 0.208, 0.057, steel)
for x in (-0.48, 0.48):
    for y in (-0.28, 0.28):
        drum(base, f"Anchor fastener {x:+.2f} {y:+.2f}", (x, y, 0.023), 0.028, 0.022, steel)
block(studio, "Studio ground", (0, 0, -0.218), (200, 200, 0.03), paper, 0)

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
# The full-cell shot keeps the gripper, torch, stands and both stations in view.
# Give the hero edit's closure keys neighbors so their tangents match.
hero_start, hero_end = 601, 1706
hero_period = hero_end - hero_start + 1
for frame in range(hero_start % 14 - 14, source.frame_end + 14, 14):
    phase = tau * (frame - hero_start) / hero_period
    camera.location = (1.68 + 0.42 * sin(phase), -7.5, 5.45 + 0.22 * cos(phase))
    aim(camera, (-0.05, 0.03, 0.49))
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
scene.render.fps_base = source_fps_base
scene.frame_start, scene.frame_end = 1, 2211
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = '//frames/h-frame_'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
for frame, label in (
    (236, "Loader pick"),
    (283, "Loader place"),
    (496, "Clamps"),
    (hero_start, "Hero in · weld"),
    (1028, "J9 station swap"),
    (1182, "Torch approach"),
    (1258, "Weld and reload"),
    (hero_end, "Hero out"),
):
    scene.timeline_markers.new(label, frame=frame)
scene.frame_set(hero_start)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.color_type = 'MATERIAL'

bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
