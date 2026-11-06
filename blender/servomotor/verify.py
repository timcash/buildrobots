"""Check saved part motion, callouts, framing and loop closure without rendering."""

from math import isclose, tau

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
camera = scene.camera
assert not bpy.data.libraries
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 216, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 1024)

parts = [scene.objects[name] for name in (
    'Finned housing', 'Wound stator', 'Permanent magnet rotor', 'Output shaft',
    'Front bell and bearing', 'Rear bell and bearing', 'Absolute encoder',
    'Feedback cover and sockets',
)]
spinners = [scene.objects[name] for name in ('Rotor spin', 'Shaft spin', 'Encoder target spin')]
assert [obj.parent for obj in spinners] == [parts[2], parts[3], parts[6]]
graphics = [obj for obj in scene.collection.children['09 | Explanatory callouts'].objects
            if obj.type == 'FONT']
assert {obj.data.body for obj in graphics} == {'01  STATOR', '02  ROTOR', '03  SHAFT', '04  ENCODER'}
assert all(obj.data.font.packed_file for obj in graphics)

scene.frame_set(1)
tracked = [*parts, *spinners, camera, *(obj.parent for obj in graphics)]
initial = [obj.matrix_world.copy() for obj in tracked]
initial_zoom = camera.data.ortho_scale
assert all(part.location.length < 1e-6 for part in parts)

scene.frame_set(153)
assert all(part.location.length > .5 for part in parts)
assert camera.data.ortho_scale > initial_zoom
assert all(obj.parent.scale.x > .99 for obj in graphics)

model = [obj for obj in scene.objects if obj.type in {'MESH', 'CURVE', 'FONT'}]
callout_roots = {obj.parent for obj in graphics}
housing, stator, rotor, shaft, front, rear, encoder, cover = parts
for frame in range(1, 218):
    scene.frame_set(frame)
    housing_offset = Vector((housing.location.y, housing.location.z)).length
    rear_overlap = (rear.location.x - 1.39) - (housing.location.x - 1.42)
    # Allow the rear bell to seat into the machined land on-axis at home.
    assert rear_overlap <= (.031 if housing_offset < .001 else 0), (frame, 'rear bell and housing')
    if housing_offset > .001:
        if housing.location.x + 1.25 > stator.location.x - 1.26:
            assert housing_offset > 2.68, (frame, 'stator and housing')
    assert rear.location.x - 1.65 > encoder.location.x - 1.80, (frame, 'rear bell and encoder')
    if cover.location.x - 1.52 > encoder.location.x - 2.10:
        offset = encoder.location - cover.location
        assert Vector((offset.y, offset.z)).length + .77 < .975, (frame, 'encoder and cover')
    axial_gap = rotor.location.x - .99 - (stator.location.x + 1.12)
    if axial_gap < 0:
        assert Vector((rotor.location.y, rotor.location.z)).length + .668 < .715, frame
    shaft_min = shaft.location.x - 1.91
    shaft_max = shaft.location.x + 2.61
    for part, x_limits, outer in (
        (stator, (-1.26, 1.12), 1.11),
        (rotor, (-.99, .91), .668),
        (front, (1.21, 1.62), 1.72),
        (rear, (-1.65, -1.39), 1.54),
        (encoder, (-2.10, -1.80), .77),
    ):
        x_min, x_max = [part.location.x + x for x in x_limits]
        if shaft_min < x_max and shaft_max > x_min:
            offset = shaft.location - part.location
            radial = Vector((offset.y, offset.z)).length
            assert radial < .001 or radial > outer + .285, (frame, part.name, radial)
            if part == rotor and radial < .001:
                assert shaft.location.x + .91 >= rotor.location.x + .89, (frame, 'shaft collar')
    angle = 3 * tau * (frame - 1) / 216
    for obj in spinners:
        assert isclose(obj.rotation_euler.x, angle, abs_tol=1e-5), (frame, obj.name)
        assert abs(obj.rotation_euler.y) + abs(obj.rotation_euler.z) < 1e-6
    for obj in model:
        if obj.parent in callout_roots and obj.parent.scale.x < .01:
            continue
        for corner in obj.bound_box:
            point = world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
            assert 0.01 < point.x < .99 and .01 < point.y < .99, (frame, obj.name, point)

assert isclose(camera.data.ortho_scale, initial_zoom, abs_tol=1e-6)
for obj, start in zip(tracked, initial):
    assert all(abs(a - b) < 1e-5 for before, after in zip(start, obj.matrix_world)
               for a, b in zip(before, after)), obj.name

for name, peak in (('Electrical steel', 86), ('NdFeB magnet segments', 105),
                   ('Ground steel | shaft', 126), ('Encoder solder mask', 146)):
    strength = bpy.data.materials[name].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    scene.frame_set(1)
    assert strength.default_value == 0, name
    scene.frame_set(peak)
    assert strength.default_value > .18, name
    scene.frame_set(217)
    assert strength.default_value == 0, name

print('PASS: eight moving assemblies, synchronized rotation, four highlights and closed loop')
