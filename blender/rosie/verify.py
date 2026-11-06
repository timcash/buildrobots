"""Check the saved Rosie rig, framing, and loop without a render device."""

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
base = scene.objects['base_link']
links = [scene.objects[f'link_{number}'] for number in range(1, 7)]
axes = [(0, 0, 1), (0, 1, 0), (0, 1, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
origins = [(0, 0, 0), (0.16, -0.1255, 0.15), (0, 0, 0.6),
           (0.159, 0.1255, 0.105), (0.5147, 0, 0), (0, 0, -0.0993)]

assert not bpy.data.libraries
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 192, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 960)
assert (base.matrix_world.translation - Vector((0, 0, 0.0294))).length < 1e-5
assert base.matrix_world.to_quaternion().angle < 1e-5
for number, (link, parent, origin) in enumerate(zip(links, [base, *links[:-1]], origins), start=1):
    assert link.type == 'MESH' and link.parent == parent and link['joint'] == f'J{number}'
    assert len(link.data.polygons) > 1000
    assert (link.location - Vector(origin)).length < 1e-5
tool = scene.objects['tool0']
assert tool.parent == links[-1] and tool.location.length < 1e-5
assert (tool.rotation_euler.to_matrix() @ Vector((0, 0, 1)) - Vector((0, 0, -1))).length < 1e-5

tracked = [base, *links, scene.camera]
scene.frame_set(1)
start = [obj.matrix_world.copy() for obj in tracked]
local_start = [link.rotation_euler.copy() for link in links]
seen_motion = [False] * len(links)
for frame in range(1, 193):
    scene.frame_set(frame)
    assert base.matrix_world == start[0]
    for index, (link, axis) in enumerate(zip(links, axes)):
        direction = Vector(axis)
        assert (link.rotation_euler.to_matrix() @ direction - direction).length < 1e-5
        if (Vector(link.rotation_euler) - Vector(local_start[index])).length > 0.05:
            seen_motion[index] = True
    for link in [base, *links]:
        for corner in link.bound_box:
            view = world_to_camera_view(scene, scene.camera, link.matrix_world @ Vector(corner))
            assert 0.01 < view.x < 0.99 and 0.01 < view.y < 0.99, (frame, link.name, view)
assert all(seen_motion)
last_camera_position = scene.camera.location.copy()

scene.frame_set(193)
for initial, obj in zip(start, tracked):
    assert all(abs(a - b) < 1e-5 for row, end_row in zip(initial, obj.matrix_world) for a, b in zip(row, end_row)), obj.name
incoming = scene.camera.location - last_camera_position
scene.frame_set(2)
outgoing = scene.camera.location - start[-1].translation
assert incoming.length > 0.005 and (incoming - outgoing).length < 0.001

print('PASS: six AMR joint axes, fixed base, full camera framing, and closed loop')
