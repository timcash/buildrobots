"""Check the editable reducer rig, framing, and native animation."""

from math import cos, hypot, isclose, sin, tau

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
objects = scene.objects
assert not bpy.data.libraries
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 240, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 1024)

wave, fixed, flex, output = (objects[name] for name in (
    '01 | Wave generator — input', '02 | Circular spline — stationary',
    '03 | Flexspline — 200 external teeth', '04 | Output flange and bearing',
))
cam, cup, flange = (objects[name] for name in ('Input spin', 'Flexspline spin', 'Output spin'))
assert (cam.parent, cup.parent, flange.parent) == (wave, flex, output)
internal = objects['202 internal teeth']
external = objects['200 external teeth']
assert internal.parent == fixed and external.parent == cup
assert len(internal.data.vertices) == 202 * 5 * 6
assert len(external.data.vertices) == 200 * 5 * 6
assert sum(obj.name.startswith('Wave bearing ball') for obj in cam.children) == 40

labels = [obj for obj in objects if obj.type == 'FONT']
assert len(labels) == 15 and all(obj.data.font.packed_file for obj in labels)
assert {obj.data.body for obj in labels if obj.data.size > .04} == {
    'Two moving mesh zones', 'Wave generator', 'Circular spline', 'Flexspline', 'Output flange',
}

scene.frame_set(1)
meshes = [obj for obj in objects if obj.type == 'MESH']
visible_objects = [*meshes, *labels]
start = {obj.name: (obj.matrix_world.copy(), obj.hide_render) for obj in visible_objects}
initial_zoom = scene.camera.data.ortho_scale
shapes = external.data.shape_keys.key_blocks
initial_lobes = (shapes['Cosine lobe'].value, shapes['Sine lobe'].value)

for frame in range(1, 242):
    scene.frame_set(frame)
    assert not any(fixed.rotation_euler)
    assert isclose(cup.rotation_euler.x, flange.rotation_euler.x, abs_tol=1e-7)
    if frame <= 67:
        phase = tau * (frame - 1) / 66
        assert all(obj.location.length < 1e-6 for obj in (wave, fixed, flex, output))
        assert isclose(cam.rotation_euler.x, phase, abs_tol=1e-6)
        assert isclose(flange.rotation_euler.x, -phase / 100, abs_tol=1e-6)
        lobe = 2 * (phase - flange.rotation_euler.x)
        assert isclose(shapes['Cosine lobe'].value, cos(lobe), abs_tol=1e-5)
        assert isclose(shapes['Sine lobe'].value, sin(lobe), abs_tol=1e-5)
        marks = objects['Opposed engagement zones']
        assert marks.parent == fixed and len(marks.children) == 2
        assert isclose(marks.rotation_euler.x, phase, abs_tol=1e-6)
        assert all(not mark.hide_render for mark in marks.children)
    if 108 <= frame <= 203:
        assert wave.location.x < fixed.location.x < flex.location.x < output.location.x
        assert all(b.location.x - a.location.x > 2.4 for a, b in
                   zip((wave, fixed, flex), (fixed, flex, output)))
        assert hypot(shapes['Cosine lobe'].value, shapes['Sine lobe'].value) < 1e-6

    assert len([label for label in labels if not label.hide_render]) == 3
    depsgraph = bpy.context.evaluated_depsgraph_get()
    camera_inverse = scene.camera.matrix_world.inverted()
    width = scene.camera.data.ortho_scale
    height = width * scene.render.resolution_y / scene.render.resolution_x
    for obj in visible_objects:
        if obj.hide_render:
            continue
        bounds = [world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(corner))
                  for corner in obj.bound_box]
        if all(.005 < p.x < .995 and .005 < p.y < .995 for p in bounds):
            continue
        # A diagonal corner of a ring's box can leave the image while the ring fits.
        assert obj.type == 'MESH', (frame, obj.name, bounds)
        matrix = camera_inverse @ obj.matrix_world
        vertices = obj.evaluated_get(depsgraph).data.vertices
        assert all(abs(p.x) < .495 * width and abs(p.y) < .495 * height
                   for p in (matrix @ vertex.co for vertex in vertices)), (frame, obj.name)

assert isclose(scene.camera.data.ortho_scale, initial_zoom, abs_tol=1e-6)
assert all(isclose(shapes[name].value, value, abs_tol=1e-6)
           for name, value in zip(('Cosine lobe', 'Sine lobe'), initial_lobes))
for obj in visible_objects:
    matrix, hidden = start[obj.name]
    assert hidden == obj.hide_render
    if not hidden:
        assert all(abs(a - b) < 1e-5 for old, new in zip(matrix, obj.matrix_world)
                   for a, b in zip(old, new)), obj.name

for name, frame in (('elliptical cam', 115), ('fixed circular spline', 140),
                    ('thin flexspline', 163), ('output flange', 187)):
    material = bpy.data.materials['Highlight | ' + name]
    base = material.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    scene.frame_set(1)
    idle = tuple(base.default_value)
    scene.frame_set(frame)
    assert base.default_value[2] - base.default_value[0] > .60, name
    scene.frame_set(241)
    assert tuple(base.default_value) == idle, name

print('PASS: four editable assemblies, 200/202 teeth, paired mesh zones, 100:1 output and loop closure')
