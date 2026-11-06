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
assert not any("enclosure" in collection.name.lower() for collection in scene.collection.children)
assert scene.objects["Recessed deck floor"].parent is None
assert all(scene.objects[f"{stand} stand · workpiece plate"].parent is None for stand in ("Front", "Rear"))
product_meshes = [obj for obj in scene.objects if obj.type == 'MESH' and obj.name != "Studio ground"]

arm_shoulders = []
for role in ("Welder", "Loader"):
    arm = scene.collection.children[f"{role} Rosie 1400 rig"]
    parent = None
    for joint in ("base", "turret", "upper_arm", "elbow", "forearm", "wrist", "flange"):
        control = arm.objects[f"{role} · {joint}"]
        assert control.type == 'EMPTY' and control.parent == parent
        assert not control.hide_render and not control.hide_viewport
        assert any(child.type == 'MESH' and not child.hide_render for child in control.children)
        parent = control
    arm_shoulders.append(arm.objects[f"{role} · upper_arm"])


def pose(frame):
    scene.frame_set(frame)
    return tuple(obj.matrix_world.copy() for obj in (index, base, camera))


start = pose(1)
at_swap = pose(81)
assert isclose(index.rotation_euler.z, pi, abs_tol=1e-6)
assert (at_swap[0].to_quaternion() @ Vector((1, 0, 0))).x < -0.999
assert at_swap[1] == start[1]
closure = pose(193)
for initial, closed in zip(start, closure):
    assert all(abs(a - b) < 1e-5 for row, end_row in zip(initial, closed) for a, b in zip(row, end_row))

before = pose(192)[2].translation
after = pose(2)[2].translation
incoming = closure[2].translation - before
outgoing = after - start[2].translation
assert incoming.x > 0.01 and outgoing.x > 0.01
assert (incoming - outgoing).length < 0.001

for frame in range(1, 193):
    scene.frame_set(frame)
    left, right = [world_to_camera_view(scene, camera, arm.matrix_world.translation).x for arm in arm_shoulders]
    assert 0.08 < left < 0.35 and 0.65 < right < 0.92, (frame, left, right)
    for obj in product_meshes:
        for corner in obj.bound_box:
            view = world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
            assert 0.01 < view.x < 0.99 and 0.01 < view.y < 0.99, (frame, obj.name, view)

print("PASS: two articulated Rosie arms, open deck, native bay exchange, closed loop, full frame coverage")
