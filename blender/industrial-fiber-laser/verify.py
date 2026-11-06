"""Verify the native animation in the saved fiber-laser scene."""

import bpy
from mathutils import Vector

scene = bpy.context.scene
objects = bpy.data.objects
camera = scene.camera
overlay = objects['Screen-aligned phase labels']
head = objects['05 | Processing head']
stage = objects['06 | Coupon linear stage']
weld = objects['Growing weld bead']
beam = objects['Illustrative focused beam']
phases = {
    84: ('Pump diode package', 'Pump light in pigtail', 'Combine pump light'),
    115: ('Gain fiber jacket', 'Signal through gain fiber', 'Amplify in the Yb coil'),
    151: ('Braided delivery jacket', 'Signal in delivery fiber', 'Guide light to the head'),
    173: ('Blue AR-coated optics', 'Signal inside head', 'Focus light on the seam'),
}

assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 240, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 1024)
assert all(obj.data.font.packed_file for obj in objects if obj.type == 'FONT')
assert not any(image.source == 'FILE' and not image.packed_file for image in bpy.data.images)


def emission(material):
    shader = bpy.data.materials[material].node_tree.nodes['Principled BSDF']
    return shader.inputs['Emission Strength'].default_value


def visible_state():
    visible = [obj for obj in objects if not obj.hide_render]
    return (
        tuple(obj.name for obj in visible),
        tuple(v for obj in visible for row in obj.matrix_world for v in row),
        (camera.data.ortho_scale, *(emission(material) for material, _, _ in phases.values())),
    )


scene.frame_set(1)
first = visible_state()
scene.frame_set(241)
last = visible_state()
assert first[0] == last[0], 'Visibility changes at the loop boundary'
for a, b in zip(first[1:], last[1:]):
    assert all(abs(x - y) < 1e-5 for x, y in zip(a, b)), 'Loop boundary differs from frame 1'

for frame, (material, trace, caption) in phases.items():
    scene.frame_set(frame)
    assert emission(material) > .3, (frame, material)
    signal = objects[trace]
    assert not signal.hide_render and signal.data.bevel_factor_end > signal.data.bevel_factor_start, trace
    assert not objects[caption].hide_render, caption
    assert objects['Source lid'].location.z > 2, frame
assert objects['Removable head cowl'].location.x > .8

for frame in range(167, 193):
    scene.frame_set(frame)
    assert not weld.hide_render and not beam.hide_render, frame
    weld_tip = stage.location.x - .65 + 1.3 * weld.data.bevel_factor_end
    assert abs(weld_tip - head.location.x) < .04, (frame, weld_tip)

model = [obj for obj in objects if obj.type in {'MESH', 'CURVE', 'FONT'}
         and obj.parent != overlay and not obj.name.endswith('contact shadow')]
captions = [obj for obj in overlay.children if obj.type == 'FONT' and not obj.name.startswith('Optical path step')]
for frame in (1, 17, 35, 52, 69, 97, 118, 136, 152, 166, 179, 192, 209, 226, 240, 241):
    scene.frame_set(frame)
    assert sum(not obj.hide_render for obj in captions) == 1, frame
    inverse = camera.matrix_world.inverted()
    half_width = camera.data.ortho_scale / 2
    half_height = half_width * scene.render.resolution_y / scene.render.resolution_x
    for obj in model:
        if obj.hide_render:
            continue
        transform = inverse @ obj.matrix_world
        for corner in obj.bound_box:
            point = transform @ Vector(corner)
            assert abs(point.x) < half_width and abs(point.y) < half_height, (frame, obj.name)

print('PASS: laser reveal, four optical phases, weld tracking, framing, and loop closure')
