"""Verify the saved scene without any add-ons or render devices."""

from math import isclose, pi

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


scene = bpy.context.scene
index = scene.objects["J9 · 180 degree bay exchange"]
base = scene.objects["Skid · lower flange"]
camera = scene.camera
assert not bpy.data.libraries
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 192, 24)
assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 720)

moving_parts = [obj for obj in index.children if obj.type == 'MESH']
assert len(moving_parts) > 100
assert all(scene.objects[f"Bay {bay} · workpiece plate"].parent == index for bay in "AB")
assert base.parent is None


def pose(frame):
    scene.frame_set(frame)
    return tuple(obj.matrix_world.copy() for obj in (index, base, camera))


start = pose(1)
at_swap = pose(81)
assert isclose(index.rotation_euler.z, pi, abs_tol=1e-6)
assert (at_swap[0].to_quaternion() @ Vector((1, 0, 0))).x < -0.999
assert at_swap[1] == start[1]
for initial, closed in zip(start, pose(193)):
    assert all(abs(a - b) < 1e-5 for row, end_row in zip(initial, closed) for a, b in zip(row, end_row))

for frame in range(1, 193):
    scene.frame_set(frame)
    for obj in moving_parts + [base]:
        for corner in obj.bound_box:
            view = world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
            assert 0.01 < view.x < 0.99 and 0.01 < view.y < 0.99, (frame, obj.name, view)

print("PASS: native bay exchange, fixed base, closed index and camera, full frame coverage")
