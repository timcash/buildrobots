"""Check the saved camera scene's animation, framing, and packed assets."""

import bpy
from mathutils import Vector

scene = bpy.context.scene
camera = scene.camera
objects = bpy.data.objects
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 240, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 1024)
assert all(obj.data.font.packed_file for obj in objects if obj.type == 'FONT')

overlay = objects['Camera-space phase captions']
assembly = objects['Camera | optical axis +X']
target = objects['Inspection target | machined part']
strobe = objects['Inspection flash on target'].data
model_parts = [obj for parent in (assembly, target) for obj in parent.children_recursive
               if obj.type in {'MESH', 'CURVE', 'FONT'}]
key_materials = ('Strobe emitters', 'AR-coated lens glass', 'CMOS photosites',
                 'PCB signal path', 'Ethernet status')


def emission(name):
    shader = bpy.data.materials[name].node_tree.nodes['Principled BSDF']
    return shader.inputs['Emission Strength'].default_value


def snapshot():
    transforms = tuple(value for obj in objects for row in obj.matrix_world for value in row)
    captions = tuple(obj.hide_render for obj in overlay.children)
    return transforms, captions, (camera.data.ortho_scale, strobe.energy,
                                   *(emission(name) for name in key_materials))


scene.frame_set(1)
first = snapshot()
scene.frame_set(241)
last = snapshot()
for a, b in zip(first, last):
    assert all(abs(x - y) < 1e-5 for x, y in zip(a, b)), 'Loop boundary differs from frame 1'

for frame in range(1, 242):
    scene.frame_set(frame)
    assert sum(not obj.hide_render for obj in overlay.children) == 3, frame

for frame, name, threshold in ((24, 'Strobe emitters', 3), (120, 'AR-coated lens glass', .70),
                               (138, 'CMOS photosites', 1.3), (164, 'PCB signal path', 1.7)):
    scene.frame_set(frame)
    assert emission(name) > threshold, name
    assert sum(emission(other) > .5 for other in key_materials[:-1]) == 1, frame

scene.frame_set(138)
for name, axis, threshold in (
    ('Heat sink cover', 'z', 1.8), ('03 | focus and aperture barrel', 'z', 1.9),
    ('04.4 | lens element', 'x', 2.4), ('06 | CMOS sensor board', 'x', .5),
    ('07 | image processing board', 'x', 1.6), ('08 | Ethernet and trigger board', 'x', 2.7),
):
    assert abs(getattr(objects[name].location, axis)) >= threshold, name

for frame in (1, 24, 39, 56, 81, 101, 120, 138, 164, 180, 200, 225, 240):
    scene.frame_set(frame)
    inverse_camera = camera.matrix_world.inverted()
    half_width = camera.data.ortho_scale / 2
    half_height = half_width * scene.render.resolution_y / scene.render.resolution_x
    for obj in model_parts:
        transform = inverse_camera @ obj.matrix_world
        limits = [transform @ Vector(corner) for corner in obj.bound_box]
        if all(abs(v.x) < half_width and abs(v.y) < half_height for v in limits):
            continue
        points = (v.co for v in obj.data.vertices) if obj.type == 'MESH' else map(Vector, obj.bound_box)
        for point in points:
            v = transform @ point
            assert abs(v.x) < half_width and abs(v.y) < half_height, (frame, obj.name)

print('PASS: camera framing, optical separation, highlight sequence, and loop closure')
